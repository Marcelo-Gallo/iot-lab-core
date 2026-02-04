from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.v1 import deps
from app.core.database import get_session
from app.core.security import get_password_hash
from app.models.organization import Organization
from app.models.user import User
from app.schemas.onboarding import OnboardingBase
from app.schemas.organization import OrganizationRead

router = APIRouter()

@router.post("/", response_model=OrganizationRead)
async def onboard_new_tenant(
    payload: OnboardingBase,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(deps.get_current_active_superuser), # Segurança Hierárquica
):
    """
    Setup Inicial de Tenant (Laboratório).
    Cria Organização + Admin em uma transação atômica.
    Restrito a Superusuários.
    """
    # 1. Validação de Unicidade (Org)
    q_org = select(Organization).where(Organization.slug == payload.org_slug)
    if (await session.exec(q_org)).first():
        raise HTTPException(status_code=400, detail="Slug da organização já existe.")

    # 2. Validação de Unicidade (User)
    q_user = select(User).where(User.username == payload.admin_email)
    if (await session.exec(q_user)).first():
        raise HTTPException(status_code=400, detail="Email do administrador já está em uso.")

    try:
        # 3. Criação da Organização
        new_org = Organization(
            name=payload.org_name,
            slug=payload.org_slug,
            description=payload.org_description
        )
        session.add(new_org)
        await session.flush() # Gera o ID da Org sem commitar ainda
        await session.refresh(new_org)

        # 4. Criação do Usuário Admin vinculado
        new_admin = User(
            username=payload.admin_email,
            email=payload.admin_email,
            full_name=payload.admin_name,
            hashed_password=get_password_hash(payload.admin_password),
            organization_id=new_org.id, # VÍNCULO FORTE
            is_active=True,
            is_superuser=False # Admin de Org não é Superuser
        )
        session.add(new_admin)

        # 5. Commit Atômico (Tudo ou Nada)
        await session.commit()
        await session.refresh(new_org)
        
        return new_org

    except Exception as e:
        await session.rollback()
        print(f"Erro no Onboarding: {e}")
        raise HTTPException(status_code=500, detail="Falha interna ao criar tenant.")