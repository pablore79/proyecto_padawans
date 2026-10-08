from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    rol: str = Field(..., pattern="^(admin|docente|alumno)$")
    alumno_id: int | None = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)


class UserRead(UserBase):
    id: int
    activo: bool
    created_at: datetime
    updated_at: datetime
    created_by: int | None = None

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    sub: str
    user_id: int
    username: str
    rol: str
    alumno_id: int | None = None
