from rest_framework import serializers
from src.users.models import User, Role

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['role_id', 'role_name']

class UserSerializer(serializers.ModelSerializer):
    """
    Serializador para leer datos de Usuario (Salida).
    Incluye información anidada del rol.
    """
    role = RoleSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_active', 'role']

class RegisterUserSerializer(serializers.Serializer):
    """
    Serializador para validación de entrada durante el registro.
    Usamos un Serializer estándar (no ModelSerializer) para controlar explícitamente 
    los datos antes de pasarlos a la capa de servicios.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    role_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Ya existe un usuario con este correo electrónico.")
        return value
