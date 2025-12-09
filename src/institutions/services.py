from .models import EnvironmentalInstitution, InstitutionColorSet, IntegrationRequest
from django.db import transaction
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from src.users.models import User, UserRole
from common.validation import ValidationStatus

class InstitutionService:    
    """
    Capa de servicio para manejar la lógica de negocio de las Instituciones.
    """
    @staticmethod
    def create_institution(data: dict, colors_list: list[str]) -> EnvironmentalInstitution:
        """
        Crea una institución y asigna sus colores corporativos de forma atómica.
        Args:
            data (dict): Diccionario con los datos del modelo EnvironmentalInstitution.
            colors_list (list[str]): Lista de códigos hexadecimales de color.
        Returns:
            EnvironmentalInstitution: La instancia creada con sus relaciones.
        Raises:
            ValidationError: Si se supera el límite de colores permitidos (máx 5).
        """
        with transaction.atomic():
            # 1. Crear la entidad padre
            institution = EnvironmentalInstitution.objects.create(**data)
            # 2. Procesar y crear las entidades hijas (Colores)
            if colors_list:
                # Validamos reglas de negocio extra si fuera necesario (ej: máx 3 colores)
                if len(colors_list) > 5:
                    raise ValidationError("Una institución no puede tener más de 5 colores corporativos.")

                color_objects = [
                    InstitutionColorSet(institution=institution, color_hex=color)
                    for color in colors_list
                ]
                # Bulk create es más eficiente para bases de datos grandes
                InstitutionColorSet.objects.bulk_create(color_objects)

            return institution

    @staticmethod
    def get_all_institutions():
        return EnvironmentalInstitution.objects.all().prefetch_related('colors')
    
    @staticmethod
    def register_institution(data: dict, colors: list, representative_user: User) -> EnvironmentalInstitution:
        """
        Registra una institución, sus colores y asigna al usuario creador como representante
        dentro de una transacción atómica.
        """
        unique_colors = list(set(colors))
        with transaction.atomic():
            institution = EnvironmentalInstitution.objects.create(**data)

            color_objects = [
                InstitutionColorSet(institution=institution, color_hex=color)
                for color in unique_colors 
            ]
            InstitutionColorSet.objects.bulk_create(color_objects)

            # Actualizamos el usuario representante para que pertenezca a esta institución
            representative_user.institution = institution
            representative_user.save()
        
        return institution
    
    @staticmethod
    def approve_institution_service(institution_id: int):
        """
        Cambia el estado de validación de una institución a ACCEPTED.
        También aprueba los roles de los usuarios representantes de la institución.
        """
        institution = get_object_or_404(EnvironmentalInstitution, pk=institution_id)

        if institution.validation_status == 'ACCEPTED':
            # Opcional: Lanzar error o simplemente retornar sin cambios
            return institution

        with transaction.atomic():
            # 1. Aprobar la institución
            institution.validation_status = 'ACCEPTED'
            institution.save()

            # 2. Aprobar los roles de los usuarios asociados a esta institución
            # que tengan roles pendientes (representantes/miembros de la institución)
            users_in_institution = User.objects.filter(institution=institution)
            UserRole.objects.filter(
                user__in=users_in_institution,
                approved_status=ValidationStatus.PENDING
            ).update(approved_status=ValidationStatus.ACCEPTED)

        return institution

class IntegrationRequestService:
    """
    Capa de servicio para gestionar el flujo de aprobación de solicitudes.
    """
    @staticmethod
    def create_request(data: dict) -> IntegrationRequest:
        """
        Registra una nueva solicitud de integración validando duplicados.

        Evita que una misma institución tenga múltiples solicitudes pendientes
        simultáneamente (prevención de spam).
        """
        existing_pending = IntegrationRequest.objects.filter(
            institution=data['institution'], 
            request_status=IntegrationRequest.RequestStatus.PENDING
        ).exists()
        
        if existing_pending:
            raise ValidationError("Esta institución ya tiene una solicitud pendiente.")

        return IntegrationRequest.objects.create(**data)

    @staticmethod
    def approve_request(request_id: int, user) -> IntegrationRequest:
        """
        Aprueba una solicitud existente, registrando auditoría del revisor.
        Args:
            request_id (int): ID de la solicitud.
            user (User): Usuario administrador que realiza la aprobación.
        Returns:
            IntegrationRequest: La solicitud actualizada con estado APPROVED.
        """
        try:
            integration_request = IntegrationRequest.objects.get(pk=request_id)
        except IntegrationRequest.DoesNotExist:
            raise ValidationError(f"Solicitud {request_id} no encontrada.")

        with transaction.atomic():
            integration_request.request_status = IntegrationRequest.RequestStatus.APPROVED
            integration_request.reviewed_by = user
            integration_request.review_date = timezone.now()
            integration_request.save()
            
        return integration_request
