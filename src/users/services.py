from django.db import transaction
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
    email = validated_data['email']
    password = validated_data['password']
    first_name = validated_data['first_name']
    last_name = validated_data['last_name']
    job_title = validated_data.get('job_title', '')
    institution_id = validated_data.get('institution_id')
    phone = validated_data['phone']
    
    card_front = validated_data.get('professional_card_front')
    card_rear = validated_data.get('professional_card_rear')
    
    requested_role_slug = validated_data.pop('requested_role', 'citizen')

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
            is_active=True  # Activo por defecto
        ) # type: ignore
        
        if requested_role_slug == 'citizen':
            # Los ciudadanos se aprueban automáticamente
            role = get_object_or_404(Role, role_name='citizen')
            UserRole.objects.create(
                user=user, 
                role=role, 
                approved_status=ValidationStatus.ACCEPTED # Aprobado automáticamente
            )
        else:
            # Roles institucionales quedan PENDING
            role = get_object_or_404(Role, role_name=requested_role_slug)
            
            UserRole.objects.create(
                user=user, 
                role=role, 
                approved_status=ValidationStatus.PENDING
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
    document_type = validated_data['document_type']
    document_number = validated_data['document_number']
    institution_name = validated_data['institution']
    front_card = validated_data['front_card']
    back_card = validated_data['back_card']
    
    with transaction.atomic():
        # Actualizar datos del usuario existente
        user.job_title = f"{document_type}: {document_number} - {institution_name}"
        user.professional_card_front = front_card
        user.professional_card_rear = back_card
        user.save()
        
        # Verificar que tenga rol de investigador, si no lo tiene, crearlo
        researcher_role, _ = Role.objects.get_or_create(role_name='researcher')
        user_role, created = UserRole.objects.get_or_create(
            user=user,
            role=researcher_role,
            defaults={'approved_status': ValidationStatus.PENDING}
        )
        
        # Si ya existía pero no está pendiente, mantenerlo como está
        # (podría estar APPROVED o REJECTED)
    
    return user


def get_pending_researcher_requests():
    """
    Obtiene todas las solicitudes de rol de investigador pendientes de aprobación.
    """
    return UserRole.objects.filter(
        role__role_name='researcher',
        approved_status=ValidationStatus.PENDING
    ).select_related('user', 'role', 'user__institution')


def approve_researcher_request(user_role_id: int, admin_user: User) -> UserRole:
    """
    Aprueba una solicitud de investigador.
    
    Args:
        user_role_id: ID de la asignación de rol a aprobar
        admin_user: Usuario admin que realiza la aprobación
        
    Returns:
        UserRole: La asignación actualizada
    """
    user_role = get_object_or_404(UserRole, pk=user_role_id)
    user_role.approved_status = ValidationStatus.ACCEPTED
    user_role.assigned_by = admin_user
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
