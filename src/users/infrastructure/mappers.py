from ..domain.entities import User as UserEntity, Password
from .. import domain as entities
from src.users.models import User as UserModel

class UserMapper:
    """
    Translates between the User domain entity and the Django User model.
    """
    @staticmethod
    def user_model_to_entity(user_model: UserModel) -> UserEntity:
        """
        Converts a Django User model instance to a UserEntity domain object.
        """
        return UserEntity(
            user_id=user_model.id,
            first_name=user_model.first_name,
            last_name=user_model.last_name,
            email=user_model.email,
            password=Password(hashed_value=user_model.password),
            is_active=user_model.is_active,
            register_date=str(user_model.register_date),
            user_type_id=user_model.user_type.user_type_id if user_model.user_type else None
        )

    @staticmethod
    def user_entity_to_model(user_entity: UserEntity) -> UserModel:
        """
        Converts a UserEntity domain object to a Django User model instance.
        """
        return UserModel(
            id=user_entity.user_id,
            first_name=user_entity.first_name,
            last_name=user_entity.last_name,
            email=user_entity.email,
            password=user_entity.password.hashed_value,
            is_active=user_entity.is_active,
            register_date=user_entity.register_date,
            user_type_id=user_entity.user_type_id
        )