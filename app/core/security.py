from datetime import datetime, timedelta
from typing import Any, Union, Dict
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(subject: Union[str, Dict[str, Any]], expires_delta: timedelta = None) -> str:
    """
    Gera o JWT assinado.
    Agora suporta Dicionários para injetar claims extras (como organization_id).
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Base do payload
    to_encode = {"exp": expire}

    if isinstance(subject, dict):
        to_encode.update(subject)
    else:
        to_encode["sub"] = str(subject)
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)