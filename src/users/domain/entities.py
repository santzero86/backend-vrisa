from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Password:
    hashed_value: str

@dataclass
class User:
    user_id: int
    first_name: str
    last_name: str
    email: str
    password: Password
    register_date: Optional[str] = None
    user_type_id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@dataclass
class Role:
    id: int
    name: str
