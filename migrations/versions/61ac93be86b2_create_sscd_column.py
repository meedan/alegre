"""create sscd column

Revision ID: 61ac93be86b2
Revises: e495509fad52
Create Date: 2023-11-06 20:57:37.335903

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from app.main import create_app, db


# revision identifiers, used by Alembic.
revision = '61ac93be86b2'
down_revision = 'e495509fad52'
branch_labels = None
depends_on = None


def upgrade():
    # op.add_column('images', sa.Column('sscd', Vector(256), nullable=True))
    pass


def downgrade():
    # op.drop_index(op.f('ix_images_sscd'), table_name='images')
    # op.drop_column('images', 'sscd')
    pass

