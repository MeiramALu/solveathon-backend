from django.apps import AppConfig

class FactoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'factory'

    def ready(self):
        # ВОТ ЭТА СТРОКА ВКЛЮЧАЕТ АВТОМАТИКУ:
        from . import signals