from rest_framework import serializers
from src.institutions.models import EnvironmentalInstitution

class CreateInstitutionSerializer(serializers.Serializer):
    """
    Serializer para validar los datos de entrada al crear una institución.
    No está ligado a un modelo porque los datos los procesará el Command.
    """
    institute_name = serializers.CharField(max_length=255)
    physic_address = serializers.CharField(max_length=255)
    representative_id = serializers.IntegerField()

    def validate_institute_name(self, value):
        """
        Valida que no exista ya una institución con ese nombre.
        """
        if EnvironmentalInstitution.objects.filter(institute_name=value).exists():
            raise serializers.ValidationError("Ya existe una institución con este nombre.")
        return value

class InstitutionSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar los datos de una institución.
    """
    representative_email = serializers.EmailField(source='representative.email', read_only=True)
    
    class Meta:
        model = EnvironmentalInstitution
        fields = ['id', 'institute_name', 'physic_address', 'representative_email']

