"""mlops_monitoring_schema

Revision ID: 9e81bf3a56d1
Revises: 2d43ca5b45e2
Create Date: 2026-10-06 23:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e81bf3a56d1'
down_revision: Union[str, Sequence[str], None] = '2d43ca5b45e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to model_versions for MLOps registry
    op.add_column('model_versions', sa.Column('status', sa.String(length=32), nullable=False, server_default='candidate'))
    op.add_column('model_versions', sa.Column('git_commit', sa.String(length=64), nullable=True))
    op.add_column('model_versions', sa.Column('artifact_path', sa.String(length=256), nullable=True))
    op.add_column('model_versions', sa.Column('checksum', sa.String(length=64), nullable=True))
    op.add_column('model_versions', sa.Column('feature_schema', sa.JSON(), nullable=True))
    op.add_column('model_versions', sa.Column('promoted_at', sa.DateTime(), nullable=True))
    op.add_column('model_versions', sa.Column('promoted_by', sa.String(length=64), nullable=True))
    op.create_index(op.f('ix_model_versions_status'), 'model_versions', ['status'], unique=False)

    # 1. Prediction outcomes table
    op.create_table(
        'prediction_outcomes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('load_id', sa.String(length=128), nullable=False),
        sa.Column('actual_posted_rate', sa.Float(), nullable=False),
        sa.Column('recorded_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prediction_outcomes_load_id'), 'prediction_outcomes', ['load_id'], unique=True)
    op.create_index(op.f('ix_prediction_outcomes_recorded_at'), 'prediction_outcomes', ['recorded_at'], unique=False)

    # 2. Data quality metrics table
    op.create_table(
        'data_quality_metrics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('run_id', sa.String(length=64), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('feature_name', sa.String(length=64), nullable=False),
        sa.Column('total_records', sa.Integer(), nullable=False),
        sa.Column('missing_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('missing_pct', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('invalid_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('invalid_pct', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='NORMAL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_quality_metrics_run_id'), 'data_quality_metrics', ['run_id'], unique=False)
    op.create_index(op.f('ix_data_quality_metrics_timestamp'), 'data_quality_metrics', ['timestamp'], unique=False)

    # 3. Drift metrics table
    op.create_table(
        'drift_metrics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('run_id', sa.String(length=64), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('feature_name', sa.String(length=64), nullable=False),
        sa.Column('metric_type', sa.String(length=32), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('threshold_warning', sa.Float(), nullable=False, server_default='0.1'),
        sa.Column('threshold_critical', sa.Float(), nullable=False, server_default='0.25'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='NORMAL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_drift_metrics_run_id'), 'drift_metrics', ['run_id'], unique=False)
    op.create_index(op.f('ix_drift_metrics_timestamp'), 'drift_metrics', ['timestamp'], unique=False)

    # 4. Model performance table
    op.create_table(
        'model_performance',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('run_id', sa.String(length=64), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('model_version', sa.String(length=64), nullable=False),
        sa.Column('sample_size', sa.Integer(), nullable=False),
        sa.Column('rmse', sa.Float(), nullable=False),
        sa.Column('mae', sa.Float(), nullable=False),
        sa.Column('mape', sa.Float(), nullable=False),
        sa.Column('r2', sa.Float(), nullable=False),
        sa.Column('residual_mean', sa.Float(), nullable=True),
        sa.Column('residual_std', sa.Float(), nullable=True),
        sa.Column('segment_name', sa.String(length=64), nullable=False, server_default='all'),
        sa.Column('segment_value', sa.String(length=64), nullable=False, server_default='all'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_model_performance_run_id'), 'model_performance', ['run_id'], unique=False)
    op.create_index(op.f('ix_model_performance_timestamp'), 'model_performance', ['timestamp'], unique=False)
    op.create_index(op.f('ix_model_performance_model_version'), 'model_performance', ['model_version'], unique=False)

    # 5. Monitoring runs table
    op.create_table(
        'monitoring_runs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('run_id', sa.String(length=64), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('prediction_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('data_quality_status', sa.String(length=32), nullable=False, server_default='NORMAL'),
        sa.Column('drift_status', sa.String(length=32), nullable=False, server_default='NORMAL'),
        sa.Column('performance_status', sa.String(length=32), nullable=False, server_default='NORMAL'),
        sa.Column('alert_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_monitoring_runs_run_id'), 'monitoring_runs', ['run_id'], unique=True)
    op.create_index(op.f('ix_monitoring_runs_timestamp'), 'monitoring_runs', ['timestamp'], unique=False)

    # 6. Model audit events table
    op.create_table(
        'model_audit_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('model_version', sa.String(length=64), nullable=False),
        sa.Column('event_type', sa.String(length=32), nullable=False),
        sa.Column('actor', sa.String(length=64), nullable=False, server_default='system'),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_model_audit_events_timestamp'), 'model_audit_events', ['timestamp'], unique=False)
    op.create_index(op.f('ix_model_audit_events_model_version'), 'model_audit_events', ['model_version'], unique=False)


def downgrade() -> None:
    op.drop_table('model_audit_events')
    op.drop_table('monitoring_runs')
    op.drop_table('model_performance')
    op.drop_table('drift_metrics')
    op.drop_table('data_quality_metrics')
    op.drop_table('prediction_outcomes')
    op.drop_index(op.f('ix_model_versions_status'), table_name='model_versions')
    op.drop_column('model_versions', 'promoted_by')
    op.drop_column('model_versions', 'promoted_at')
    op.drop_column('model_versions', 'feature_schema')
    op.drop_column('model_versions', 'checksum')
    op.drop_column('model_versions', 'artifact_path')
    op.drop_column('model_versions', 'git_commit')
    op.drop_column('model_versions', 'status')
