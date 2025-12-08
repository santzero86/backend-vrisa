from common.validation import ValidationStatus
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from src.users.models import User, Role, UserRole
from src.institutions.models import EnvironmentalInstitution


class InstitutionSerializer(serializers.ModelSerializer):
    """
    Serializador para mostrar información básica de la institución dentro de las respuestas de usuario.
    """
    institution_id = serializers.IntegerField(source='id', read_only=True)
    class Meta:
        model = EnvironmentalInstitution
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
    roles = RoleSerializer(many=True, read_only=True) 

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'phone',
            'job_title',
            'institution',
            'roles', 
            'professional_card_front',
            'professional_card_rear',
            'is_active',
            'created_at'
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
    institution_id = serializers.IntegerField(required=False, allow_null=True)
    phone = serializers.CharField(max_length=20)
    requested_role = serializers.CharField(required=False, default='citizen')
    
    job_title = serializers.CharField(max_length=150, required=False)
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
        if value is None:
            return None
        """
        Verifica que la institución referenciada exista en la base de datos.
        """
        if not EnvironmentalInstitution.objects.filter(pk=value).exists():
            raise serializers.ValidationError("La institución seleccionada no existe.")
        return value

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Personaliza el payload del token JWT para incluir información contextual
    del usuario (Rol, Institución, Nombre) directamente en el token cifrado.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Agregar datos personalizados al token
        token['email'] = user.email
        token['full_name'] = f"{user.first_name} {user.last_name}"
        token['first_name'] = user.first_name
        
        # Agregar Institución (si tiene)
        if user.institution:
            token['institution_id'] = user.institution.id
            token['institution_name'] = user.institution.institute_name
        else:
            token['institution_id'] = None
        
        # Agregar Roles
        primary_role, role_status = cls.get_primary_role(user)
        
        token['primary_role'] = primary_role
        token['role_status'] = role_status
        token['roles_list'] = list(user.roles.values_list('role_name', flat=True))

        return token
        

    @staticmethod
    def get_primary_role(user):
        """
        Determina el rol principal y su estado.
        Retorna siempre una tupla: (nombre_rol, estado)
        """
        if user.is_superuser:
            return 'super_admin', 'APPROVED'
        elif user.is_staff:
            return 'staff', 'APPROVED'
        
        user_roles = UserRole.objects.filter(user=user)
        
        # Prioridad 1: Roles ya aprobados
        approved_assignment = user_roles.filter(approved_status=ValidationStatus.ACCEPTED).first()
        if approved_assignment:
            return approved_assignment.role.role_name, 'APPROVED'
        
        # Prioridad 2: Roles pendientes
        pending_assignment = user_roles.filter(approved_status=ValidationStatus.PENDING).first()
        if pending_assignment:
            return pending_assignment.role.role_name, 'PENDING'
        
        # Default: Ciudadano aprobado
        return 'citizen', 'APPROVED'