from dataclasses import dataclass
from typing import Optional

# DTO para recibir los datos para crear una institución
@dataclass(frozen=True)
class CreateInstitutionDTO:
    institute_name: str
    physic_address: str
    representative_id: int # El ID del usuario que será el representante

# DTO para devolver los datos de la institución creada
@dataclass(frozen=True)
class InstitutionDTO:
    id: int
    institute_name: str
    physic_address: str
    representative_email: Optional[str]