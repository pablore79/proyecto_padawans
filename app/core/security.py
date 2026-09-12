from datetime import UTC, datetime, timedelta

from jose import jwt  # type: ignore[import-untyped]
from passlib.context import CryptContext  # type: ignore[import-untyped]
from pydantic import BaseModel

from app.core.config import settings

# Usar pbkdf2_sha256 para evitar el bug de bcrypt en passlib (detect_wrap_bug)
# y el límite de 72 bytes de bcrypt
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
    pbkdf2_sha256__default_rounds=29000,
)


class TokenData(BaseModel):
    sub: str
    user_id: int
    username: str
    rol: str
    alumno_id: int | None = None
    exp: datetime


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bool(pwd_context.verify(plain_password, hashed_password))


def get_password_hash(password: str) -> str:
    return str(pwd_context.hash(password))


def create_access_token(
    data: dict[str, str | int | datetime | None],
    expires_delta: timedelta | None = None,
) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return str(encoded_jwt)


def decode_access_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return TokenData(**payload)
    except jwt.ExpiredSignatureError as err:
        raise ValueError("Token expirado") from err
    except jwt.JWTError as err:
        raise ValueError("Token inválido") from err


def create_token_data(
    user_id: int,
    username: str,
    rol: str,
    alumno_id: int | None = None,
) -> dict[str, str | int | datetime | None]:
    return {
        "sub": str(user_id),
        "user_id": user_id,
        "username": username,
        "rol": rol,
        "alumno_id": alumno_id,
    }
