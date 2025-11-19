from src.institutions.domain.entities import EnvironmentalInstitution as InstitutionEntity
from src.institutions.domain.entities import UserInfo
from src.institutions.models import EnvironmentalInstitution as InstitutionModel, InstitutionColorSet
from src.users.models import User

class InstitutionMapper:
    #Traduce entre la entidad de dominio EnvironmentalInstitution y el modelo de Django.
    @staticmethod
    def model_to_entity(institution_model: InstitutionModel) -> InstitutionEntity:
        #Convierte un objeto del modelo de Django a una entidad de dominio.
        representative_info = None
        if institution_model.representative:
            representative_info = UserInfo(
                id=institution_model.representative.id,
                full_name=institution_model.representative.get_full_name()
            )
            
        # Obtenemos todos los objetos de color asociados y extraemos el valor hexadecimal
        color_list = [color.color_hex for color in institution_model.colors.all()]

        return InstitutionEntity(
            id=institution_model.id,
            institute_name=institution_model.institute_name,
            physic_address=institution_model.physic_address,
            representative=representative_info,
            logo_url=institution_model.institute_logo.url if institution_model.institute_logo else None,
            colors=color_list
        )

    @staticmethod
    def entity_to_model(institution_entity: InstitutionEntity) -> InstitutionModel:
        if institution_entity.id:
            institution_model = InstitutionModel.objects.get(pk=institution_entity.id)
        else:
            # Si no tiene ID, es una nueva instancia.
            institution_model = InstitutionModel()

        # Mapeamos los campos
        institution_model.institute_name = institution_entity.institute_name
        institution_model.physic_address = institution_entity.physic_address
        
        # Asignamos el representante por su ID
        if institution_entity.representative:
            institution_model.representative_id = institution_entity.representative.id
        else:
            institution_model.representative_id = None

        return institution_model