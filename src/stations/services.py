import secrets
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
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
    address = validated_data.get('address_reference', '')
    institution_id = validated_data.get("institution_id")

    # Verificar Institución
    institution = get_object_or_404(EnvironmentalInstitution, pk=institution_id)

    # Verificar Manager (si viene en los datos, usamos ese, si no, el usuario actual)
    manager_id = validated_data.get("manager_user_id", user_id)
    manager = get_object_or_404(User, pk=manager_id)

    # Crear Point a partir de lat/long (IMPORTANTE: Point(longitud, latitud))
    location_point = Point(lon, lat, srid=4326)

    with transaction.atomic():
        station = MonitoringStation.objects.create(
            station_name=name,
            location=location_point,
            address_reference=address,
            institution=institution,
            manager_user=manager,
            operative_status=OperativeStatus.PENDING
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


def get_nearby_stations(latitude: float, longitude: float, radius_km: float):
    """
    Obtiene estaciones de monitoreo cercanas a una ubicación dada.

    Utiliza consultas espaciales de PostGIS para encontrar estaciones dentro
    de un radio especificado, ordenadas por distancia.

    Args:
        latitude (float): Latitud del punto de referencia
        longitude (float): Longitud del punto de referencia
        radius_km (float): Radio de búsqueda en kilómetros

    Returns:
        QuerySet: Estaciones ordenadas por distancia, con atributo 'distance' anotado
    """
    # Crear punto de referencia (IMPORTANTE: Point(longitud, latitud))
    reference_point = Point(longitude, latitude, srid=4326)

    # Buscar estaciones dentro del radio especificado
    # D() permite especificar distancias en diferentes unidades (km, m, mi, etc.)
    nearby_stations = (
        MonitoringStation.objects
        .filter(location__distance_lte=(reference_point, D(km=radius_km)))
        .annotate(distance=Distance('location', reference_point))
        .order_by('distance')
    )

    return nearby_stations
