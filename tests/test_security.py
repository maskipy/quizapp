"""
security.py reads SECRET_KEY from the settings, so these tests need settings to exist.
tests/conftest.py provides test-only ones.
"""

from datetime import timedelta

import jwt
import pytest

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

# --- passwords ---------------------------------------------------------------


def test_a_password_verifies_against_its_own_hash():
    hashed = hash_password("correct-horse-battery-staple")
    assert verify_password("correct-horse-battery-staple", hashed)


def test_a_wrong_password_does_not_verify():
    hashed = hash_password("correct-horse-battery-staple")
    assert not verify_password("wrong-password", hashed)


def test_the_stored_hash_is_argon2id_and_never_the_password():
    hashed = hash_password("hunter2hunter2")
    assert hashed.startswith("$argon2id$")
    assert "hunter2" not in hashed


def test_the_same_password_hashes_differently_each_time():
    # Every hash gets a random salt, so two hashes of one password differ...
    first = hash_password("same-password")
    second = hash_password("same-password")
    assert first != second
    # ...and both still verify. We can't compare hashes directly; verify() is the judge.
    assert verify_password("same-password", first)
    assert verify_password("same-password", second)


# --- tokens ------------------------------------------------------------------


def test_a_token_gives_back_the_subject_it_was_created_with():
    token = create_access_token("42")
    assert decode_access_token(token) == "42"


def test_an_expired_token_is_rejected():
    token = create_access_token("42", expires_delta=timedelta(seconds=-1))  # expired 1s ago
    assert decode_access_token(token) is None


@pytest.mark.parametrize(
    "bad_token",
    [
        pytest.param("not.a.jwt", id="garbage"),
        pytest.param("", id="empty"),
        pytest.param(
            jwt.encode({"sub": "42"}, "some-other-secret-of-sufficient-length!!", "HS256"),
            id="wrong-secret",
        ),
        pytest.param(
            jwt.encode({"foo": "bar"}, settings.secret_key, algorithm=settings.algorithm),
            id="no-subject",
        ),
    ],
)
def test_bad_tokens_are_rejected(bad_token):
    # One test body, four inputs: pytest runs it once per pytest.param and names each run.
    assert decode_access_token(bad_token) is None


# --- the settings themselves -------------------------------------------------


def test_tests_use_their_own_secret_not_the_developers():
    assert settings.secret_key == "test-only-secret-key-never-used-outside-the-test-suite"
