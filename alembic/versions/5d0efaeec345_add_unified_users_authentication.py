"""migrate existing admins into users

Revision ID: 5d0efaeec345
Revises: 46bc5a9e1b04
Create Date: 2026-09-19
"""

from alembic import op


revision = "5d0efaeec345"
down_revision = "46bc5a9e1b04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Copy existing admin accounts into the unified users table.
    # They keep their existing password hashes.
    op.execute(
        """
        INSERT INTO users (
            full_name,
            email,
            phone,
            username,
            password_hash,
            role,
            is_active,
            created_at
        )
        SELECT
            username,
            username || '@janatha-library.local',
            NULL,
            username,
            password_hash,
            'admin',
            is_active,
            created_at
        FROM admins
        WHERE NOT EXISTS (
            SELECT 1
            FROM users
            WHERE users.username = admins.username
        )
        """
    )


def downgrade() -> None:
    # Remove only the admin users that were migrated from admins.
    op.execute(
        """
        DELETE FROM users
        WHERE role = 'admin'
          AND email LIKE '%@janatha-library.local'
        """
    )