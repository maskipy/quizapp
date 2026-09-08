"""
We only ever store the output of hash_password(). Raw passwords never
touch the database.
"""

from pwdlib import PasswordHash

# this returns a PasswordHash object that can be used to hash and verify passwords.
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)
