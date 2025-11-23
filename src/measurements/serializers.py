from rest_framework import serializers
from .models import VariableCatalog, Measurement

class VariableCatalogSerializer(serializers.ModelSerializer):
    """
    Serializador para el catálogo de variables.
    Permite ver y definir los tipos de datos del sistema.
    """
    class Meta:
        model = VariableCatalog
        fields = '__all__'

class MeasurementSerializer(serializers.ModelSerializer):
    """
    Serializador para los registros de mediciones.
    Comportamiento:
    - Escritura (Write): Recibe IDs de 'sensor' y 'variable'.
    - Lectura (Read): Incluye campos 'aplanados' (sensor_serial, variable_code)
      para facilitar el consumo en el Frontend sin hacer peticiones extra.
    """
    sensor_serial = serializers.CharField(source='sensor.serial_number', read_only=True)
    variable_code = serializers.CharField(source='variable.code', read_only=True)
    variable_unit = serializers.CharField(source='variable.unit', read_only=True)

    class Meta:
        model = Measurement
        fields = [
            'measurement_id', 
            'sensor', 
            'sensor_serial', 
            'variable', 
            'variable_code', 
            'variable_unit',
            'value', 
            'measure_date', 
            'created_at'
        ]