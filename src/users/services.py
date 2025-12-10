from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from common.validation import ValidationStatus
from src.users.models import User, Role, UserRole
from src.institutions.models import EnvironmentalInstitution


def create_user(validated_data: dict) -> User:
    """
    Lógica de negocio para registrar un nuevo usuario en VRISA.

    Proceso:
    1. Extrae los datos validados.
    2. Inicia una transacción atómica para asegurar integridad.
    3. Vincula el usuario a la Institución especificada.
    4. Guarda los archivos de la tarjeta profesional si se proporcionan.
    5. Crea el usuario con 'is_active=True'.

    Args:
        validated_data (dict): Diccionario con datos ya validados por el serializador.

    Returns:
        User: Instancia del usuario creado.
    """
    email = validated_data["email"]
    password = validated_data["password"]
    first_name = validated_data["first_name"]
    last_name = validated_data["last_name"]
    job_title = validated_data.get("job_title", "")
    institution_id = validated_data.get("institution_id")
    phone = validated_data["phone"]

    card_front = validated_data.get("professional_card_front")
    card_rear = validated_data.get("professional_card_rear")

    requested_role_slug = validated_data.pop("requested_role", "citizen")

    # transaccion para crear el usuario y asignar un rol por defecto hasta que un admin que lo verifique
    with transaction.atomic():
        institution = None
        if institution_id:
            institution = get_object_or_404(EnvironmentalInstitution, pk=institution_id)

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            job_title=job_title,
            phone=phone,
            institution=institution,
            professional_card_front=card_front,
            professional_card_rear=card_rear,
            is_active=True,  # Activo por defecto
        )  # type: ignore

        if requested_role_slug == "citizen":
            # Los ciudadanos se aprueban automáticamente
            role = get_object_or_404(Role, role_name="citizen")
            UserRole.objects.create(
                user=user,
                role=role,
                approved_status=ValidationStatus.ACCEPTED,  # Aprobado automáticamente
            )
        else:
            # Roles institucionales quedan PENDING
            role = get_object_or_404(Role, role_name=requested_role_slug)

            UserRole.objects.create(
                user=user, role=role, approved_status=ValidationStatus.PENDING
            )

    return user


def complete_researcher_registration(user: User, validated_data: dict) -> User:
    """
    Completa el registro de un investigador existente en VRISA.

    Actualiza los datos del usuario ya registrado con la información adicional
    requerida para investigadores (documento, tarjeta profesional, etc.).

    Args:
        user (User): Usuario autenticado que está completando su registro.
        validated_data (dict): Diccionario con datos ya validados por el serializador.

    Returns:
        User: Instancia del usuario actualizado.
    """
    document_type = validated_data["document_type"]
    document_number = validated_data["document_number"]
    front_card = validated_data["front_card"]
    back_card = validated_data["back_card"]
    
    institution_id = validated_data.get("institution_id")
    is_independent = validated_data.get("is_independent", False)
    
    institution_ref = None
    institution_name_str = "Independiente"

    if institution_id:
        institution_ref = get_object_or_404(EnvironmentalInstitution, pk=institution_id)
        institution_name_str = institution_ref.institute_name
    elif not is_independent:
        institution_name_str = validated_data.get("institution", "No especificada")

    with transaction.atomic():
        # Actualizar datos del usuario existente
        user.job_title = f"{document_type}: {document_number} - {institution_name_str}"
        
        # Actualizar relación con institución (Si es independiente, esto será None)
        user.institution = institution_ref
        
        user.professional_card_front = front_card
        user.professional_card_rear = back_card
        user.save()

        # Verificar que tenga rol de investigador, si no lo tiene, crearlo
        researcher_role, _ = Role.objects.get_or_create(role_name="researcher")
        
        # Buscar si ya tiene el rol asignado
        UserRole.objects.update_or_create(
            user=user,
            role=researcher_role,
            defaults={"approved_status": ValidationStatus.PENDING}
        )
    
    return user


def get_pending_researcher_requests(requesting_user):
    """
    Obtiene las solicitudes pendientes de investigadores.

    Lógica de filtrado:
    1. Si es Super Admin: Ve los investigadores 'Independientes' (sin institución).
    2. Si es Institution Head: Ve SOLO los investigadores que solicitaron unirse a SU institución.
    """
    queryset = UserRole.objects.filter(
        role__role_name="researcher", approved_status=ValidationStatus.PENDING
    ).select_related("user", "role", "user__institution")

    if requesting_user.is_superuser:
        # El super admin se encarga de gestionar investigadores independientes
        return queryset.filter(user__institution__isnull=True)

    if requesting_user.institution:
        # El representante de institución solo ve los de su propia institución
        return queryset.filter(user__institution=requesting_user.institution)

    return queryset.none()


def approve_researcher_request(user_role_id: int, approver_user: User) -> UserRole:
    """
    Aprueba una solicitud de investigador.

    Args:
        user_role_id: ID de la asignación de rol a aprobar
        admin_user: Usuario admin que realiza la aprobación

    Returns:
        UserRole: La asignación actualizada
    """
    user_role = get_object_or_404(UserRole, pk=user_role_id)
    target_user = user_role.user

    # Reglas de Seguridad
    if approver_user.is_superuser:
        # El super admin solo debería aprobar independientes
        pass
    elif approver_user.institution:
        # Validar que el usuario objetivo pertenezca a la MISMA institución del aprobador
        if target_user.institution != approver_user.institution:
            raise PermissionError(
                "No puedes aprobar investigadores de otra institución o independientes."
            )
    else:
        raise PermissionError("No tienes permisos para aprobar solicitudes.")

    user_role.approved_status = ValidationStatus.ACCEPTED
    user_role.assigned_by = approver_user
    user_role.save()
    return user_role


def reject_researcher_request(user_role_id: int, admin_user: User) -> UserRole:
    """
    Rechaza una solicitud de investigador.

    Args:
        user_role_id: ID de la asignación de rol a rechazar
        admin_user: Usuario admin que realiza el rechazo

    Returns:
        UserRole: La asignación actualizada
    """
    user_role = get_object_or_404(UserRole, pk=user_role_id)
    user_role.approved_status = ValidationStatus.REJECTED
    user_role.assigned_by = admin_user
    user_role.save()
    return user_role


def get_user_by_id(user_id: int) -> User:
    """
    Método para obtener un usuario por su ID.
    Lanza Http404 si no se encuentra.
    """
    user = get_object_or_404(User, pk=user_id)
    return user


def get_total_users_count() -> int:
    """
    Retorna el número total de usuarios registrados en el sistema.
    """
    return User.objects.count()


def get_user_stats_breakdown():
    """
    Retorna el conteo total y el desglose por roles.
    """
    total = User.objects.count()

    # Contar usuarios por rol principal
    roles_breakdown = (
        UserRole.objects.filter(approved_status=ValidationStatus.ACCEPTED)
        .values("role__role_name")
        .annotate(count=Count("id"))
    )

    # Convertir a un diccionario más limpio
    stats = {item["role__role_name"]: item["count"] for item in roles_breakdown}

    return {"total_users": total, "breakdown": stats}
