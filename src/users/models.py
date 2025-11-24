from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from src.institutions.models import EnvironmentalInstitution


class Permission(models.Model):
    """
    Representa una acción específica o recurso protegido en el sistema (tabla 'permission').
    
    Ejemplos: 'create_station', 'view_reports', 'validate_user'.
    """
    permission_id = models.AutoField(primary_key=True)
    permission_name = models.CharField(
        max_length=150, 
        unique=True, 
        verbose_name="Nombre del Permiso"
    )
    description = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Descripción"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    def __str__(self) -> str:
        return self.permission_name

    class Meta:
        db_table = 'permission'
        verbose_name = 'Permiso'
        verbose_name_plural = 'Permisos'

class Role(models.Model):
    """
    Representa el rol del usuario en el sistema (relación 'role').
    
    Define los niveles de permiso y acceso dentro de la plataforma VRISA.
    Ejemplos: Administrador, Técnico, Investigador.
    """
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.role_name
    
    class Meta:
        db_table = 'role'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'

class CustomUserManager(BaseUserManager):
    """
    Gestor personalizado de usuarios.

    Reemplaza el comportamiento por defecto de Django para utilizar el  correo electrónico (email)
    como identificador único en lugar del 'username'.
    """
    def create_user(self, email, password = None, **extra_fields):
        """
        Crea y guarda un usuario con el email y contraseña dados.
        """
        if not email:
            raise ValueError(_('El correo electrónico es obligatorio.'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password = None, **extra_fields):
        """
        Crea y guarda un superusuario con permisos de staff y superuser.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('El superusuario debe tener is_staff=True.'))
        
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    """
    Modelo de Usuario personalizado para el sistema VRISA (tabla 'user').

    Extiende de AbstractUser para mantener las funcionalidades de autenticación de Django.

    Atributos principales:
        email: Identificador único del usuario.
        job_title: Cargo laboral dentro de la institución, es opcional.
        institution: Relación con la entidad ambiental a la que pertenece, es opcional.
        professional_card_*: Archivos digitales de la tarjeta profesional, es opcional.
    """
    username = None
    email = models.EmailField(_('dirección de correo'), unique=True)
    job_title = models.CharField(max_length=150, blank=True, null=True)
    professional_card_front = models.ImageField(upload_to='users/cards/', blank=True, null=True)
    professional_card_rear = models.ImageField(upload_to='users/cards/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    institution = models.ForeignKey(
        EnvironmentalInstitution, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='users'
    )

    roles = models.ManyToManyField(
        Role, 
        through='UserRole',
        through_fields=('user', 'role'), 
        related_name='users',
        verbose_name="Roles asignados"
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = CustomUserManager() # type: ignore
    
    def __str__(self) -> str:
        return self.email

    class Meta:
        db_table = 'user'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

class UserRole(models.Model):
    """
    Relación intermedia para asignar roles a los usuarios (tabla 'user_role').

    Gestiona la relación de muchos a muchos entre Usuarios y Roles, permitiendo
    registrar quién realizó la asignación del rol (trazabilidad).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    
    assigned_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_roles_history'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_role'
        unique_together = ('user', 'role')


class RolePermission(models.Model):
    """
    Modelo intermedio para la tabla 'rol_permission' (según diagrama).
    
    Vincula Roles con Permisos, permitiendo definir qué puede hacer cada rol
    y dejando registro de qué administrador configuró ese permiso.
    """
    role = models.ForeignKey(Role, on_delete=models.CASCADE, verbose_name="Rol")
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, verbose_name="Permiso")
    
    # Campo requerido por el diagrama: granted_by
    granted_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='granted_permissions_history',
        verbose_name="Otorgado por"
    )
    
    granted_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de otorgamiento")

    class Meta:
        db_table = 'rol_permission'
        unique_together = ('role', 'permission')
        verbose_name = 'Permiso de Rol'
        verbose_name_plural = 'Permisos de Roles'