from src.institutions.domain.entities import EnvironmentalInstitution as InstitutionEntity, UserInfo
from src.institutions.infrastructure.repositories import InstitutionRepository
from src.users.infrastructure.repositories import UserRepository
from src.institutions.application.dto import CreateInstitutionDTO, InstitutionDTO
from common.exceptions import ConflictError, NotFoundError

class CreateInstitutionCommand:
    def __init__(self, institution_repo: InstitutionRepository, user_repo: UserRepository):
        self._institution_repo = institution_repo
        self._user_repo = user_repo

    def execute(self, create_dto: CreateInstitutionDTO) -> InstitutionDTO:
        # 1. Validar que la institución no exista
        if self._institution_repo.find_by_name(create_dto.institute_name):
            raise ConflictError(f"La institución '{create_dto.institute_name}' ya existe.")

        # 2. Validar que el usuario representante exista
        user_entity = self._user_repo.find_by_id(create_dto.representative_id)
        if not user_entity:
            raise NotFoundError(f"El usuario con ID '{create_dto.representative_id}' no fue encontrado.")

        # 3. Crear la entidad de dominio
        representative_info = UserInfo(id=user_entity.user_id, full_name=f"{user_entity.first_name} {user_entity.last_name}")
        
        new_institution_entity = InstitutionEntity(
            id=None, # La BD asignará el ID
            institute_name=create_dto.institute_name,
            physic_address=create_dto.physic_address,
            representative=representative_info
        )

        # 4. Persistir la entidad usando el repositorio
        created_entity = self._institution_repo.save(new_institution_entity)

        # 5. Devolver un DTO con la información del resultado
        return InstitutionDTO(
            id=created_entity.id,
            institute_name=created_entity.institute_name,
            physic_address=created_entity.physic_address,
            representative_email=user_entity.email # Obtenemos el email de la entidad de usuario
        )