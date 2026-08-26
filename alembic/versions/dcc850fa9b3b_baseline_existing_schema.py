"""Baseline existing database schema.

Revision ID: dcc850fa9b3b
Revises:
Create Date: 2026-08-26
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "dcc850fa9b3b"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = None

branch_labels: Union[
    str,
    Sequence[str],
    None,
] = None

depends_on: Union[
    str,
    Sequence[str],
    None,
] = None


def upgrade() -> None:
    # Existing database already contains the schema.
    # This revision only restores Alembic history.
    pass


def downgrade() -> None:
    pass