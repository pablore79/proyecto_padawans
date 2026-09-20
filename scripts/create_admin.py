import argparse
import asyncio
import getpass
import sys

from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_db_context
from app.models.usuario import RolUsuario
from app.schemas.auth import UserCreate
from app.services.admin_bootstrap import (
    AdminBootstrapError,
    AdminBootstrapStatus,
    create_initial_admin,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Crea el administrador inicial de forma segura.",
    )
    parser.add_argument("--username", help="Username del administrador")
    parser.add_argument("--email", help="Email del administrador")
    return parser


def collect_user_data(username: str | None, email: str | None) -> UserCreate:
    resolved_username = username.strip() if username is not None else input("Username: ").strip()
    resolved_email = email.strip() if email is not None else input("Email: ").strip()
    password = getpass.getpass("Contraseña: ")
    confirmation = getpass.getpass("Confirmar contraseña: ")
    if password != confirmation:
        raise AdminBootstrapError("Las contraseñas no coinciden.")

    return UserCreate(
        username=resolved_username,
        email=resolved_email,
        password=password,
        rol=RolUsuario.ADMIN,
        alumno_id=None,
    )


async def run(user_data: UserCreate) -> AdminBootstrapStatus:
    async with get_db_context() as db:
        result = await create_initial_admin(db, user_data)
    return result.status


def main() -> int:
    args = build_parser().parse_args()
    try:
        user_data = collect_user_data(args.username, args.email)
        status = asyncio.run(run(user_data))
    except (AdminBootstrapError, ValidationError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1
    except SQLAlchemyError:
        sys.stderr.write("Error: falló la operación de base de datos; no se guardaron cambios.\n")
        return 1

    if status == AdminBootstrapStatus.ALREADY_EXISTS:
        sys.stdout.write("El administrador inicial ya existe; no se realizaron cambios.\n")
    else:
        sys.stdout.write("Administrador inicial creado correctamente.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
