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
            role = Role.objects.get(role_name='citizen')
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
