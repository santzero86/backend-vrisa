# src/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from src.users.models import User, Role, UserType

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Customizes the User model representation in the admin panel.
    """
    # Fields to display in the list view
    list_display: tuple[str] = ('email', 'first_name', 'last_name', 'is_staff', 'role')
    
    # Fields to search by
    search_fields: tuple[str] = ('email', 'first_name', 'last_name')
    
    # Fields to filter by
    list_filter: tuple[str] = ('is_staff', 'is_superuser', 'is_active', 'groups')
    
    # We need to declare fieldsets because we're using a custom user model
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Custom Fields', {'fields': ('role', 'user_type')}), # Add your custom fields here
    )
    
    # Fields for the creation form
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'password2'), # For password confirmation
        }),
    )
    
    # Which field is used for ordering
    ordering: tuple[str] = ('email',)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display: tuple[str] = ('role_id', 'role_name', 'created_at')
    search_fields: tuple[str] = ('role_name',)

@admin.register(UserType)
class UserTypeAdmin(admin.ModelAdmin):
    list_display: tuple[str] = ('user_type_id', 'user_type_name')
    search_fields: tuple[str] = ('user_type_name',)
