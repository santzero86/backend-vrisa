from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class RoleDTO:
    id: int
    name: str

@dataclass(frozen=True)
class UserDTO:
    """
    Data Transfer Object for returning user information.
    This is the public representation of a user.
    """
    id: int
    email: str
    first_name: str
    last_name: str
    is_active: bool
    role: Optional[RoleDTO]

@dataclass(frozen=True)
class RegisterUserDTO:
    """
    Data Transfer Object for receiving user registration data.
    """
    email: str
    password: str
    first_name: str
    last_name: str
    role_id: Optional[int]