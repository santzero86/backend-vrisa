from django.db import models
from src.stations.models import MonitoringStation

class Sensor(models.Model):
    """
    Representa un dispositivo sensor físico dentro del sistema.
    Almacena información técnica como modelo, fabricante, número de serie
    y el estado operativo actual del dispositivo.
    """
    sensor_id = models.AutoField(primary_key=True)
    model = models.CharField(max_length=100, verbose_name="Modelo del Sensor")
    manufacturer = models.CharField(max_length=100, verbose_name="Fabricante")
    serial_number = models.CharField(max_length=100, unique=True, verbose_name="Número de Serie")
    installation_date = models.DateField(verbose_name="Fecha de Instalación")
    
    station = models.ForeignKey(
        MonitoringStation,
        on_delete=models.CASCADE,
        related_name='sensors',
        verbose_name="Estación Asignada",
        null=True, blank=True 
    ) 



    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Activo'
        INACTIVE = 'INACTIVE', 'Inactivo'
        MAINTENANCE = 'MAINTENANCE', 'Mantenimiento'

    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.ACTIVE,
        verbose_name="Estado"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.model} - {self.serial_number} ({self.status})"
    
    class Meta:
        db_table = 'sensor' 
        verbose_name = "Sensor"
        verbose_name_plural = "Sensores"
