from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from src.users.models import User, Role, UserType

class UserRoleInline(admin.TabularInline):
    """
    Permite la edición en línea de los roles asignados a un usuario 
    directamente desde la vista de detalle del Usuario en el Admin.
    
    Esto visualiza la tabla 'user_role'.
    """
    model = UserRole
    extra = 1
    autocomplete_fields = ['role']

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Configuración del panel de administración para el modelo User.
    Organiza los campos en grupos lógicos y muestra las relaciones nuevas.
    """
    # Campos a mostrar en la lista de registros
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'role')    
    # Filtros laterales
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información personal', {
            'fields': ('first_name', 'last_name')
        }),
        'Documentación Profesional', ({
            'fields': ('professional_card_front', 'professional_card_rear')
        }),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Fechas importantes', {
            'fields': ('last_login', 'date_joined')
        }),
        ('Campos Personalizados', {
            'fields': ('role', 'user_type')
        }),
        ('Auditoría', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')
        })
    )
    readonly_fields = ('created_at', 'updated_at', 'last_login', 'date_joined')
    
    # Campos para el formulario de creación
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'password2', 'first_name', 'last_name', 'institution'),
        }),
    )
    
    search_fields = ('email', 'first_name', 'last_name', 'institution__institute_name')
    ordering = ('email',)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """
    Administración de los roles del sistema.
    """
    list_display = ('role_id', 'role_name', 'created_at')
    search_fields = ('role_name',)

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """
    Administración directa de la tabla intermedia user_role (opcional).
    Útil para auditoría de quién asignó qué rol.
    """
    list_display = ('user', 'role', 'assigned_by', 'assigned_at')
    list_filter = ('role', 'assigned_at')
    search_fields = ('user__email', 'role__role_name')
