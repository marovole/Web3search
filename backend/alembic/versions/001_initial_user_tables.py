"""initial_user_tables

Revision ID: 001
Revises: 
Create Date: 2025-01-26 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建users表
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=True),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('email_verification_token', sa.String(length=64), nullable=True),
        sa.Column('password_reset_token', sa.String(length=64), nullable=True),
        sa.Column('password_reset_expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_email_active', 'users', ['email', 'is_active'])
    op.create_index('ix_users_created_at', 'users', ['created_at'])
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index(op.f('ix_users_username'), 'users', ['username'])

    # 创建user_preferences表
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('preferences', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_user_preferences_user_id'), 'user_preferences', ['user_id'])

    # 创建sessions表
    op.create_table(
        'sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('refresh_token_hash', sa.String(length=255), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('device_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sessions_user_id'), 'sessions', ['user_id'])
    op.create_index(op.f('ix_sessions_refresh_token_hash'), 'sessions', ['refresh_token_hash'], unique=True)
    op.create_index('ix_sessions_user_expires', 'sessions', ['user_id', 'expires_at'])
    op.create_index('ix_sessions_revoked_expires', 'sessions', ['is_revoked', 'expires_at'])
    op.create_index(op.f('ix_sessions_created_at'), 'sessions', ['created_at'])
    op.create_index(op.f('ix_sessions_last_used_at'), 'sessions', ['last_used_at'])

    # 更新conversations表，添加user_id外键（如果表已存在）
    try:
        op.add_column('conversations', sa.Column('user_id', sa.String(length=36), nullable=True))
        op.create_foreign_key(
            'fk_conversations_user_id',
            'conversations',
            'users',
            ['user_id'],
            ['id'],
            ondelete='CASCADE'
        )
        op.create_index(op.f('ix_conversations_user_id'), 'conversations', ['user_id'])
    except Exception:
        # 如果conversations表不存在或列已存在，忽略错误
        pass

    # 更新reports表，添加user_id外键（如果表已存在）
    try:
        op.add_column('reports', sa.Column('user_id', sa.String(length=36), nullable=True))
        op.create_foreign_key(
            'fk_reports_user_id',
            'reports',
            'users',
            ['user_id'],
            ['id'],
            ondelete='CASCADE'
        )
        op.create_index(op.f('ix_reports_user_id'), 'reports', ['user_id'])
    except Exception:
        # 如果reports表不存在或列已存在，忽略错误
        pass


def downgrade() -> None:
    # 删除reports表的user_id外键
    try:
        op.drop_index(op.f('ix_reports_user_id'), table_name='reports')
        op.drop_constraint('fk_reports_user_id', 'reports', type_='foreignkey')
        op.drop_column('reports', 'user_id')
    except Exception:
        pass

    # 删除conversations表的user_id外键
    try:
        op.drop_index(op.f('ix_conversations_user_id'), table_name='conversations')
        op.drop_constraint('fk_conversations_user_id', 'conversations', type_='foreignkey')
        op.drop_column('conversations', 'user_id')
    except Exception:
        pass

    # 删除sessions表
    op.drop_index(op.f('ix_sessions_last_used_at'), table_name='sessions')
    op.drop_index(op.f('ix_sessions_created_at'), table_name='sessions')
    op.drop_index('ix_sessions_revoked_expires', table_name='sessions')
    op.drop_index('ix_sessions_user_expires', table_name='sessions')
    op.drop_index(op.f('ix_sessions_refresh_token_hash'), table_name='sessions')
    op.drop_index(op.f('ix_sessions_user_id'), table_name='sessions')
    op.drop_table('sessions')

    # 删除user_preferences表
    op.drop_index(op.f('ix_user_preferences_user_id'), table_name='user_preferences')
    op.drop_table('user_preferences')

    # 删除users表
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index('ix_users_created_at', table_name='users')
    op.drop_index('ix_users_email_active', table_name='users')
    op.drop_index('ix_users_id', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')

