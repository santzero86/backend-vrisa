from rest_framework import serializers
from .models import Sensor

class SensorSerializer(serializers.ModelSerializer):
    """
    Serializador estándar para el modelo Sensor.
    Los campos de auditoría (fechas) son de solo lectura.
    """
    class Meta:
        model = Sensor
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']