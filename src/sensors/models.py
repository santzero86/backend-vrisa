from django.conf import settings
from django.db import models
from src.stations.models import MonitoringStation

User = settings.AUTH_USER_MODEL

class Sensor(models.Model):
    """
    Representa un dispositivo sensor físico dentro del sistema.
    Almacena información técnica como modelo, fabricante, número de serie
    y el estado operativo actual del dispositivo.
    """

    sensor_id = models.AutoField(primary_key=True)
    model = models.CharField(max_length=100, verbose_name="Modelo del Sensor")
    manufacturer = models.CharField(max_length=100, verbose_name="Fabricante")
    serial_number = models.CharField(
        max_length=100, unique=True, verbose_name="Número de Serie"
    )
    installation_date = models.DateField(verbose_name="Fecha de Instalación")

    station = models.ForeignKey(
        MonitoringStation,
        on_delete=models.CASCADE,
        related_name="sensors",
        verbose_name="Estación Asignada",
        null=True,
        blank=True,
    )

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Activo"
        INACTIVE = "INACTIVE", "Inactivo"
        MAINTENANCE = "MAINTENANCE", "Mantenimiento"

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Estado",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.model} - {self.serial_number} ({self.status})"

    class Meta:
        db_table = "sensor"
        verbose_name = "Sensor"
        verbose_name_plural = "Sensores"


class MaintenanceLog(models.Model):
    """
    Registro de mantenimiento de un sensor (tabla 'maintenance_log').

    Permite llevar la trazabilidad de calibraciones, reparaciones o limpiezas
    realizadas a los sensores para garantizar la calidad del dato.
    """

    maintenance_log_id = models.AutoField(primary_key=True)

    sensor = models.ForeignKey(
        Sensor,
        on_delete=models.CASCADE,
        related_name="maintenance_logs",
        verbose_name="Sensor",
    )

    technical_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="performed_maintenances",
        verbose_name="Técnico Responsable",
    )

    log_date = models.DateTimeField(verbose_name="Fecha del Mantenimiento")

    description = models.TextField(verbose_name="Descripción de actividades")

    # Campo para certificados
    certificate_file = models.FileField(
        upload_to="maintenance_certificates/",
        null=True,
        blank=True,
        verbose_name="Certificado de Calibración/Mantenimiento",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mantenimiento {self.sensor.serial_number} - {self.log_date.date()}"

    class Meta:
        db_table = "maintenance_log"
        verbose_name = "Bitácora de Mantenimiento"
        verbose_name_plural = "Bitácoras de Mantenimiento"
        ordering = ["-log_date"]
