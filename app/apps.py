from django.apps import AppConfig
from django.db.models.signals import post_migrate


def app_post_migrate_callback(sender, **kwargs):
    try:
        from .seed_data import seed_initial_data
        seed_initial_data()
    except Exception:
        pass


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        post_migrate.connect(app_post_migrate_callback, sender=self)
