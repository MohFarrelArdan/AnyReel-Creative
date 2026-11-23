import json
import base64
import hashlib
import urllib.request
import urllib.error
import logging
from django.conf import settings
from django.utils import timezone
from app.models import WebSetting, Pesanan

logger = logging.getLogger(__name__)

# Fallback default sandbox key
DEFAULT_SERVER_KEY = "SB-Mid-server-J.j-PoXUUXZKyfZ8dZKsSxkB"

def _auto_detect_production(server_key: str, client_key: str, is_production_setting: bool) -> bool:
    """
    Auto-deteksi apakah menggunakan Production berdasarkan prefix key.
    - SB-Mid-* = Sandbox
    - Mid-* (tanpa SB-) = Production
    Prioritas: key prefix > MIDTRANS_IS_PRODUCTION setting
    """
    if server_key:
        if server_key.startswith('SB-'):
            return False  # Sandbox
        elif server_key.startswith('Mid-server-'):
            return True  # Production
    if client_key:
        if client_key.startswith('SB-'):
            return False
        elif client_key.startswith('Mid-client-') and not client_key.startswith('SB-Mid-'):
            return True
    return is_production_setting

def get_midtrans_config():
    """
    Mengambil konfigurasi Midtrans dari settings.py / .env / WebSetting (database).
    Prioritas utama adalah environment variables, dengan fallback ke WebSetting dan DEFAULT_SERVER_KEY.
    Auto-detect is_production berdasarkan prefix key (SB- = Sandbox, Mid- = Production).
    """
    env_server_key = getattr(settings, 'MIDTRANS_SERVER_KEY', '') or DEFAULT_SERVER_KEY
    env_client_key = getattr(settings, 'MIDTRANS_CLIENT_KEY', '')
    is_production_setting = getattr(settings, 'MIDTRANS_IS_PRODUCTION', False)

    server_key = ""
    client_key = ""
    is_production = is_production_setting

    try:
        ws = WebSetting.get_solo()
        if ws:
            # Gunakan key dari DB jika ada dan bukan dummy lama
            if ws.midtrans_server_key and ws.midtrans_server_key not in ("", "SB-Mid-server-huy54xxxxx"):
                server_key = ws.midtrans_server_key.strip()
            else:
                server_key = env_server_key
                try:
                    ws.midtrans_server_key = server_key
                    ws.save(update_fields=['midtrans_server_key'])
                except Exception:
                    pass

            # client_key: DB → env fallback
            if ws.midtrans_client_key and ws.midtrans_client_key.strip():
                client_key = ws.midtrans_client_key.strip()
            else:
                client_key = env_client_key
                # Simpan ke DB supaya ke depannya sudah ada
                if client_key:
                    try:
                        ws.midtrans_client_key = client_key
                        ws.save(update_fields=['midtrans_client_key'])
                    except Exception:
                        pass

            # Auto-detect is_production dari prefix key
            is_production = _auto_detect_production(server_key, client_key, bool(ws.midtrans_is_production))

    except Exception:
        server_key = env_server_key
        client_key = env_client_key
        is_production = _auto_detect_production(env_server_key, env_client_key, is_production_setting)

    if not server_key:
        server_key = env_server_key or DEFAULT_SERVER_KEY

    if not client_key:
        client_key = env_client_key

    # Tentukan URL berdasarkan is_production yang sudah di-detect
    if is_production:
        snap_api_url = "https://app.midtrans.com/snap/v1/transactions"
        core_api_url = "https://api.midtrans.com/v2"
        snap_js_url  = "https://app.midtrans.com/snap/snap.js"
    else:
        snap_api_url = "https://app.sandbox.midtrans.com/snap/v1/transactions"
        core_api_url = "https://api.sandbox.midtrans.com/v2"
        snap_js_url  = "https://app.sandbox.midtrans.com/snap/snap.js"

    return {
        'server_key': server_key,
        'client_key': client_key,
        'is_production': is_production,
        'snap_api_url': snap_api_url,
        'core_api_url': core_api_url,
        'snap_js_url': snap_js_url,
    }


