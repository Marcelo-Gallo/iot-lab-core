from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.organization import Organization

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str

    username: str = Field(unique=True, index=True)
    email: Optional[str] = None
    full_name: Optional[str] = None
    
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)

    organization_id: Optional[int] = Field(default=None, foreign_key="organization.id")
    organization: Optional["Organization"] = Relationship(back_populates="users")