from django.db import models

from django.db import models
from src.sensors.models import Sensor 

class VariableCatalog(models.Model):
    """
    Catálogo maestro de variables meteorológicas y contaminantes.
    Actúa como un diccionario para definir qué tipos de datos puede interpretar el sistema.
    Define metadatos como unidades de medida y rangos de validación automática.
    """
    variable_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, verbose_name="Nombre (Ej: Material Particulado 2.5)")
    code = models.CharField(max_length=20, unique=True, verbose_name="Código (Ej: PM2.5)")
    unit = models.CharField(max_length=20, verbose_name="Unidad (Ej: µg/m³)")
    
    # Límites para validación básica de calidad de datos
    min_expected_value = models.FloatField(default=0)
    max_expected_value = models.FloatField(default=1000)

    def __str__(self):
        return f"{self.name} ({self.unit})"

class Measurement(models.Model):
    """
    Registro histórico de una medición individual.
    Esta tabla almacena la serie de tiempo de los datos recolectados.
    Está optimizada para búsquedas por sensor y fecha.
    """
    measurement_id = models.AutoField(primary_key=True)
    
    # Relación con el Sensor (Core del requerimiento)
    sensor = models.ForeignKey(
        Sensor,
        on_delete=models.CASCADE,
        related_name='measurements',
        verbose_name="Sensor Origen"
    )
    
    # Relación con la Variable
    variable = models.ForeignKey(
        VariableCatalog,
        on_delete=models.PROTECT,
        related_name='measurements'
    )
    
    value = models.FloatField(verbose_name="Valor Medido")
    measure_date = models.DateTimeField(verbose_name="Fecha de Toma de Dato")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-measure_date']
        indexes = [
            models.Index(fields=['sensor', 'measure_date']),
        ]

    def __str__(self):
        return f"{self.variable.code}: {self.value}"