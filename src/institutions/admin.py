from django.contrib import admin
from src.institutions.models import EnvironmentalInstitution, IntegrationRequest, InstitutionColorSet

class InstitutionColorSetInline(admin.TabularInline):
    """
    Permite la edición inline de colores dentro del panel de la Institución.
    """
    model = InstitutionColorSet
    extra = 1

# Panel para Instituciones: Búsqueda por nombre/email rep, filtro por fecha creación.
@admin.register(EnvironmentalInstitution)
class EnvironmentalInstitutionAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para Instituciones.
    Incluye búsqueda por representante y filtros de fecha.
    """
    list_display = ('institute_name', 'physic_address', 'created_at')
    search_fields = ('institute_name', 'representative__email')
    list_filter = ('created_at',)
    inlines = [InstitutionColorSetInline] 

# Panel para solicitudes: Visualiza estado y fechas. Búsqueda por nombre de institución asociada.
@admin.register(IntegrationRequest)
class IntegrationRequestAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para Solicitudes.
    Visualiza el estado, fechas y quién revisó la solicitud.
    """
    list_display = ('institution', 'request_status', 'request_date', 'reviewed_by')
    search_fields = ('institution__institute_name',)
    list_filter = ('request_status', 'request_date')