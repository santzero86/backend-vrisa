from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from src.users.models import User, Role, UserType

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Personaliza la representación del modelo Usuario en el panel de administración.
    """
    # Campos a mostrar en la lista de registros
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'role')    
    # Filtros laterales
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información personal', {'fields': ('first_name', 'last_name')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas importantes', {'fields': ('last_login', 'date_joined')}),
        ('Campos Personalizados', {'fields': ('role', 'user_type')}), # Tus campos extra
    )
    
    # Campos para el formulario de creación
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'password2'),
        }),
    )
    
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('role_id', 'role_name', 'created_at')
    search_fields = ('role_name',)

@admin.register(UserType)
class UserTypeAdmin(admin.ModelAdmin):
    list_display = ('user_type_id', 'user_type_name')
    search_fields = ('user_type_name',)
