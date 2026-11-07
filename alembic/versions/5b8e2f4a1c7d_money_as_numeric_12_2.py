"""store transaction amount as numeric(12, 2), not null

Revision ID: 5b8e2f4a1c7d
Revises: 13dd973ac0cf
Create Date: 2026-11-07 10:15:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b8e2f4a1c7d'
down_revision: Union[str, Sequence[str], None] = '13dd973ac0cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Exactly 2 decimal places (cents/tiyn), up to 10 digits before the point.
    Existing values with more decimals are rounded by PostgreSQL."""
    op.alter_column(
        'transactions', 'amount',
        existing_type=sa.Numeric(),
        type_=sa.Numeric(12, 2),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        'transactions', 'amount',
        existing_type=sa.Numeric(12, 2),
        type_=sa.Numeric(),
        nullable=True,
    )
