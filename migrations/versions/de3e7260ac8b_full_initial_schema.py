"""Full initial schema

Revision ID: de3e7260ac8b
Revises: 
Create Date: 2026-01-29 02:03:51.235574

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = 'de3e7260ac8b'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### Tabela de USUÁRIOS ###
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('full_name', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('hashed_password', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('is_superuser', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # ### Tabela de TIPOS DE SENSOR ###
    op.create_table('sensor_types',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('unit', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sensor_types_name'), 'sensor_types', ['name'], unique=True)

    # ### Tabela de DISPOSITIVOS (COMPLETA) ###
    op.create_table('devices',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('slug', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('location', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    
    # --- Campos de Negócio Mantidos ---
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('is_battery_powered', sa.Boolean(), nullable=False, server_default='false'),
    
    # --- Campos de Controle do Sistema ---
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('heartbeat_interval', sa.Integer(), nullable=False, server_default='300'),
    sa.Column('deleted_at', sa.DateTime(), nullable=True),
    sa.Column('last_seen', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_devices_name'), 'devices', ['name'], unique=False)
    op.create_index(op.f('ix_devices_slug'), 'devices', ['slug'], unique=True)

    # ### Tabelas de RELACIONAMENTO e FILHOS ###
    op.create_table('device_sensor_links',
    sa.Column('device_id', sa.Integer(), nullable=False),
    sa.Column('sensor_type_id', sa.Integer(), nullable=False),
    sa.Column('calibration_formula', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
    sa.ForeignKeyConstraint(['sensor_type_id'], ['sensor_types.id'], ),
    sa.PrimaryKeyConstraint('device_id', 'sensor_type_id')
    )
    
    op.create_table('device_tokens',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('device_id', sa.Integer(), nullable=False),
    sa.Column('token', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('label', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('last_used_at', sa.DateTime(), nullable=True),
    sa.Column('is_rotating', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_device_tokens_device_id'), 'device_tokens', ['device_id'], unique=False)
    op.create_index(op.f('ix_device_tokens_token'), 'device_tokens', ['token'], unique=True)

    op.create_table('measurements',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('device_id', sa.Integer(), nullable=False),
    sa.Column('sensor_type_id', sa.Integer(), nullable=False),
    sa.Column('value', sa.Float(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
    sa.ForeignKeyConstraint(['sensor_type_id'], ['sensor_types.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('measurements')
    op.drop_index(op.f('ix_device_tokens_token'), table_name='device_tokens')
    op.drop_index(op.f('ix_device_tokens_device_id'), table_name='device_tokens')
    op.drop_table('device_tokens')
    op.drop_table('device_sensor_links')
    op.drop_index(op.f('ix_devices_slug'), table_name='devices')
    op.drop_index(op.f('ix_devices_name'), table_name='devices')
    op.drop_table('devices')
    op.drop_index(op.f('ix_sensor_types_name'), table_name='sensor_types')
    op.drop_table('sensor_types')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_table('users')