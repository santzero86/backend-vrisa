import secrets
from django.db import transaction
from django.shortcuts import get_object_or_404
from common.validation import OperativeStatus, ValidationStatus
from src.institutions.models import EnvironmentalInstitution
from src.stations.models import MonitoringStation
from src.users.models import User, UserRole


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
    name = validated_data.get("station_name")
    lat = validated_data.get("geographic_location_lat")
    lon = validated_data.get("geographic_location_long")
    address = validated_data.get("address_reference", "")
    institution_id = validated_data.get("institution_id")

    # Verificar Institución
    institution = get_object_or_404(EnvironmentalInstitution, pk=institution_id)

    # Verificar Manager (si viene en los datos, usamos ese, si no, el usuario actual)
    manager_id = validated_data.get("manager_user_id", user_id)
    manager = get_object_or_404(User, pk=manager_id)

    with transaction.atomic():
        station = MonitoringStation.objects.create(
            station_name=name,
            geographic_location_lat=lat,
            geographic_location_long=lon,
            address_reference=address,
            institution=institution,
            manager_user=manager,
            operative_status=OperativeStatus.PENDING,
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



def approve_station_service(station_id: int) -> MonitoringStation:
    """
    Aprueba una estación de monitoreo y, como efecto en cascada,
    aprueba el rol de 'station_admin' del usuario manager asociado.
    """
    station = get_object_or_404(MonitoringStation, pk=station_id)

    # Si ya está activa, no hacemos nada (idempotencia)
    if station.operative_status == OperativeStatus.ACTIVE:
        return station

    with transaction.atomic():
        # 1. Actualizar estado de la estación
        station.operative_status = OperativeStatus.ACTIVE
        station.save()

        # 2. Actualizar estado del rol del usuario manager
        if station.manager_user:
            # Buscamos específicamente el rol de station_admin pendiente
            # para no aprobar accidentalmente otros roles que pueda tener solicitados.
            UserRole.objects.filter(
                user=station.manager_user,
                role__role_name="station_admin",
                approved_status=ValidationStatus.PENDING,
            ).update(approved_status=ValidationStatus.ACCEPTED)

    return station
