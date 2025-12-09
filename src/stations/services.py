import secrets
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from src.institutions.models import EnvironmentalInstitution
from src.stations.models import MonitoringStation, StationAffiliationRequest
from src.users.models import User


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

    with transaction.atomic():
        # Crear la estación
        # Nota: El método .save() del modelo se encargará de generar el token si falta
        station = MonitoringStation.objects.create(
            station_name=name,
            geographic_location_lat=lat,
            geographic_location_long=lon,
            address_reference=address,
            institution=institution,
            manager_user=manager,
            operative_status=MonitoringStation.OperativeStatus.INACTIVE,  # Nace inactiva por defecto
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


def create_affiliation_request(data: dict, user: User) -> StationAffiliationRequest:
    """
    Crea una solicitud de afiliación.
    Regla: Solo el Manager de la estación puede solicitar afiliarla a otra institución.
    """
    station = data.get("station")
    target_institution = data.get("target_institution")

    # Validar que la estación existe
    if not station:
        raise ValidationError("La estación es requerida.")

    # Validar que el usuario que crea la solicitud sea el manager de la estación
    if station.manager_user != user:
        raise ValidationError("No tienes permisos para gestionar esta estación.")

    #  Validar que no se esté solicitando a la misma institución actual
    if station.institution == target_institution:
        raise ValidationError("La estación ya pertenece a esta institución.")

    request = StationAffiliationRequest.objects.create(
        station=station,
        target_institution=target_institution,
        requester=user,
        status="PENDING",
    )
    return request


def review_affiliation_request(
    request_id: int, reviewer: User, new_status: str, comments: str
) -> StationAffiliationRequest:
    """
    Procesa la revisión (Aprobar/Rechazar) por parte de la Institución.
    """
    affiliation_req = get_object_or_404(StationAffiliationRequest, pk=request_id)

    # Validar que el revisor pertenezca a la institución destino
    if reviewer.institution != affiliation_req.target_institution:
        raise ValidationError(
            "No tienes permisos para gestionar solicitudes de esta institución."
        )

    with transaction.atomic():
        # Actualizar la solicitud
        affiliation_req.status = new_status
        affiliation_req.reviewed_by = reviewer
        affiliation_req.review_comments = comments
        affiliation_req.save()

        # Si se aprueba, se actualiza la institución a la que pertenece la estación
        if new_status == "ACCEPTED":
            station = affiliation_req.station
            station.institution = affiliation_req.target_institution
            station.operative_status = MonitoringStation.OperativeStatus.ACTIVE
            station.save()

    return affiliation_req
