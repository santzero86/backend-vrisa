# src/institutions/serializers.py
from rest_framework import serializers
from .models import EnvironmentalInstitution, InstitutionColorSet, IntegrationRequest

# Serializador auxiliar para mostrar la estructura anidada de colores (Solo lectura).
class InstitutionColorSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstitutionColorSet
        fields = ['id', 'color_hex']

class EnvironmentalInstitutionSerializer(serializers.ModelSerializer):
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
            'created_at'
        ]
        read_only_fields = ['created_at']

# Incluye el nombre de la institución para facilitar la lectura en el Frontend.
class IntegrationRequestSerializer(serializers.ModelSerializer):
    institution_name = serializers.CharField(source='institution.institute_name', read_only=True)

    class Meta:
        model = IntegrationRequest
        fields = '__all__'
        read_only_fields = ['request_date', 'reviewed_by', 'review_date']