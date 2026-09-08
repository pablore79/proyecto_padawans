from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.core.database import get_db
from app.models.usuario import Usuario
from app.schemas.auth import LoginRequest, Token, UserCreate, UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=Token)
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    return await auth_service.login(credentials.username, credentials.password)


@router.get("/me", response_model=UserRead)
async def me(current_user: Usuario = Depends(get_current_user)):
    return UserRead.model_validate(current_user)


@router.post("/users", response_model=UserRead, status_code=201)
async def create_user(
    user_data: UserCreate,
    current_user: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    auth_service = AuthService(db)
    return await auth_service.register(user_data, current_user.id)
