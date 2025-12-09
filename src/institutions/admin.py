from django.contrib import admin
from src.institutions.models import EnvironmentalInstitution, InstitutionColorSet

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
