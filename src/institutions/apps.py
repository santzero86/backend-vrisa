from django.apps import AppConfig

class InstitutionsConfig(AppConfig):
    '''
    Configuración principal del módulo de Instituciones.
    Define el tipo de AutoField por defecto y el namespace 'src.institutions'.
    '''
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.institutions'
    label = 'institutions'
