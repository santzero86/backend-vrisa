from ..domain import entities
from . import models

def user_model_to_entity(user_model: models.User) -> entities.User:
    return entities.User(
        user_id=user_model.user_id,
        first_name=user_model.user_first_name,
        last_name=user_model.user_last_name,
        email=user_model.user_email,
        password=entities.Password(hashed_value=user_model.password_hash),
        register_date=str(user_model.register_date),
        user_type_id=user_model.user_type_id,
        created_at=str(user_model.created_at),
        updated_at=str(user_model.updated_at)
    )

def user_entity_to_model(user: entities.User) -> models.User:
    return models.User(
        user_id=user.user_id,
        user_first_name=user.first_name,
        user_last_name=user.last_name,
        user_email=user.email,
        password_hash=user.password.hashed_value,
        register_date=user.register_date,
        user_type_id=user.user_type_id,
        created_at=user.created_at,
        updated_at=user.updated_at
    )