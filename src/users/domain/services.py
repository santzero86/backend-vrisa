from .entities import User, Password

class UserService:
    def register_user(self, first_name: str, last_name: str, email: str, password_plain: str) -> User:
        # TODO: Implement password hashing with salt
        hashed_password: str = self.hash_password(password_plain)
        password: Password = Password(hashed_value=hashed_password)
        user = User(user_id=0, first_name=first_name, last_name=last_name, email=email, password=password) # User ID will be assigned by the repository
        return user

    def hash_password(self, password_plain: str) -> str:
        # In real implementation use bcrypt or similar
        return "hashed_" + password_plain # Placeholder