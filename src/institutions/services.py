from django.db import transaction
from django.core.exceptions import ValidationError
from .models import EnvironmentalInstitution, InstitutionColorSet, IntegrationRequest
from django.utils import timezone

# Crea institución y colores de forma atómica. Falla todo si algo falla (ACID).
# Recibe: data (dict con datos básicos), colors_list (lista de hex strings).
# Devuelve: La instancia EnvironmentalInstitution creada.
# Lanza: ValidationError si se superan los 5 colores permitidos.
class InstitutionService:    
    @staticmethod
    def create_institution(data: dict, colors_list: list[str]) -> EnvironmentalInstitution:
        # Iniciamos una transacción atómica. Si algo falla aquí, NADA se guarda en la BD.
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

# Registra una solicitud validando que la institución no tenga otra pendiente (evita spam).
# Recibe: data (dict validado). Devuelve: Instancia IntegrationRequest.
# Lanza: ValidationError si ya existe una solicitud en estado PENDING.

class IntegrationRequestService:
    @staticmethod
    def create_request(data: dict) -> IntegrationRequest:
        existing_pending = IntegrationRequest.objects.filter(
            institution=data['institution'], 
            request_status=IntegrationRequest.RequestStatus.PENDING
        ).exists()
        
        if existing_pending:
            raise ValidationError("Esta institución ya tiene una solicitud pendiente.")

        return IntegrationRequest.objects.create(**data)

    # Aprueba una solicitud, actualiza timestamps y asigna el revisor.
    # Recibe: request_id (int), user (User admin). Devuelve: Instancia actualizada.
    # Lanza: ValidationError si el ID no existe.
    @staticmethod
    def approve_request(request_id: int, user) -> IntegrationRequest:
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