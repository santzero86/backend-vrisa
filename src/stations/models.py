import secrets
from django.conf import settings
from django.contrib.gis.db import models
from common.validation import OperativeStatus
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

    operative_status = models.CharField(
        max_length=20,
        choices=OperativeStatus.choices,
        default=OperativeStatus.PENDING,
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

    # Ubicación geográfica usando PostGIS (SRID 4326 = WGS84)
    location = models.PointField(srid=4326, verbose_name="Ubicación")

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
