"""
Security utilities: password hashing (pwdlib/Argon2) and JWT access tokens (PyJWT).

We only ever store the output of hash_password(). Raw passwords never touch the database.
"""

import asyncio
import threading
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

password_hash = PasswordHash.recommended()

# Argon2 is deliberately expensive: roughly 64 MiB of memory plus real CPU time per hash.
# Calling it directly inside an `async def` endpoint freezes the whole event loop -- no
# other request is served until it finishes -- so the *_async wrappers below run it in a
# worker thread. The semaphore caps how many hashes run at once: a burst of 180 logins
# queues up instead of allocating 64 MiB x 180 at the same moment.
MAX_CONCURRENT_HASHES = 4
_hash_slots = threading.BoundedSemaphore(MAX_CONCURRENT_HASHES)


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def _run_limited(func: Callable[..., Any], *args: Any) -> Any:
    with _hash_slots:
        return func(*args)


async def hash_password_async(password: str) -> str:
    """Use this from endpoints; hash_password() is the blocking version."""
    return await asyncio.to_thread(_run_limited, hash_password, password)


async def verify_password_async(plain_password: str, hashed_password: str) -> bool:
    """Use this from endpoints; verify_password() is the blocking version."""
    return await asyncio.to_thread(_run_limited, verify_password, plain_password, hashed_password)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT. `subject` is the user's id -- whatever get_current_user
    will later use to look the user back up."""
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> str | None:
    """Return the token's subject if valid and not expired, else None."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except jwt.PyJWTError:
        return None
    return payload.get("sub")
