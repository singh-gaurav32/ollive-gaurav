"""index logs.timestamp

Revision ID: 0003_index_logs_timestamp
Revises: 0002_logs_and_failed_log_events
Create Date: 2026-08-16

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0003_index_logs_timestamp"
down_revision: Union[str, None] = "0002_logs_and_failed_log_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_logs_timestamp", "logs", ["timestamp"])


def downgrade() -> None:
    op.drop_index("ix_logs_timestamp", table_name="logs")
