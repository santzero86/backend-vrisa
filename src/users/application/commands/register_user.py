from django.contrib.auth.hashers import make_password
from src.users.domain.entities import UserEntity, RoleEntity
from src.users.infrastructure.repositories import UserRepository
from src.users.application.dto import RegisterUserDTO, UserDTO, RoleDTO
from src.users.application.exceptions import UserAlreadyExistsError

class RegisterUserCommand:
    def __init__(self: 'RegisterUserCommand', repository: UserRepository) -> None:
        self._repository: UserRepository = repository

    def execute(self: 'RegisterUserCommand', user_dto: RegisterUserDTO) -> UserDTO:
        # Check if user already exists
        if self._repository.find_by_email(user_dto.email):
            raise UserAlreadyExistsError(f"User with email {user_dto.email} already exists.")

        # Create RoleEntity if role_id is provided
        role: Optional[RoleEntity] = None
        if user_dto.role_id:
            # In a real app, you would fetch the role name from a RoleRepository
            # For simplicity, we create a placeholder entity
            role = RoleEntity(id=user_dto.role_id, name="Assigned Role")

        # Create a domain entity from the DTO data
        # IMPORTANT: Password hashing happens here, just before saving.
        # This is an application-level concern.
        user_entity: UserEntity = UserEntity(
            id=None, # The database will generate the ID
            email=user_dto.email,
            first_name=user_dto.first_name,
            last_name=user_dto.last_name,
            password_hash=make_password(user_dto.password), # Hashing the password
            is_active=True, # New users are active by default
            role=role
        )

        # Persist using the repository
        created_user: UserEntity = self._repository.save(user_entity)

        # Return a DTO with the created user's data
        role_dto: Optional[RoleDTO] = None
        if created_user.role:
            role_dto = RoleDTO(id=created_user.role.id, name=created_user.role.name)
        
        return UserDTO(
            id=created_user.id,
            email=created_user.email,
            first_name=created_user.first_name,
            last_name=created_user.last_name,
            is_active=created_user.is_active,
            role=role_dto
        )
