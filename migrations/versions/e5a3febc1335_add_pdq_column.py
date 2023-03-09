"""add pdq column

Revision ID: e5a3febc1335
Revises: unknown
Create Date: 2023-03-06 13:45:08.505076

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import BIT


# revision identifiers, used by Alembic.
revision = 'e5a3febc1335'
down_revision = 'c2622ac44992'
branch_labels = None
depends_on = None

print('here at ssss')


def upgrade():
    print('here at e5a3febc1335')
    op.add_column('images', sa.Column('pdq', BIT(256), nullable=True))
    op.create_index(op.f('ix_images_pdq'), 'images', ['pdq'], unique=False)
    op.alter_column('images', 'phash', nullable=True)


def downgrade():
    op.drop_column('images', 'pdq')
    op.drop_index(op.f('ix_images_pdq'), table_name='images')
    op.alter_column('images', 'phash', nullable=False)

