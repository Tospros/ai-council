"""Initial migration - create prompts_history table

Revision ID: 001_initial
Revises: 
Create Date: 2026-01-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the schema if it doesn't exist
    op.execute('CREATE SCHEMA IF NOT EXISTS main')
    
    # Create the prompts_history table
    op.create_table(
        'prompts_history',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('response', sa.Text(), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('llm_name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='rating_range'),
        sa.PrimaryKeyConstraint('id'),
        schema='main'
    )
    
    # Create indexes for common queries
    op.create_index(
        'ix_prompts_history_llm_name',
        'prompts_history',
        ['llm_name'],
        schema='main'
    )
    op.create_index(
        'ix_prompts_history_created_at',
        'prompts_history',
        ['created_at'],
        schema='main'
    )


def downgrade() -> None:
    op.drop_index('ix_prompts_history_created_at', table_name='prompts_history', schema='main')
    op.drop_index('ix_prompts_history_llm_name', table_name='prompts_history', schema='main')
    op.drop_table('prompts_history', schema='main')
    op.execute('DROP SCHEMA IF EXISTS main CASCADE')
