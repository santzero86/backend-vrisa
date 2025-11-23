from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Sensor

class SensorService:
    @staticmethod
    def create_sensor(data: dict) -> Sensor:
        with transaction.atomic():
            sensor = Sensor.objects.create(**data)
            return sensor

    @staticmethod
    def update_sensor_status(sensor_id: int, new_status: str) -> Sensor:
        try:
            sensor = Sensor.objects.get(pk=sensor_id)
            sensor.status = new_status
            sensor.save()
            return sensor
        except Sensor.DoesNotExist:
            raise ValidationError(f"El sensor {sensor_id} no existe.")