from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

class UserType(models.Model):
    """
    Representa el tipo de usuario en el sistema (ej. 'Técnico', 'Autoridad').
    """
    user_type_id = models.AutoField(primary_key=True)
    user_type_name = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        return self.user_type_name

class Role(models.Model):
    """
    Representa el rol del usuario, definiendo sus niveles de permiso y acceso.
    """
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.role_name

class CustomUserManager(BaseUserManager):
    """
    Manager personalizado donde el correo electrónico (email) es el identificador 
    único para la autenticación en lugar del nombre de usuario.
    """
    def create_user(self, email: str, password: str = None, **extra_fields):
        if not email:
            raise ValueError(_('El correo electrónico es obligatorio.'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str = None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('El superusuario debe tener is_staff=True.'))
        
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    """
    Modelo de Usuario personalizado para el sistema VRISA usando email como username.
    """
    username = None
    email = models.EmailField(_('dirección de correo'), unique=True)
    
    # Usamos SET_NULL para no borrar al usuario si se borra su rol o tipo
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    user_type = models.ForeignKey(UserType, on_delete=models.SET_NULL, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = CustomUserManager()
    
    def __str__(self) -> str:
        return self.email
