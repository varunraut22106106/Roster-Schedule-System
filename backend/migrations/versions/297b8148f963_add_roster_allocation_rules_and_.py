
"""add roster allocation rules and staffing time slots

Revision ID: 297b8148f963
Revises: 9aee1ba0e101
Create Date: 2026-11-24 11:40:00.947125

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '297b8148f963'
down_revision: Union[str, Sequence[str], None] = '9aee1ba0e101'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create roster allocation rules table
    op.create_table(
        'roster_allocation_rules',

        sa.Column(
            'allocation_rule_id',
            sa.Uuid(),
            nullable=False
        ),

        sa.Column(
            'roster_id',
            sa.Uuid(),
            nullable=False
        ),

        sa.Column(
            'employee_id',
            sa.Uuid(),
            nullable=False
        ),

        sa.Column(
            'roster_date',
            sa.Date(),
            nullable=False
        ),

        sa.Column(
            'process_id',
            sa.Uuid(),
            nullable=False
        ),

        sa.Column(
            'allocation_mode',
            sa.Enum('FIXED', 'FLEXIBLE', name='allocationmode'),
            nullable=False
        ),

        sa.Column(
            'fixed_minutes',
            sa.Integer(),
            nullable=True
        ),

        sa.Column(
            'minimum_minutes',
            sa.Integer(),
            nullable=True
        ),

        sa.Column(
            'maximum_minutes',
            sa.Integer(),
            nullable=True
        ),

        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False
        ),

        # Check constraints
        sa.CheckConstraint(
            'fixed_minutes IS NULL OR fixed_minutes > 0',
            name='ck_allocation_fixed_positive'
        ),

        sa.CheckConstraint(
            'minimum_minutes IS NULL OR minimum_minutes > 0',
            name='ck_allocation_minimum_positive'
        ),

        sa.CheckConstraint(
            'maximum_minutes IS NULL OR maximum_minutes > 0',
            name='ck_allocation_maximum_positive'
        ),

        sa.CheckConstraint(
            'minimum_minutes IS NULL OR maximum_minutes IS NULL '
            'OR minimum_minutes <= maximum_minutes',
            name='ck_allocation_min_max'
        ),

        sa.CheckConstraint(
            "(allocation_mode = 'FIXED' "
            "AND fixed_minutes IS NOT NULL "
            "AND minimum_minutes IS NULL "
            "AND maximum_minutes IS NULL) "
            "OR "
            "(allocation_mode = 'FLEXIBLE' "
            "AND fixed_minutes IS NULL "
            "AND minimum_minutes IS NOT NULL "
            "AND maximum_minutes IS NOT NULL)",
            name='ck_allocation_mode_values'
        ),

        # Foreign keys
        sa.ForeignKeyConstraint(
            ['roster_id'],
            ['rosters.roster_id'],
            ondelete='CASCADE'
        ),

        sa.ForeignKeyConstraint(
            ['employee_id'],
            ['employees.employee_id']
        ),

        sa.ForeignKeyConstraint(
            ['process_id'],
            ['processes.process_id']
        ),

        sa.PrimaryKeyConstraint('allocation_rule_id'),

        sa.UniqueConstraint(
            'roster_id',
            'employee_id',
            'roster_date',
            'process_id',
            name='uq_roster_employee_date_process_rule'
        )
    )

    # Allocation lookup index
    op.create_index(
        'ix_roster_allocation_employee_date',
        'roster_allocation_rules',
        ['employee_id', 'roster_date'],
        unique=False
    )

    # Add time-slot fields to staffing requirements
    op.add_column(
        'staffing_requirements',
        sa.Column('start_time', sa.Time(), nullable=True)
    )

    op.add_column(
        'staffing_requirements',
        sa.Column('end_time', sa.Time(), nullable=True)
    )

    # Ensure both time fields are supplied together
    op.create_check_constraint(
        'ck_staffing_time_slot_pair',
        'staffing_requirements',
        '(start_time IS NULL AND end_time IS NULL) OR '
        '(start_time IS NOT NULL AND end_time IS NOT NULL)'
    )

    # Ensure end time is later than start time
    op.create_check_constraint(
        'ck_staffing_time_slot_order',
        'staffing_requirements',
        'start_time IS NULL OR end_time > start_time'
    )


def downgrade() -> None:
    # Remove staffing constraints first
    op.drop_constraint(
        'ck_staffing_time_slot_order',
        'staffing_requirements',
        type_='check'
    )

    op.drop_constraint(
        'ck_staffing_time_slot_pair',
        'staffing_requirements',
        type_='check'
    )

    # Remove staffing time-slot columns
    op.drop_column(
        'staffing_requirements',
        'end_time'
    )

    op.drop_column(
        'staffing_requirements',
        'start_time'
    )

    # Remove allocation index
    op.drop_index(
        'ix_roster_allocation_employee_date',
        table_name='roster_allocation_rules'
    )

    # Remove allocation table
    op.drop_table('roster_allocation_rules')

    # Remove PostgreSQL enum type
    sa.Enum(
        'FIXED',
        'FLEXIBLE',
        name='allocationmode'
    ).drop(op.get_bind(), checkfirst=True)
