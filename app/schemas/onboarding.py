from pydantic import BaseModel, EmailStr
from typing import Optional

class OnboardingBase(BaseModel):
    # Dados da Organização
    org_name: str
    org_slug: str
    org_description: Optional[str] = None

    # Dados do Admin da Organização
    admin_email: EmailStr
    admin_password: str
    admin_name: str