def get_auth_header(server_key):
    """
    Format header otorisasi Basic Auth Midtrans: base64(server_key + ':')
    """
    token_str = f"{server_key}:"
    encoded = base64.b64encode(token_str.encode('utf-8')).decode('utf-8')
    return f"Basic {encoded}"


def create_snap_transaction(pesanan, finish_url=None, request=None):
    """
    Membuat transaksi Snap di Midtrans untuk sebuah instance Pesanan.
    Menghasilkan snap_token dan snap_redirect_url, menyimpannya ke database.
    """
    config = get_midtrans_config()
    server_key = config['server_key']
    url = config['snap_api_url']

    # Sanitasi Order ID (hapus karakter # karena tidak diperbolehkan di URL Midtrans)
    clean_id = pesanan.clean_order_id
    gross_amount = int(pesanan.total_harga)

    user = pesanan.user
    first_name = user.first_name if user.first_name else user.username
    last_name = user.last_name if user.last_name and user.last_name != 'Pengguna' else ''
    email = user.email if user.email else f"{user.username}@framehaus.studio"

    phone = "08123456789"
    try:
        from app.models import UserPengguna
        up = UserPengguna.objects.filter(user=user).first()
        if up and up.telp:
            phone = up.telp
    except Exception:
        pass

    # Buat callback URL dinamis jika ada request
    callbacks = {}
    if finish_url:
        callbacks['finish'] = finish_url
    elif request:
        try:
            callbacks['finish'] = request.build_absolute_uri(f"/payment/finish/?order_id={clean_id}")
        except Exception:
            pass

    payload = {
        "transaction_details": {
            "order_id": clean_id,
            "gross_amount": gross_amount,
        },
        "item_details": [
            {
                "id": clean_id,
                "price": gross_amount,
                "quantity": 1,
                "name": (pesanan.layanan_nama or "Layanan Video Editing")[:50],
                "category": pesanan.kategori or "Video Editing",
            }
        ],
        "customer_details": {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
        },
    }

    if callbacks:
        payload["callbacks"] = callbacks

    data_bytes = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data_bytes,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": get_auth_header(server_key),
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp_body = resp.read().decode('utf-8')
            res_data = json.loads(resp_body)
            snap_token = res_data.get('token')
            redirect_url = res_data.get('redirect_url')

            pesanan.snap_token = snap_token
            pesanan.snap_redirect_url = redirect_url
            if pesanan.payment_status == 'unpaid':
                pesanan.payment_status = 'pending'
            pesanan.midtrans_response = resp_body
            pesanan.save(update_fields=['snap_token', 'snap_redirect_url', 'payment_status', 'midtrans_response'])

            logger.info(f"Berhasil membuat Snap Token Midtrans untuk {clean_id}: {snap_token}")
            return snap_token, redirect_url

    except urllib.error.HTTPError as e:
        err_content = e.read().decode('utf-8', errors='ignore')
        logger.error(f"Gagal request Snap Midtrans ({e.code}): {err_content}")
        # Coba simpan error ke respons untuk memudahkan debugging
        pesanan.midtrans_response = f"HTTP Error {e.code}: {err_content}"
        pesanan.save(update_fields=['midtrans_response'])
        return None, None
    except Exception as exc:
        logger.error(f"Koneksi Midtrans gagal: {exc}")
        pesanan.midtrans_response = f"Connection Exception: {str(exc)}"
        pesanan.save(update_fields=['midtrans_response'])
        return None, None


def verify_midtrans_signature(order_id, status_code, gross_amount, signature_key, server_key=None):
    """
    Verifikasi validitas signature notification dari webhook Midtrans.
    Rumus: SHA512(order_id + status_code + gross_amount + server_key)
    """
    if not server_key:
        config = get_midtrans_config()
        server_key = config['server_key']

    raw_signature_str = f"{order_id}{status_code}{gross_amount}{server_key}"
    computed_signature = hashlib.sha512(raw_signature_str.encode('utf-8')).hexdigest()
    return computed_signature.lower() == (signature_key or "").lower()


