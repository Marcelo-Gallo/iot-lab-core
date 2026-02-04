from typing import Generator, Annotated
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from sqlalchemy.orm import selectinload

from app.core import security
from app.core.config import settings
from app.core.database import get_session
from app.models.user import User
from app.schemas.token import TokenPayload
from app.models.device_token import DeviceToken
from app.models.device import Device

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)

async def get_current_device(
    x_device_token: str = Header(..., alias="X-Device-Token"),
    session: AsyncSession = Depends(get_session)
) -> Device:
    """
    Valida o Token do Header e retorna o Dispositivo correspondente.
    Se falhar, retorna 401.
    """
    query = select(DeviceToken).where(DeviceToken.token == x_device_token)
    result = await session.exec(query)
    db_token = result.first()

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de dispositivo inválido.",
        )

    query_device = (
        select(Device)
        .where(Device.id == db_token.device_id)
        .options(selectinload(Device.sensors))
    )
    result_device = await session.exec(query_device)
    device = result_device.first()

    if not device or not device.is_active:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dispositivo inativo ou não encontrado.",
        )

    return device

async def get_current_user(
    session: AsyncSession = Depends(get_session),
    token: str = Depends(reusable_oauth2)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Não foi possível validar as credenciais",
        )
    
    # Busca o usuário no banco
    result = await session.exec(select(User).where(User.id == int(token_data.sub)))
    user = result.first()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Usuário inativo")
        
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Retorna o usuário atual se ele estiver ativo.
    (Redundante com get_current_user, mas mantém consistência de nomenclatura)
    """
    return current_user

async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=400, detail="O usuário não tem privilégios suficientes"
        )
    return current_user