"""create sscd column

Revision ID: 5e823fb0eaaa
Revises: 0acf2526e02f
Create Date: 2023-12-22 19:09:12.936855

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from app.main import create_app, db
import sqlalchemy
from sqlalchemy.schema import DDL

# revision identifiers, used by Alembic.
revision = '5e823fb0eaaa'
down_revision = '0acf2526e02f'
branch_labels = None
depends_on = None


def upgrade():
    sqlalchemy.event.listen(
      db.metadata,
      'before_create',
      DDL("""
          CREATE EXTENSION IF NOT EXISTS vector;
          """)
    )
    op.add_column('images', sa.Column('sscd', Vector(256), nullable=True))
    # op.create_index(op.f('ix_images_sscd'), 'images', ['sscd'], unique=False)

def downgrade():
    # op.drop_index(op.f('ix_images_sscd'), table_name='images')
    op.drop_column('images', 'sscd')