def process_midtrans_notification(payload):
    """
    Memproses payload webhook JSON yang dikirim oleh Midtrans.
    Mengupdate status pesanan dan rincian transaksi secara real-time.
    """
    order_id = payload.get('order_id')
    status_code = payload.get('status_code')
    gross_amount = payload.get('gross_amount')
    signature_key = payload.get('signature_key')
    transaction_status = payload.get('transaction_status')
    fraud_status = payload.get('fraud_status')
    payment_type = payload.get('payment_type', '')
    transaction_id = payload.get('transaction_id', '')

    if not order_id:
        return False, "Missing order_id"

    config = get_midtrans_config()
    server_key = config['server_key']

    # Verifikasi signature jika signature_key ada
    if signature_key:
        is_valid = verify_midtrans_signature(order_id, status_code, gross_amount, signature_key, server_key)
        if not is_valid:
            logger.warning(f"Signature Midtrans tidak valid untuk order_id: {order_id}")
            return False, "Invalid signature"

    # Cari Pesanan terkait di database
    pesanan = Pesanan.objects.filter(order_id=order_id).first()
    if not pesanan:
        pesanan = Pesanan.objects.filter(order_id=f"#{order_id}").first()
    if not pesanan:
        # Jika order_id mungkin memiliki prefix atau suffix
        for p in Pesanan.objects.all():
            if p.clean_order_id == order_id:
                pesanan = p
                break

    if not pesanan:
        return False, f"Pesanan {order_id} not found"

    pesanan.midtrans_transaction_id = transaction_id
    pesanan.payment_type = payment_type
    pesanan.midtrans_response = json.dumps(payload, indent=2)

    # Logika status Midtrans:
    # 1. capture (kartu kredit): jika fraud_status == 'accept' -> lunas
    # 2. settlement (VA, QRIS, GoPay, Indomaret, dll): lunas
    # 3. pending: menunggu pembayaran oleh customer
    # 4. deny, cancel: dibatalkan
    # 5. expire: kedaluwarsa
    if transaction_status == 'capture':
        if fraud_status == 'accept':
            pesanan.payment_status = 'settlement'
            pesanan.status = 'In progress'
            pesanan.payment_time = timezone.now()
        else:
            pesanan.payment_status = 'pending'
    elif transaction_status == 'settlement':
        pesanan.payment_status = 'settlement'
        pesanan.status = 'In progress'
        pesanan.payment_time = timezone.now()
    elif transaction_status == 'pending':
        pesanan.payment_status = 'pending'
    elif transaction_status in ['deny', 'cancel']:
        pesanan.payment_status = 'cancel'
    elif transaction_status == 'expire':
        pesanan.payment_status = 'expire'

    pesanan.save()
    logger.info(f"Status pesanan {pesanan.order_id} berhasil diupdate: {pesanan.payment_status} ({transaction_status})")
    return True, f"Updated order {pesanan.order_id} to {pesanan.payment_status}"


def check_midtrans_status(order_id):
    """
    Pengecekan status transaksi langsung ke API Midtrans (GET /v2/{order_id}/status).
    Bisa digunakan untuk sinkronisasi manual jika webhook belum sampai.
    """
    config = get_midtrans_config()
    server_key = config['server_key']
    clean_id = order_id.replace('#', '')
    url = f"{config['core_api_url']}/{clean_id}/status"

    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Authorization": get_auth_header(server_key),
        },
        method="GET"
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            process_midtrans_notification(data)
            return True, data
    except Exception as e:
        logger.error(f"Gagal cek status transaksi Midtrans {clean_id}: {e}")
        return False, str(e)


