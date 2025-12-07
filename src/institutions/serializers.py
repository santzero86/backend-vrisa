from rest_framework import serializers
from .models import EnvironmentalInstitution, InstitutionColorSet, IntegrationRequest
import json

class InstitutionColorSetSerializer(serializers.ModelSerializer):
    """
    Serializador auxiliar para la representación anidada de colores.
    Diseñado principalmente para lectura (read-only) dentro de la institución.
    """
    class Meta:
        model = InstitutionColorSet
        fields = ['id', 'color_hex']

class EnvironmentalInstitutionSerializer(serializers.ModelSerializer):
    """
    Serializador principal para Instituciones Ambientales.
    
    Maneja dos flujos de datos para los colores:
    1. 'colors': Salida anidada completa (read-only).
    2. 'colors_input': Entrada simplificada (lista de strings) para la creación (write-only).
    """
    # Read-only para mostrar los datos
    colors = InstitutionColorSetSerializer(many=True, read_only=True)
    
    # Write-only para recibir la entrada simple
    colors_input = serializers.ListField(
        child=serializers.CharField(max_length=7), 
        write_only=True, 
        required=False
    )

    class Meta:
        model = EnvironmentalInstitution
        fields = [
            'id', 
            'institute_name', 
            'physic_address', 
            'institute_logo',
            'colors', 
            'colors_input',
            'created_at',
            'validation_status'
        ]
        read_only_fields = ['created_at', 'validation_status']

class IntegrationRequestSerializer(serializers.ModelSerializer):
    """
    Serializador para las solicitudes de integración.
    Incluye el nombre de la institución de forma plana para facilitar su lectura en frontend.
    """
    institution_name = serializers.CharField(source='institution.institute_name', read_only=True)

    class Meta:
        model = IntegrationRequest
        fields = '__all__'
        read_only_fields = ['request_date', 'reviewed_by', 'review_date']

class InstitutionRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializador específico para el registro inicial de una institución.
    Maneja la recepción de colores como un string JSON (dado que viene de FormData).
    """
    # Se reciben los colores como un string JSON: '["#FFF", "#000"]'
    colors = serializers.CharField(write_only=True)

    class Meta:
        model = EnvironmentalInstitution
        fields = ['institute_name', 'physic_address', 'institute_logo', 'colors']

    def validate_colors(self, value):
        try:
            colors = json.loads(value)
            if not isinstance(colors, list):
                raise serializers.ValidationError("El formato debe ser una lista de colores.")
            return colors
        except ValueError:
            raise serializers.ValidationError("JSON de colores inválido.")
