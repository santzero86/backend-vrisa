from django.contrib import admin
from src.stations.models import MonitoringStation

@admin.register(MonitoringStation)
class MonitoringStationAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para el modelo MonitoringStation.
    """
    list_display = (
        'station_name', 
        'operative_status', 
        'institution', 
        'geographic_location_lat', 
        'geographic_location_long'
    )
    list_filter = ('operative_status', 'institution')
    search_fields = ('station_name', 'institution__institute_name')
    
    # El token debe ser solo visible
    readonly_fields = ('authentication_token', 'created_at', 'updated_at')
    
    fieldsets = (
        (None, {'fields': ('station_name', 'institution', 'manager_user')}),
        ('Ubicación y Estado', {'fields': ('geographic_location_lat', 'geographic_location_long', 'operative_status')}),
        ('Credenciales', {'fields': ('authentication_token',)}),
        ('Auditoría', {'fields': ('created_at', 'updated_at')}),
    )