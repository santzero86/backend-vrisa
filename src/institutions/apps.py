from django.apps import AppConfig

# Configuración principal del módulo de Instituciones.
# Define el tipo de AutoField por defecto y el namespace 'src.institutions'.
class InstitutionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.institutions'
    label = 'institutions'