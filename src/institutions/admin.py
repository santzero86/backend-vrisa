from django.contrib import admin
from src.users.models import EnvironmentalInstitution, IntegrationRequest, InstitutionColorSet

# Permite editar los colores directamente dentro de la pantalla de la Institución (Master-Detail).
class InstitutionColorSetInline(admin.TabularInline):
    model = InstitutionColorSet
    extra = 1

# Panel para Instituciones: Búsqueda por nombre/email rep, filtro por fecha creación.
@admin.register(EnvironmentalInstitution)
class EnvironmentalInstitutionAdmin(admin.ModelAdmin):
    list_display = ('institute_name', 'physic_address', 'created_at')
    search_fields = ('institute_name', 'representative__email')
    list_filter = ('created_at',)
    inlines = [InstitutionColorSetInline] 

# Panel para solicitudes: Visualiza estado y fechas. Búsqueda por nombre de institución asociada.
@admin.register(IntegrationRequest)
class IntegrationRequestAdmin(admin.ModelAdmin):
    list_display = ('institution', 'request_status', 'request_date', 'reviewed_by')
    search_fields = ('institution__institute_name',)
    list_filter = ('request_status', 'request_date')