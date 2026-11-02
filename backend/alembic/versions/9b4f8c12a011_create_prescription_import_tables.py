"""create prescription import tables

Revision ID: 9b4f8c12a011
Revises: 7cece35e08e9
Create Date: 2026-11-02 14:03:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b4f8c12a011'
down_revision: Union[str, Sequence[str], None] = '7cece35e08e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'import_sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('family_id', sa.Integer(), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.Column('source_type', sa.String(length=30), nullable=False),
        sa.Column('source_filename', sa.String(length=255), nullable=False),
        sa.Column('source_hash', sa.String(length=64), nullable=False),
        sa.Column('storage_path', sa.String(length=500), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('import_mode', sa.String(length=50), nullable=False),
        sa.Column('overall_confidence', sa.Float(), nullable=True),
        sa.Column('parser_version', sa.String(length=30), nullable=False),
        sa.Column('raw_payload', sa.JSON(), nullable=True),
        sa.Column('normalized_payload', sa.JSON(), nullable=True),
        sa.Column('review_payload', sa.JSON(), nullable=True),
        sa.Column('commit_summary', sa.JSON(), nullable=True),
        sa.Column('target_prescription_id', sa.Integer(), nullable=True),
        sa.Column('is_duplicate', sa.Boolean(), nullable=False),
        sa.Column('duplicate_of_import_id', sa.Integer(), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.Column('reviewed_by_user_id', sa.Integer(), nullable=True),
        sa.Column('committed_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('committed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['committed_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['duplicate_of_import_id'], ['import_sessions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['family_id'], ['families.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['member_id'], ['family_members.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['target_prescription_id'], ['prescriptions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_import_sessions_family_id'), 'import_sessions', ['family_id'], unique=False)
    op.create_index(op.f('ix_import_sessions_member_id'), 'import_sessions', ['member_id'], unique=False)
    op.create_index(op.f('ix_import_sessions_source_hash'), 'import_sessions', ['source_hash'], unique=False)
    op.create_index(op.f('ix_import_sessions_status'), 'import_sessions', ['status'], unique=False)

    op.create_table(
        'import_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('import_session_id', sa.Integer(), nullable=False),
        sa.Column('row_index', sa.Integer(), nullable=False),
        sa.Column('item_type', sa.String(length=40), nullable=False),
        sa.Column('raw_data', sa.JSON(), nullable=True),
        sa.Column('normalized_data', sa.JSON(), nullable=True),
        sa.Column('edited_data', sa.JSON(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('resolution_status', sa.String(length=30), nullable=False),
        sa.Column('matched_entity_type', sa.String(length=50), nullable=True),
        sa.Column('matched_entity_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['import_session_id'], ['import_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_import_items_import_session_id'), 'import_items', ['import_session_id'], unique=False)

    op.create_table(
        'import_validation_issues',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('import_session_id', sa.Integer(), nullable=False),
        sa.Column('import_item_id', sa.Integer(), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('code', sa.String(length=60), nullable=False),
        sa.Column('field_path', sa.String(length=150), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('suggested_fix', sa.Text(), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), nullable=False),
        sa.Column('resolved_by_user_id', sa.Integer(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['import_item_id'], ['import_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['import_session_id'], ['import_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resolved_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_import_validation_issues_code'), 'import_validation_issues', ['code'], unique=False)
    op.create_index(op.f('ix_import_validation_issues_import_item_id'), 'import_validation_issues', ['import_item_id'], unique=False)
    op.create_index(op.f('ix_import_validation_issues_import_session_id'), 'import_validation_issues', ['import_session_id'], unique=False)
    op.create_index(op.f('ix_import_validation_issues_severity'), 'import_validation_issues', ['severity'], unique=False)

    op.create_table(
        'import_entity_links',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('import_session_id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=20), nullable=False),
        sa.Column('previous_snapshot', sa.JSON(), nullable=True),
        sa.Column('new_snapshot', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['import_session_id'], ['import_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_import_entity_links_entity_id'), 'import_entity_links', ['entity_id'], unique=False)
    op.create_index(op.f('ix_import_entity_links_entity_type'), 'import_entity_links', ['entity_type'], unique=False)
    op.create_index(op.f('ix_import_entity_links_import_session_id'), 'import_entity_links', ['import_session_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_import_entity_links_import_session_id'), table_name='import_entity_links')
    op.drop_index(op.f('ix_import_entity_links_entity_type'), table_name='import_entity_links')
    op.drop_index(op.f('ix_import_entity_links_entity_id'), table_name='import_entity_links')
    op.drop_table('import_entity_links')

    op.drop_index(op.f('ix_import_validation_issues_severity'), table_name='import_validation_issues')
    op.drop_index(op.f('ix_import_validation_issues_import_session_id'), table_name='import_validation_issues')
    op.drop_index(op.f('ix_import_validation_issues_import_item_id'), table_name='import_validation_issues')
    op.drop_index(op.f('ix_import_validation_issues_code'), table_name='import_validation_issues')
    op.drop_table('import_validation_issues')

    op.drop_index(op.f('ix_import_items_import_session_id'), table_name='import_items')
    op.drop_table('import_items')

    op.drop_index(op.f('ix_import_sessions_status'), table_name='import_sessions')
    op.drop_index(op.f('ix_import_sessions_source_hash'), table_name='import_sessions')
    op.drop_index(op.f('ix_import_sessions_member_id'), table_name='import_sessions')
    op.drop_index(op.f('ix_import_sessions_family_id'), table_name='import_sessions')
    op.drop_table('import_sessions')

