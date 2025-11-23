from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Sensor

class SensorService:
    """
    Capa de servicio para encapsular la lógica de negocio de los Sensores.
    """
    @staticmethod
    def create_sensor(data: dict) -> Sensor:
        """
        Crea un nuevo sensor en la base de datos de forma transaccional.
        Args:
            data (dict): Datos validados del sensor. 
        Returns:
            Sensor: Instancia del sensor creado.
        """
        with transaction.atomic():
            sensor = Sensor.objects.create(**data)
            return sensor

    @staticmethod
    def update_sensor_status(sensor_id: int, new_status: str) -> Sensor:
        """
        Actualiza el estado operativo de un sensor específico.
        Args:
            sensor_id (int): Identificador único del sensor.
            new_status (str): Nuevo estado (debe coincidir con Sensor.Status).
        Raises:
            ValidationError: Si el sensor no existe.
        """
        try:
            sensor = Sensor.objects.get(pk=sensor_id)
            sensor.status = new_status
            sensor.save()
            return sensor
        except Sensor.DoesNotExist:
            raise ValidationError(f"El sensor {sensor_id} no existe.")