from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Measurement
from src.sensors.models import Sensor

class MeasurementService:
    @staticmethod
    def create_measurement(data: dict) -> Measurement:
        sensor = data.get('sensor')
        variable = data.get('variable')
        value = data.get('value')

        # 1. Validación de Negocio: Sensor Activo
        if sensor.status != Sensor.Status.ACTIVE:
            raise ValidationError(f"El sensor {sensor.serial_number} no está activo (Estado: {sensor.status}).")

        # 2. Validación de Negocio: Rango de valores (Calidad de datos simple)
        if value < variable.min_expected_value or value > variable.max_expected_value:
            raise ValidationError(f"El valor {value} está fuera del rango permitido para {variable.code}.")

        with transaction.atomic():
            measurement = Measurement.objects.create(**data)
            return measurement