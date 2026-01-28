from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'jailbreak_sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('original_prompt', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'jailbreak_attempts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('attacker_model', sa.String(length=100), nullable=False),
        sa.Column('attacker_prompt', sa.Text(), nullable=False),
        sa.Column('target_model', sa.String(length=100), nullable=True),
        sa.Column('target_response', sa.Text(), nullable=True),
        sa.Column('user_rating', sa.Float(), nullable=True),
        sa.Column('rating_comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('rated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['jailbreak_sessions.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'model_stats',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('total_attempts', sa.Integer(), nullable=True),
        sa.Column('total_ratings', sa.Integer(), nullable=True),
        sa.Column('average_rating', sa.Float(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('model_name')
    )


def downgrade() -> None:
    op.drop_table('model_stats')
    op.drop_table('jailbreak_attempts')
    op.drop_table('jailbreak_sessions')
