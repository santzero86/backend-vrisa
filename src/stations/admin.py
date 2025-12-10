from django.contrib import admin
from src.stations.models import MonitoringStation

@admin.register(MonitoringStation)
class MonitoringStationAdmin(admin.ModelAdmin):
    """
    Configuración del panel de administración para el modelo MonitoringStation.
    Actualizado para usar PostGIS PointField.
    """
    list_display = (
        'station_name',
        'operative_status',
        'institution',
        'get_latitude',
        'get_longitude'
    )
    list_filter = ('operative_status', 'institution')
    search_fields = ('station_name', 'institution__institute_name')

    # El token debe ser solo visible
    readonly_fields = ('authentication_token', 'created_at', 'updated_at')

    fieldsets = (
        (None, {'fields': ('station_name', 'institution', 'manager_user', 'address_reference')}),
        ('Ubicación y Estado', {'fields': ('location', 'operative_status')}),
        ('Credenciales', {'fields': ('authentication_token',)}),
        ('Auditoría', {'fields': ('created_at', 'updated_at')}),
    )

    def get_latitude(self, obj):
        """Extrae la latitud del campo Point para mostrar en list_display."""
        return round(obj.location.y, 6) if obj.location else None
    get_latitude.short_description = 'Latitud'

    def get_longitude(self, obj):
        """Extrae la longitud del campo Point para mostrar en list_display."""
        return round(obj.location.x, 6) if obj.location else None
    get_longitude.short_description = 'Longitud'
