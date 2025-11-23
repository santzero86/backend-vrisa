from rest_framework import serializers
from .models import VariableCatalog, Measurement

class VariableCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariableCatalog
        fields = '__all__'

class MeasurementSerializer(serializers.ModelSerializer):
    # Campos informativos de solo lectura
    sensor_serial = serializers.CharField(source='sensor.serial_number', read_only=True)
    variable_code = serializers.CharField(source='variable.code', read_only=True)

    class Meta:
        model = Measurement
        fields = [
            'measurement_id', 'sensor', 'sensor_serial', 
            'variable', 'variable_code', 
            'value', 'measure_date', 'created_at'
        ]