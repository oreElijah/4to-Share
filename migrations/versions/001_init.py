"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2026-03-21 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('firstname', sa.String(), nullable=False),
        sa.Column('lastname', sa.String(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(), nullable=False),
        sa.Column('password', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=True)
    
    op.create_table('posts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('caption', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('file_type', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_posts_id'), 'posts', ['id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_posts_id'), table_name='posts')
    op.drop_table('posts')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
