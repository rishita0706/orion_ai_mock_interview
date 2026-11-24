"""initial tables

Revision ID: 001
Revises: 
Create Date: 2026-04-10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('institution', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_id', 'users', ['id'])

    op.create_table(
        'sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed', sa.Boolean(), nullable=True),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('content_score', sa.Float(), nullable=True),
        sa.Column('fluency_score', sa.Float(), nullable=True),
        sa.Column('nonverbal_score', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_sessions_id', 'sessions', ['id'])

    op.create_table(
        'session_answers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('video_path', sa.String(), nullable=True),
        sa.Column('audio_path', sa.String(), nullable=True),
        sa.Column('transcript', sa.Text(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('content_score', sa.Float(), nullable=True),
        sa.Column('fluency_score', sa.Float(), nullable=True),
        sa.Column('nonverbal_score', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_session_answers_id', 'session_answers', ['id'])

    op.create_table(
        'analysis_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('speech_metrics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('nonverbal_metrics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('content_metrics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('delta_overall', sa.Float(), nullable=True),
        sa.Column('delta_content', sa.Float(), nullable=True),
        sa.Column('delta_fluency', sa.Float(), nullable=True),
        sa.Column('delta_nonverbal', sa.Float(), nullable=True),
        sa.Column('ai_feedback', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id'),
    )
    op.create_index('ix_analysis_results_id', 'analysis_results', ['id'])


def downgrade():
    op.drop_table('analysis_results')
    op.drop_table('session_answers')
    op.drop_table('sessions')
    op.drop_table('users')
