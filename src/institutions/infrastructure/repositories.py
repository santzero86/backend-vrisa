from typing import Optional
from src.institutions.domain.entities import EnvironmentalInstitution as InstitutionEntity
from src.institutions.models import EnvironmentalInstitution as InstitutionModel
from src.users.models import User
from .mappers import InstitutionMapper

class InstitutionRepository:
    def save(self, institution_entity: InstitutionEntity) -> InstitutionEntity:
        institution_model = InstitutionMapper.entity_to_model(institution_entity)
        institution_model.save()
        return InstitutionMapper.model_to_entity(institution_model)

    def find_by_name(self, name: str) -> Optional[InstitutionEntity]:
        try:
            institution_model = InstitutionModel.objects.get(institute_name=name)
            return InstitutionMapper.model_to_entity(institution_model)
        except InstitutionModel.DoesNotExist:
            return None
        
    def find_by_id(self, institution_id: int) -> Optional[InstitutionEntity]:
        try:
            institution_model = InstitutionModel.objects.get(pk=institution_id)
            return InstitutionMapper.model_to_entity(institution_model)
        except InstitutionModel.DoesNotExist:
            return None