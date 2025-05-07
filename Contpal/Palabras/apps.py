from django.apps import AppConfig


class PalabrasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Palabras'

    def ready(self):
        import Palabras.signals

