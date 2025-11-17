from typing import Optional
from src.users.domain.entities import User as UserEntity
from src.users.models import User
from src.users.infrastructure.mappers import UserMapper

class UserRepository:
    def find_by_id(self: 'UserRepository', user_id: int) -> Optional[UserEntity]:
        """
        Finds a user by their ID and returns a domain entity, or None if not found.
        """
        try:
            user_model: User = User.objects.get(pk=user_id)
            return UserMapper.model_to_entity(user_model)
        except User.DoesNotExist:
            return None

    def find_by_email(self: 'UserRepository', email: str) -> Optional[UserEntity]:
        """
        Finds a user by their email and returns a domain entity, or None if not found.
        """
        try:
            user_model: User = User.objects.get(email=email)
            return UserMapper.model_to_entity(user_model)
        except User.DoesNotExist:
            return None

    def save(self: 'UserRepository', user_entity: UserEntity) -> UserEntity:
        """
        Saves a user entity to the database.
        This handles both creation of new users and updates to existing ones.
        Password must be handled separately before calling save.
        """
        user_model: User = UserMapper.entity_to_model(user_entity)
        
        # This will use the password already set on the model if it exists
        # For new users, the password should be set in the application service
        user_model.save()
        
        # We map it back to an entity to ensure the returned object is consistent
        # and includes any database-generated values (like the ID for a new user).
        return UserMapper.model_to_entity(user_model)
