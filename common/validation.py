from django.db import models

class ValidationStatus(models.TextChoices):
    """
    Estados de validación comunes en el sistema.
    Usado para solicitudes, roles, y otros procesos que requieren aprobación.
    """
    PENDING = 'PENDING', 'Pendiente de Validación'
    ACCEPTED = 'ACCEPTED', 'Aceptada'
    REJECTED = 'REJECTED', 'Rechazada'