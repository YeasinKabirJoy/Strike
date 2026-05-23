from django.apps import AppConfig


class RtchatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = "apps.rtchat"
    label = "rtchat"

    def ready(self):
        import apps.rtchat.signals
