from rest_framework import serializers
from .models import EnvironmentalInstitution, InstitutionColorSet, IntegrationRequest

class InstitutionColorSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstitutionColorSet
        fields = ['id', 'color_hex']

# Campo de lectura: Muestra los colores anidados dentro del JSON de la institución.
class EnvironmentalInstitutionSerializer(serializers.ModelSerializer):
    # Incluimos los colores anidados para verlos al pedir la info de la institución
    colors = InstitutionColorSetSerializer(many=True, read_only=True)
    # Campo de escritura (write_only): Recibe una lista simple de strings ["#FFF", "#000"].
    # No se guarda en la BD directamente, lo usamos manualmente en el método create().
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

    def create(self, validated_data):
         # Extraemos los colores si vienen en la petición
        colors_data = validated_data.pop('colors_input', [])
        institution = EnvironmentalInstitution.objects.create(**validated_data)
        # Guardamos los colores
        for color_hex in colors_data:
            InstitutionColorSet.objects.create(institution=institution, color_hex=color_hex)
            
        return institution

class IntegrationRequestSerializer(serializers.ModelSerializer):
    institution_name = serializers.CharField(source='institution.institute_name', read_only=True)

    class Meta:
        model = IntegrationRequest
        fields = '__all__'
        read_only_fields = ['request_date', 'reviewed_by', 'review_date']