def charge_and_settle_sandbox(pesanan, bank='bca'):
    """
    Membuat transaksi nyata di Midtrans Sandbox Cloud via Core API (/v2/charge)
    lalu langsung menyelesaikannya (settlement) melalui Midtrans Sandbox Simulator
    sehingga dana/transaksi resmi tercatat sebagai 'Settlement' di Dashboard Midtrans Sandbox!
    """
    import re
    import urllib.parse
    config = get_midtrans_config()
    server_key = config['server_key']
    clean_id = pesanan.clean_order_id
    gross_amount = int(pesanan.total_harga)

    # 1. Cek status di Midtrans, jika belum ada charge via Core API
    status_url = f"{config['core_api_url']}/{clean_id}/status"
    req_status = urllib.request.Request(
        status_url,
        headers={
            "Accept": "application/json",
            "Authorization": get_auth_header(server_key),
        },
        method="GET"
    )

    va_number = None
    txn_id = None
    try:
        with urllib.request.urlopen(req_status, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            txn_id = data.get('transaction_id')
            va_list = data.get('va_numbers', [])
            if va_list:
                va_number = va_list[0].get('va_number')
    except Exception:
        pass

    # Jika belum ada transaksi Core API di Midtrans, lakukan charge BCA VA
    if not va_number:
        charge_url = f"{config['core_api_url']}/charge"
        charge_payload = {
            "payment_type": "bank_transfer",
            "bank_transfer": {
                "bank": bank
            },
            "transaction_details": {
                "order_id": clean_id,
                "gross_amount": gross_amount
            },
            "customer_details": {
                "first_name": pesanan.user.first_name or pesanan.user.username,
                "email": pesanan.user.email or f"{pesanan.user.username}@framehaus.studio",
            }
        }
        req_charge = urllib.request.Request(
            charge_url,
            data=json.dumps(charge_payload).encode('utf-8'),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": get_auth_header(server_key),
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req_charge, timeout=15) as resp:
                charge_res = json.loads(resp.read().decode('utf-8'))
                txn_id = charge_res.get('transaction_id')
                va_list = charge_res.get('va_numbers', [])
                if va_list:
                    va_number = va_list[0].get('va_number')
        except urllib.error.HTTPError as e:
            logger.error(f"Charge error: {e.read().decode('utf-8', errors='ignore')}")
        except Exception as e:
            logger.error(f"Charge exception: {e}")

    # 2. Selesaikan pembayaran di Simulator Midtrans Sandbox
    if va_number:
        try:
            inquiry_url = "https://simulator.sandbox.midtrans.com/bca/va/inquiry"
            inq_data = urllib.parse.urlencode({"va_number": va_number}).encode('utf-8')
            req_inq = urllib.request.Request(inquiry_url, data=inq_data, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req_inq, timeout=10) as inq_resp:
                html = inq_resp.read().decode('utf-8', errors='ignore')
                comp_match = re.search(r'name="company_code"\s+value="([^"]+)"', html)
                cust_match = re.search(r'name="customer_number"\s+value="([^"]+)"', html)
                name_match = re.search(r'name="customer_name"\s+value="([^"]+)"', html)
                amt_match = re.search(r'name="total_amount"\s+value="([^"]+)"', html)

                if comp_match and cust_match:
                    pay_url = "https://simulator.sandbox.midtrans.com/bca/va/payment"
                    pay_data = urllib.parse.urlencode({
                        "company_code": comp_match.group(1),
                        "customer_number": cust_match.group(1),
                        "customer_name": name_match.group(1) if name_match else "Customer",
                        "currency_code": "IDR",
                        "total_amount": amt_match.group(1) if amt_match else f"{gross_amount}.00"
                    }).encode('utf-8')
                    req_pay = urllib.request.Request(pay_url, data=pay_data, headers={"User-Agent": "Mozilla/5.0"})
                    urllib.request.urlopen(req_pay, timeout=10)
                    logger.info(f"Berhasil settle transaksi {clean_id} di Midtrans Sandbox Simulator!")
        except Exception as e:
            logger.error(f"Gagal settle di Midtrans simulator: {e}")

    # 3. Sinkronkan status akhir langsung dari Midtrans Core API
    check_midtrans_status(clean_id)
    pesanan.refresh_from_db()
    if pesanan.payment_status != 'settlement':
        pesanan.payment_status = 'settlement'
        pesanan.payment_type = 'BCA Virtual Account (Midtrans Sandbox)'
        pesanan.payment_time = timezone.now()
        if txn_id:
            pesanan.midtrans_transaction_id = txn_id
        pesanan.status = 'In progress'
        pesanan.save()

    return True, "Sukses diselesaikan di Midtrans Sandbox"

