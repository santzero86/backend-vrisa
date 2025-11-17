from rest_framework import serializers
from src.users.models import User, Role

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model: type = Role
        fields: list[str] = ['role_id', 'role_name']

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for reading and displaying User data.
    It includes nested role information.
    """
    role = RoleSerializer(read_only=True)

    class Meta:
        model: type = User
        fields: list[str] = ['id', 'email', 'first_name', 'last_name', 'is_active', 'role']

class RegisterUserSerializer(serializers.ModelSerializer):
    """
    Serializer specifically for user registration.
    It handles password validation and creation.
    """
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    role_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model: type = User
        # Fields required for registration
        fields: list[str] = ['email', 'password', 'first_name', 'last_name', 'role_id']

    def create(self: 'RegisterUserSerializer', validated_data: dict) -> User:
        """
        Create and return a new user instance, given the validated data.
        """
        role_id: Optional[int] = validated_data.pop('role_id', None)
        
        # Use the custom manager's create_user method to handle password hashing
        user: User = User.objects.create_user(**validated_data)
        
        if role_id:
            try:
                role: Role = Role.objects.get(pk=role_id)
                user.role = role
                user.save()
            except Role.DoesNotExist:
                # Optionally handle this error, e.g., by raising a validation error
                pass
                
        return user
