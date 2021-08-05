"""empty message

Revision ID: d8120aef29c2
Revises: d8120aef29c2
Create Date: 2021-08-04 18:09:29.478369

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd9a1aab0cbaa'
down_revision = 'd8120aef29c2'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('articles', sa.Column('hash_value', postgresql.ARRAY(sa.String(length=255, _expect_unicode=True)), nullable=True))

def downgrade():
    op.drop_column('articles', 'links')
