"""
Admin commands. There is no admin web UI on purpose: promoting someone to teacher is
rare, powerful, and should never be reachable from the public API.

    uv run python -m app.cli set-role ana@school.ma teacher
    uv run python -m app.cli set-role ana@school.ma student

The role is read from the database on every request (it isn't stored in the login
token), so a change takes effect immediately, with no re-login needed.
"""

import argparse
import asyncio
import sys
from typing import get_args

from sqlmodel import select

from app.db.session import async_session_factory, engine
from app.models import User
from app.models.user import UserRole


async def set_role(email: str, role: str) -> int:
    engine.sync_engine.echo = False  # keep the SQL log out of a command-line tool
    try:
        async with async_session_factory() as session:
            result = await session.exec(select(User).where(User.email == email.strip().lower()))
            user = result.first()
            if user is None:
                print(f"No account with email {email!r}.", file=sys.stderr)
                return 1
            previous = user.role
            user.role = role
            session.add(user)
            await session.commit()
            print(f"{user.email}: {previous} -> {role}")
            return 0
    finally:
        await engine.dispose()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli", description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    set_role_parser = commands.add_parser("set-role", help="make an account a teacher or student")
    set_role_parser.add_argument("email")
    set_role_parser.add_argument("role", choices=get_args(UserRole))
    args = parser.parse_args(argv)
    return asyncio.run(set_role(args.email, args.role))


if __name__ == "__main__":
    raise SystemExit(main())
