from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.v1 import deps
from app.core.database import get_session
from app.core.security import create_access_token, verify_password
from app.core.config import settings
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserRead

router = APIRouter()

@router.post("/login/access-token", response_model=Token)
async def login_access_token(
    session: AsyncSession = Depends(get_session),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    Login via OAuth2. 
    INJETA: 'organization_id' no Token JWT para uso no WebSocket.
    """
    # 1. Busca Usuário
    # Nota: Em produção, ideal mover essa lógica para deps.authenticate(session, user, pass)
    query = select(User).where(User.email == form_data.username) # Atenção: Form usa 'username', nosso modelo usa 'email'
    result = await session.exec(query)
    user = result.first()

    # 2. Valida Senha
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Usuário inativo")

    # 3. Prepara Payload com ISOLAMENTO VERTICAL
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    token_payload = {
        "sub": str(user.id),                  # ID Padrão (Mantém compatibilidade com deps.py)
        "organization_id": user.organization_id # <--- O SEGREDO (Novo campo)
    }

    return {
        "access_token": create_access_token(
            subject=token_payload,            # Passamos o dict completo agora
            expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.get("/login/me", response_model=UserRead)
async def read_users_me(
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retorna o contexto do usuário atual.
    """
    return current_user