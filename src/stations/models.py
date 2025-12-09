import secrets
from django.conf import settings
from django.db import models
from common.validation import ValidationStatus
from src.institutions.models import EnvironmentalInstitution

User = settings.AUTH_USER_MODEL


class MonitoringStation(models.Model):
    """
    Representa una estación de monitoreo en la red (tabla 'monitoring_station').

    Esta entidad es el núcleo de la recolección de datos. Almacena la ubicación física,
    el estado operativo y las credenciales de autenticación para los sensores IoT.
    """

    station_id = models.AutoField(primary_key=True)

    station_name = models.CharField(
        max_length=150, unique=True, verbose_name="Nombre de la Estación"
    )

    # Estados operativos definidos como Enumeración
    class OperativeStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Operativa"
        MAINTENANCE = "MAINTENANCE", "En Mantenimiento"
        INACTIVE = "INACTIVE", "Inactiva"
        OFFLINE = "OFFLINE", "Fuera de Línea"

    operative_status = models.CharField(
        max_length=20,
        choices=OperativeStatus.choices,
        default=OperativeStatus.INACTIVE,
        verbose_name="Estado Operativo",
    )

    # Token de seguridad para que la estación envíe datos a la API.
    # Se genera automáticamente en el servicio si no se provee.
    authentication_token = models.CharField(
        max_length=255,
        unique=True,
        editable=False,  # No se debe editar manualmente en el admin por seguridad
        verbose_name="Token de Autenticación",
    )

    # Dirección física o referencia (opcional)
    address_reference = models.CharField(
        max_length=255, 
        null=True, 
        blank=True, 
        verbose_name="Dirección o Referencia Física"
    )
    # Coordenadas geográficas (según diagrama: FLOAT)
    geographic_location_lat = models.FloatField(verbose_name="Latitud")
    geographic_location_long = models.FloatField(verbose_name="Longitud")

    # Auditoría
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de creación"
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Fecha de actualización"
    )

    # Relaciones (Foreign Keys)
    manager_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,  # Si se borra el usuario, la estación queda sin manager (no se borra)
        null=True,
        blank=True,
        related_name="managed_stations",
        verbose_name="Responsable Técnico (Manager)",
    )

    institution = models.ForeignKey(
        EnvironmentalInstitution,
        on_delete=models.CASCADE,  # Si se borra la institución, se borran sus estaciones
        related_name="stations",
        verbose_name="Institución Propietaria",
    )

    def __str__(self):
        return f"{self.station_name} ({self.get_operative_status_display()})"

    def save(self, *args, **kwargs):
        """
        Sobreescritura del método save para asegurar que siempre exista un token.
        """
        if not self.authentication_token:
            # Genera un token seguro de 32 bytes (64 caracteres hex)
            self.authentication_token = secrets.token_hex(32)
        super().save(*args, **kwargs)

    class Meta:
        db_table = "monitoring_station"
        verbose_name = "Estación de Monitoreo"
        verbose_name_plural = "Estaciones de Monitoreo"


class StationAffiliationRequest(models.Model):
    """
    Representa la solicitud formal de una Estación de Monitoreo para afiliarse
    a una Institución Ambiental específica (Tabla 'station_affiliation_request').

    Gestiona el flujo de:
    1. Usuario de rol `station_admin` solicita afiliación.
    2. Usuario de rol `institution_head` revisa y decide.
    3. Si se aprueba, la estación cambia de dueño.
    """

    request_id = models.AutoField(primary_key=True)

    # La estación que solicita la afiliación
    station = models.ForeignKey(
        "MonitoringStation",
        on_delete=models.CASCADE,
        related_name="affiliation_requests",
        verbose_name="Estación Solicitante",
    )

    # La institución a la que se quiere afiliar
    target_institution = models.ForeignKey(
        EnvironmentalInstitution,
        on_delete=models.CASCADE,
        related_name="received_affiliation_requests",
        verbose_name="Institución Destino",
    )

    # Referencia al usuario que creó la solicitud
    requester = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_affiliation_requests",
        verbose_name="Solicitado por",
    )

    status = models.CharField(
        max_length=20,
        choices=ValidationStatus.choices,
        default=ValidationStatus.PENDING,
        verbose_name="Estado de la Solicitud",
    )

    # Auditoría de la revisión
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_affiliation_requests",
        verbose_name="Revisado por",
    )

    review_comments = models.TextField(
        blank=True, verbose_name="Comentarios de Revisión"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "station_affiliation_request"
        verbose_name = "Solicitud de Afiliación"
        verbose_name_plural = "Solicitudes de Afiliación"
        # Regla: si ya hay una solicitud PENDING para esta estación e institución, no se puede crear otra
        constraints = [
            models.UniqueConstraint(
                fields=["station", "target_institution"],
                condition=models.Q(status="PENDING"),
                name="unique_pending_affiliation_per_station",
            )
        ]

    def __str__(self):
        return (
            f"{self.station.station_name} -> {self.target_institution.institute_name}"
        )
