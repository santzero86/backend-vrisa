from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Measurement
from src.sensors.models import Sensor

class MeasurementService:
    """
    Capa de servicio para la gestión de mediciones.
    Centraliza la lógica de negocio, validaciones de integridad y control de calidad
    de datos antes de persistir en la base de datos.
    """
    @staticmethod
    def create_measurement(data: dict) -> Measurement:
        """
        Crea un registro de medición validando reglas estrictas de negocio.
        Flujo de Validación:
        1. Verifica que el Sensor exista y esté en estado 'ACTIVE'.
        2. Verifica que el valor medido esté dentro de los rangos físicos posibles
           definidos en el catálogo de variables (Control de Calidad).
        Args:
            data (dict): Diccionario con datos validados (sensor, variable, value, date).                 Generalmente proviene de serializer.validated_data.
        Returns:
            Measurement: La instancia del modelo creada y guardada.
        Raises:
            - Si el sensor está INACTIVO o en MANTENIMIENTO.
            - Si el valor (value) está fuera de los rangos min/max esperados.
        """
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