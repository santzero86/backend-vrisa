from .models import EnvironmentalInstitution, InstitutionColorSet
from django.db import transaction
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from src.users.models import User

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
        """
        institution = get_object_or_404(EnvironmentalInstitution, pk=institution_id)

        if institution.validation_status == 'ACCEPTED':
            # Opcional: Lanzar error o simplemente retornar sin cambios
            return institution

        institution.validation_status = 'ACCEPTED'
        institution.save()
        return institution
