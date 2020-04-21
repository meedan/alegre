"""Fix image contexts

Revision ID: 8490ccc2bf87
Revises:
Create Date: 2020-04-19 03:48:49.945678

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8490ccc2bf87'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE images SET context = json_build_array(context)")
    pass


def downgrade():
    pass
