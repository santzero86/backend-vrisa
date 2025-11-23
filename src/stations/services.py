from django.db import transaction
from django.shortcuts import get_object_or_404
from src.stations.models import MonitoringStation
from src.institutions.models import EnvironmentalInstitution
from src.users.models import User
import secrets

def create_station(validated_data: dict, user_id: int) -> MonitoringStation:
    """
    Crea una nueva estación de monitoreo en el sistema.
    
    Reglas de negocio:
    1. Verifica que la institución exista.
    2. Asigna automáticamente un token de autenticación seguro.
    3. Asigna al usuario creador como manager inicial (si aplica) o valida el manager enviado.
    
    Args:
        validated_data (dict): Datos validados del serializer.
        user_id (int): ID del usuario que realiza la acción (para auditoría o asignación).
        
    Returns:
        MonitoringStation: La instancia creada.
    """
    
    # Extraer datos básicos
    name = validated_data.get('station_name')
    lat = validated_data.get('geographic_location_lat')
    lon = validated_data.get('geographic_location_long')
    institution_id = validated_data.get('institution_id')
    
    # Verificar Institución
    institution = get_object_or_404(EnvironmentalInstitution, pk=institution_id)
    
    # Verificar Manager (si viene en los datos, usamos ese, si no, el usuario actual)
    manager_id = validated_data.get('manager_user_id', user_id)
    manager = get_object_or_404(User, pk=manager_id)

    with transaction.atomic():
        # Crear la estación
        # Nota: El método .save() del modelo se encargará de generar el token si falta
        station = MonitoringStation.objects.create(
            station_name=name,
            geographic_location_lat=lat,
            geographic_location_long=lon,
            institution=institution,
            manager_user=manager,
            operative_status=MonitoringStation.OperativeStatus.INACTIVE # Nace inactiva por defecto
        )
        
    return station

def regenerate_station_token(station_id: int) -> str:
    """
    Regenera el token de autenticación de una estación por seguridad.
    Útil si se sospecha que las credenciales de la estación fueron comprometidas.
    """
    station = get_object_or_404(MonitoringStation, pk=station_id)
    new_token = secrets.token_hex(32)
    
    station.authentication_token = new_token
    station.save()
    
    return new_token