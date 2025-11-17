# src/users/application/queries/get_user.py

from typing import Optional
from src.users.infrastructure.repositories import UserRepository
from src.users.application.dto import UserDTO, RoleDTO
from common.exceptions import NotFoundError

class GetUserQuery:
    def __init__(self: 'GetUserQuery', repository: UserRepository) -> None:
        self._repository: UserRepository = repository

    def execute(self: 'GetUserQuery', user_id: int) -> UserDTO:
        user_entity = self._repository.find_by_id(user_id)

        if not user_entity:
            raise NotFoundError(f"User with ID {user_id} not found.")

        # Map entity to DTO
        role_dto: Optional[RoleDTO] = None
        if user_entity.role:
            role_dto = RoleDTO(id=user_entity.role.id, name=user_entity.role.name)

        return UserDTO(
            id=user_entity.id,
            email=user_entity.email,
            first_name=user_entity.first_name,
            last_name=user_entity.last_name,
            is_active=user_entity.is_active,
            role=role_dto
        )
