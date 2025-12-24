from django.apps import AppConfig


class PersonalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'personal'
    
    def ready(self):
        """Загружаем сигналы при старте приложения"""
        import personal.models  # noqa: F401
