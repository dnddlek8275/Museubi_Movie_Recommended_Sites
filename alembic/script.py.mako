"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: str | None = ${repr(down_revision)}
branch_labels: str | Sequence[str] | None = ${repr(branch_labels)}
depends_on: str | Sequence[str] | None = ${repr(depends_on)}


def upgrade() -> None:
    # 새 마이그레이션 적용 시 실행할 변경 사항을 작성한다.
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    # 새 마이그레이션을 되돌릴 때 실행할 변경 사항을 작성한다.
    ${downgrades if downgrades else "pass"}
