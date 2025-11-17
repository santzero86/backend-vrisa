from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

class UserType(models.Model):
    """
    Representa el tipo de usuario en el sistema, e.g., 'Técnico', 'Autoridad', 'Ciudadano'.
    """
    user_type_id: int = models.AutoField(primary_key=True)
    user_type_name: str = models.CharField(max_length=100, unique=True)
    
    # A user-friendly representation of the object.
    def __str__(self: 'UserType') -> str:
        return self.user_type_name

class Role(models.Model):
    """
    Representa el rol de un usuario, que define sus permisos y niveles de acceso.
    """
    role_id: int = models.AutoField(primary_key=True)
    role_name: str = models.CharField(max_length=100, unique=True)
    created_at: str = models.DateTimeField(auto_now_add=True)
    updated_at: str = models.DateTimeField(auto_now=True)
    
    def __str__(self: 'Role') -> str:
        return self.role_name

class CustomUserManager(BaseUserManager):
    """
    Manager personalizado para el modelo User.
    El email es el identificador único para la autenticación en lugar de nombres de usuario.
    """
    def create_user(self: 'CustomUserManager', email: str, password: str, **extra_fields) -> 'User':
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user: 'User' = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self: 'CustomUserManager', email: str, password: str, **extra_fields) -> 'User':
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Clase base para el modelo de User para el sistema VRISA.
    """
    # Remove username field from the model, we'll use email instead
    username = None

    # Redefine the email field to be unique
    email: str = models.EmailField(_('email address'), unique=True)
    
    # Foreign keys to Role and UserType
    # We use models.SET_NULL to avoid deleting the user if their role is deleted.
    # The role could be set to NULL or reassigned.
    role: Role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    user_type: UserType = models.ForeignKey(UserType, on_delete=models.SET_NULL, null=True, blank=True)

    # Set the unique identifier for login
    USERNAME_FIELD: str = 'email'
    # Required fields for createsuperuser command
    REQUIRED_FIELDS: list[str] = ['first_name', 'last_name']
    
    # Custom manager
    objects: CustomUserManager = CustomUserManager()
    
    def __str__(self: 'User') -> str:
        return self.email