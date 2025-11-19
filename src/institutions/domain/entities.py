from dataclasses import dataclass, field
from typing import Optional, List

@dataclass(frozen=True)
class UserInfo:
    id: int
    full_name: str

@dataclass
class EnvironmentalInstitution:
    id: Optional[int] # El ID puede ser None antes de guardarse en la BD
    institute_name: str
    physic_address: str
    representative: Optional[UserInfo] # Relacionado con un usuario
    logo_url: Optional[str] = None
    colors: List[str] = field(default_factory=list)

@dataclass
class IntegrationRequest:
    id: Optional[int]
    institution_id: int
    status: str # 'PENDING', 'APPROVED', etc.
    review_comments: Optional[str] = None
    reviewed_by: Optional[UserInfo] = None