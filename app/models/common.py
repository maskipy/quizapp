"""
Building blocks shared by every model file.
"""

from datetime import UTC, datetime
from typing import Annotated

from pydantic import StringConstraints
from sqlalchemy import DateTime


def utcnow() -> datetime:
    return datetime.now(UTC)


TimestampColumn = DateTime(timezone=True)

# Input limits live on the *input* schemas (Create/Update), never on table fields:
# a max_length on a table field changes the column to VARCHAR(n) (so it needs a
# migration), and table models don't run validation anyway.
Name = Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)]
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Description = Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)]
CardText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
