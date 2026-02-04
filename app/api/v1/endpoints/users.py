from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.v1 import deps
from app.core.database import get_session
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter()

@router.post("/", response_model=UserRead)
async def create_user(
    *,
    session: AsyncSession = Depends(get_session),
    user_in: UserCreate,
    current_user: User = Depends(deps.get_current_active_user), # Admin ou Superuser
) -> Any:
    """
    Cria novos usuários.
    - Superuser: Pode criar admins para qualquer organização.
    - Admin: Só pode criar usuários (alunos) na PRÓPRIA organização.
    """
    # 1. Regra de Tenant: Admin não pode criar usuário pra outra org ou sem org
    if not current_user.is_superuser:
        if user_in.organization_id and user_in.organization_id != current_user.organization_id:
             raise HTTPException(status_code=403, detail="Você não pode adicionar usuários em outra organização.")
        
        # Força o ID da organização do criador
        user_in.organization_id = current_user.organization_id
        # Admin comum não cria Superuser
        user_in.is_superuser = False

    # 2. Verifica duplicidade de Username
    query = select(User).where(User.username == user_in.username)
    result = await session.exec(query)
    if result.first():
        raise HTTPException(
            status_code=400,
            detail="O usuário com este username já existe no sistema.",
        )

    # 3. Criação
    user = User.from_orm(user_in)
    user.hashed_password = get_password_hash(user_in.password) # Hash seguro
    
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

@router.get("/", response_model=List[UserRead])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Lista usuários.
    - Superuser: Vê tudo.
    - Admin: Vê apenas usuários da sua organização.
    """
    query = select(User)
    
    # FILTRO DE ISOLAMENTO VERTICAL
    if not current_user.is_superuser:
        query = query.where(User.organization_id == current_user.organization_id)
        
    query = query.offset(skip).limit(limit)
    result = await session.exec(query)
    return result.all()

@router.get("/{user_id}", response_model=UserRead)
async def read_user_by_id(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # SEGURANÇA: Se não for superuser, só pode ver gente da própria org
    if not current_user.is_superuser and user.organization_id != current_user.organization_id:
         raise HTTPException(status_code=404, detail="Usuário não encontrado") # 404 para não vazar existência

    return user