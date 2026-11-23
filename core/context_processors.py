from app.models import WebSetting

def web_settings_context(request):
    """
    Exposes `web_setting` across all templates automatically.
    """
    try:
        setting = WebSetting.get_solo()
    except Exception:
        setting = None
    return {
        'web_setting': setting
    }
