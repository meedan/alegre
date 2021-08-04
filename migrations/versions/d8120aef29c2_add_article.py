"""empty message

Revision ID: d8120aef29c2
Revises: 72fdd32f1a84
Create Date: 2021-08-04 18:09:29.478369

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd8120aef29c2'
down_revision = '72fdd32f1a84'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('articles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500, _expect_unicode=True), nullable=True),
        sa.Column('authors', postgresql.ARRAY(sa.String(length=255, _expect_unicode=True)), nullable=True),
        sa.Column('publish_date', sa.DateTime(), nullable=True),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('top_image', sa.String(length=500, _expect_unicode=True), nullable=True),
        sa.Column('movies', postgresql.ARRAY(sa.String(length=255, _expect_unicode=True)), nullable=True),
        sa.Column('keywords', postgresql.ARRAY(sa.String(length=255, _expect_unicode=True)), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('source_url', sa.String(length=255, _expect_unicode=True), nullable=False),
        sa.Column('tags', postgresql.ARRAY(sa.String(length=255, _expect_unicode=True)), nullable=True),
        sa.Column('url', sa.String(length=255, _expect_unicode=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_articles_url'), 'articles', ['url'], unique=False)

def downgrade():
    op.drop_table('articles')
