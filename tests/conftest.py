"""
conftest.py is a special file: pytest loads it automatically, before any test file, and
what it sets up is shared by every test.

"""

import os

os.environ["SECRET_KEY"] = "test-only-secret-key-never-used-outside-the-test-suite"
os.environ["ENVIRONMENT"] = "testing"
