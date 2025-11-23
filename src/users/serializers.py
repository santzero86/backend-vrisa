from rest_framework import serializers
from src.users.models import User, Role
from src.institutions.models import Institution

class InstitutionSerializer(serializers.ModelSerializer):
    """
    Serializador para mostrar información básica de la institución dentro de las respuestas de usuario.
    """
    class Meta:
        model = Institution
        fields = ['institution_id', 'institute_name']

class RoleSerializer(serializers.ModelSerializer):
    """
    Serializador para listar los roles disponibles o asignados.
    """
    class Meta:
        model = Role
        fields = ['role_id', 'role_name']

class UserSerializer(serializers.ModelSerializer):
    """
    Serializador para leer datos de Usuario (Salida).
    Incluye objetos anidados completos para 'institution' y 'roles'.
    """
     institution = InstitutionSerializer(read_only=True)
    role = RoleSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 
            'job_title', 'institution', 'roles', 
            'professional_card_front', 'professional_card_rear',
            'is_active', 'created_at'
        ]

class RegisterUserSerializer(serializers.Serializer):
    """
    Serializador para validación de entrada durante el registro.

    Maneja la validación de:
    1. Unicidad del correo electrónico.
    2. Existencia de la institución seleccionada.
    3. Recepción de archivos (tarjeta profesional).
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    role_id = serializers.IntegerField(required=False, allow_null=True)

    job_title = serializers.CharField(max_length=150, required=False)
    institution_id = serializers.IntegerField(required=True)
    professional_card_front = serializers.ImageField(required=False)
    professional_card_rear = serializers.ImageField(required=False)

    def validate_email(self, value):
        """
        Verifica que el correo no esté registrado previamente.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Ya existe un usuario con este correo electrónico.")
        return value
    
    def validate_institution_id(self, value):
        """
        Verifica que la institución referenciada exista en la base de datos.
        """
        if not Institution.objects.filter(pk=value).exists():
            raise serializers.ValidationError("La institución seleccionada no existe.")
        return value