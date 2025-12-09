from rest_framework import serializers
from .models import MaintenanceLog, Sensor


class SensorSerializer(serializers.ModelSerializer):
    """
    Serializador estándar para el modelo Sensor.
    Los campos de auditoría (fechas) son de solo lectura.
    """

    class Meta:
        model = Sensor
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class MaintenanceLogSerializer(serializers.ModelSerializer):
    """
    Serializador para los registros de mantenimiento.
    """

    technical_user_name = serializers.CharField(
        source="technical_user.get_full_name", read_only=True
    )
    sensor_serial = serializers.CharField(source="sensor.serial_number", read_only=True)

    class Meta:
        model = MaintenanceLog
        fields = [
            "maintenance_log_id",
            "sensor",
            "sensor_serial",
            "technical_user",
            "technical_user_name",
            "log_date",
            "description",
            "certificate_file",
            "created_at",
        ]
        read_only_fields = ["created_at"]
