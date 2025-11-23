from django.db import transaction
from django.shortcuts import get_object_or_404
from src.users.models import User, Role

def create_user(validated_data: dict) -> User:
    """
    Lógica de negocio para registrar un nuevo usuario en VRISA.
    
    Proceso:
    1. Extrae los datos validados.
    2. Inicia una transacción atómica para asegurar integridad.
    3. Vincula el usuario a la Institución especificada.
    4. Guarda los archivos de la tarjeta profesional si se proporcionan.
    5. Crea el usuario con 'is_active=False' (esperando validación de admin).
    
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
    institution_id = validated_data['institution_id']
    
    card_front = validated_data.get('professional_card_front')
    card_rear = validated_data.get('professional_card_rear')

    # transaccion para crear el usuario y asignar un rol por defecto hasta que un admin que lo verifique
    with transaction.atomic():
        institution = get_object_or_404(Institution, pk=institution_id)

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            job_title=job_title,
            institution=institution,
            professional_card_front=card_front,
            professional_card_rear=card_rear,
            is_active=False # Inactivo hasta verificación por administrador del sistema
        )

    return user

def get_user_by_id(user_id: int) -> User:
    """
    Método para obtener un usuario por su ID.
    Lanza Http404 si no se encuentra.
    """
    user = get_object_or_404(User, pk=user_id)
    return user
