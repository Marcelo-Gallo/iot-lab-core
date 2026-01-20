from sqlmodel import SQLModel, Field
from typing import Optional

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: Optional[str] = None
    full_name: Optional[str] = None
    
    hashed_password: str
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)