from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.v1 import deps
from app.core.database import get_session
from app.models.organization import Organization
from app.models.user import User
from app.schemas.organization import OrganizationCreate, OrganizationRead, OrganizationUpdate

router = APIRouter()

@router.post("/", response_model=OrganizationRead)
async def create_organization(
    *,
    session: AsyncSession = Depends(get_session),
    organization_in: OrganizationCreate,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Cria uma nova organização (Tenancy).
    Apenas Superusuários podem executar esta ação.
    """
    # Verifica unicidade do slug
    query = select(Organization).where(Organization.slug == organization_in.slug)
    result = await session.exec(query)
    if result.first():
        raise HTTPException(status_code=400, detail="O slug da organização já existe.")

    # Verifica unicidade do nome
    query_name = select(Organization).where(Organization.name == organization_in.name)
    result_name = await session.exec(query_name)
    if result_name.first():
        raise HTTPException(status_code=400, detail="O nome da organização já está em uso.")

    org = Organization.from_orm(organization_in)
    session.add(org)
    await session.commit()
    await session.refresh(org)
    return org

@router.get("/", response_model=List[OrganizationRead])
async def read_organizations(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Lista todas as organizações.
    """
    query = select(Organization).offset(skip).limit(limit)
    result = await session.exec(query)
    return result.all()

@router.get("/{organization_id}", response_model=OrganizationRead)
async def read_organization(
    organization_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Obtém detalhes de uma organização específica.
    """
    org = await session.get(Organization, organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organização não encontrada")
    return org

@router.put("/{organization_id}", response_model=OrganizationRead)
async def update_organization(
    *,
    session: AsyncSession = Depends(get_session),
    organization_id: int,
    organization_in: OrganizationUpdate,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Atualiza dados da organização.
    """
    org = await session.get(Organization, organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organização não encontrada")

    update_data = organization_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(org, key, value)

    session.add(org)
    await session.commit()
    await session.refresh(org)
    return org

@router.delete("/{organization_id}")
async def delete_organization(
    *,
    session: AsyncSession = Depends(get_session),
    organization_id: int,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Remove uma organização.
    Cuidado: Isso pode deixar usuários e dispositivos órfãos se não houver CASCADE no banco.
    """
    org = await session.get(Organization, organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organização não encontrada")
    
    await session.delete(org)
    await session.commit()
    return {"ok": True}