from django.apps import AppConfig


class RtchatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rtchat'

    def ready(self):
        import rtchat.signals
