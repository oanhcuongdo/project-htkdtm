"""Merge the runtime schema and AI provider settings migration heads."""

from typing import Sequence, Union

revision: str = "e7f8a9b0c1d2"
down_revision: Union[str, Sequence[str], None] = ("c8d9e0f1a2b3", "1a2b3c4d5e6f")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
