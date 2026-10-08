#!/usr/bin/env python3
"""Bootstrap script para crear el primer administrador del sistema.

Uso:
    python -m scripts.create_admin
    python -m scripts.create_admin --username admin --email admin@bunker4.com
    python -m scripts.create_admin --database-url postgresql+psycopg://user:pass@localhost:5432/db

La contraseña se solicita interactivamente (oculta). No pasarla como argumento.
"""

import argparse
import asyncio
import getpass
import sys
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.usuario import RolUsuario, Usuario
from app.schemas.auth import UserCreate
from app.services.admin_bootstrap import AdminBootstrapError


def collect_user_data(username: str, email: str) -> UserCreate:
    """Collect and validate admin user data interactively.

    Args:
        username: Username (will be stripped)
        email: Email (will be stripped)

    Returns:
        UserCreate with validated data

    Raises:
        AdminBootstrapError: If password confirmation fails
        ValidationError: If data fails Pydantic validation
    """
    username = username.strip()
    email = email.strip()

    password = getpass.getpass("Contraseña: ")
    if not password:
        raise AdminBootstrapError("La contraseña es obligatoria")

    confirm = getpass.getpass("Confirmar contraseña: ")
    if password != confirm:
        raise AdminBootstrapError("Las contraseñas no coinciden")

    return UserCreate(
        username=username,
        email=email,
        password=password,
        rol=RolUsuario.ADMIN,
        alumno_id=None,
    )


async def create_admin(
    username: str | None = None,
    email: str | None = None,
    password: str | None = None,
    database_url: str | None = None,
) -> None:
    """Crea el primer usuario admin si no existe ninguno."""
    db_url = database_url or settings.DATABASE_URL
    engine = create_async_engine(db_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Verificar si ya existe algún admin
        existing_admin = await db.execute(select(Usuario).where(Usuario.rol == RolUsuario.ADMIN))
        existing_admin = existing_admin.scalar_one_or_none()

        if existing_admin:
            print(f"⚠️  Ya existe un administrador: {existing_admin.username} ({existing_admin.email})")
            print("   No se crea otro para evitar duplicados.")
            return

        # Solicitar datos faltantes interactivamente
        if not username:
            username = input("Username: ").strip()
            if not username:
                print("❌ Username es obligatorio")
                sys.exit(1)

        if not email:
            email = input("Email: ").strip()
            if not email:
                print("❌ Email es obligatorio")
                sys.exit(1)

        if not password:
            while True:
                password = getpass.getpass("Contraseña: ")
                if not password:
                    print("❌ Contraseña es obligatoria")
                    continue
                confirm = getpass.getpass("Confirmar contraseña: ")
                if password != confirm:
                    print("❌ Las contraseñas no coinciden")
                    continue
                break

        # Verificar colisiones de username/email (aunque no debería haber usuarios)
        collision = await db.execute(
            select(Usuario).where((Usuario.username == username) | (Usuario.email == email))
        )
        if collision.scalar_one_or_none():
            print("❌ Ya existe un usuario con ese username o email")
            sys.exit(1)

        # Crear el admin
        admin = Usuario(
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            rol=RolUsuario.ADMIN,
            alumno_id=None,  # admin no tiene alumno_id
            activo=True,
            created_by=None,  # bootstrap: no hay creador previo
            updated_by=None,
        )
        db.add(admin)
        await db.commit()
        await db.refresh(admin)

        print(f"✅ Administrador creado exitosamente:")
        print(f"   ID: {admin.id}")
        print(f"   Username: {admin.username}")
        print(f"   Email: {admin.email}")
        print(f"   Rol: {admin.rol.value}")

    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Crear primer administrador del sistema Bunker4 Alumnos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python -m scripts.create_admin
  python -m scripts.create_admin --username admin --email admin@bunker4.com
  python -m scripts.create_admin --database-url postgresql+psycopg://postgres:postgres@localhost:5432/bunker4_alumnos --username admin --email admin@bunker4.com
  python -m scripts.create_admin --username admin --email admin@bunker4.com --password 'secreto123'  # NO recomendado
        """,
    )
    parser.add_argument("--username", help="Username del administrador (se pide si no se da)")
    parser.add_argument("--email", help="Email del administrador (se pide si no se da)")
    parser.add_argument(
        "--password",
        help="Contraseña (NO recomendado por seguridad; mejor usar entrada interactiva oculta)",
    )
    parser.add_argument(
        "--database-url",
        help="URL de base de datos (default: la de settings/DATABASE_URL; usar localhost si no está en Docker)",
    )

    args = parser.parse_args()

    if args.password and not (args.username and args.email):
        print("❌ Si usa --password, debe proporcionar también --username y --email")
        sys.exit(1)

    asyncio.run(create_admin(args.username, args.email, args.password, args.database_url))


if __name__ == "__main__":
    main()