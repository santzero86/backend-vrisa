from django.db import transaction
from django.shortcuts import get_object_or_404
from src.users.models import User, Role

def create_user(validated_data: dict) -> User:
    """
    Lógica de negocio para crear un usuario.
    Maneja la creación del registro y la asignación de relaciones.
    """
    email = validated_data['email']
    password = validated_data['password']
    first_name = validated_data['first_name']
    last_name = validated_data['last_name']
    role_id = validated_data.get('role_id')

    # La transacción atómica asegura la integridad (ej. si falla la asignación de rol, no se crea el usuario)
    with transaction.atomic():
        # Usar el manager personalizado para manejar el hash de la contraseña automáticamente
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Manejar lógica de asignación de Rol
        if role_id:
            # Intentamos obtener el rol; si se provee ID, el rol debe existir.
            # get_object_or_404 lanzará un error 404 si el ID no es válido.
            role = get_object_or_404(Role, pk=role_id)
            user.role = role
            user.save()
            
    return user

def get_user_by_id(user_id: int) -> User:
    """
    Lógica de negocio para obtener un usuario.
    """
    # get_object_or_404 es un atajo que lanza Http404,
    # el cual DRF captura y convierte en una respuesta 404 automáticamente.
    user = get_object_or_404(User, pk=user_id)
    return user
