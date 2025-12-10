from django.db import models


class ValidationStatus(models.TextChoices):
    """
    Estados de validación comunes en el sistema.
    Usado para solicitudes, roles, y otros procesos que requieren aprobación.
    """

    PENDING = "PENDING", "Pendiente de Validación"
    ACCEPTED = "ACCEPTED", "Aceptada"
    REJECTED = "REJECTED", "Rechazada"


class OperativeStatus(models.TextChoices):
    """
    Estados operativos para entidades como estaciones de monitoreo.
    """

    ACTIVE = "ACTIVE", "Operativa"
    PENDING = "PENDING", "Pendiente"
    REJECTED = "REJECTED", "Rechazada"
    MAINTENANCE = "MAINTENANCE", "En Mantenimiento"
    INACTIVE = "INACTIVE", "Inactiva"
    OFFLINE = "OFFLINE", "Fuera de Línea"
