"""empty message

Revision ID: 297c7feec4c1
Revises: None
Create Date: 2016-04-26 21:27:28.856550

"""

# revision identifiers, used by Alembic.
revision = '297c7feec4c1'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('parent_item',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('parent_ASIN', sa.String(length=40), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('variation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('parent_ASIN', sa.String(length=40), nullable=True),
    sa.Column('ASIN', sa.String(length=40), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('item',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ASIN', sa.String(length=40), nullable=True),
    sa.Column('URL', sa.String(length=1000), nullable=True),
    sa.Column('list_price_amount', sa.Integer(), nullable=True),
    sa.Column('list_price_formatted', sa.String(length=40), nullable=True),
    sa.Column('name', sa.String(length=400), nullable=True),
    sa.Column('product_group', sa.String(length=40), nullable=True),
    sa.Column('date_last_checked', sa.Date(), nullable=True),
    sa.Column('parent_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['parent_id'], ['parent_item.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('ASIN')
    )
    op.create_table('image',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('thumbnailURL', sa.String(length=400), nullable=True),
    sa.Column('thumbnailHeight', sa.Integer(), nullable=True),
    sa.Column('thumbnailWidth', sa.Integer(), nullable=True),
    sa.Column('smallURL', sa.String(length=400), nullable=True),
    sa.Column('smallHeight', sa.Integer(), nullable=True),
    sa.Column('smallWidth', sa.Integer(), nullable=True),
    sa.Column('mediumURL', sa.String(length=400), nullable=True),
    sa.Column('mediumHeight', sa.Integer(), nullable=True),
    sa.Column('mediumWidth', sa.Integer(), nullable=True),
    sa.Column('largeURL', sa.String(length=400), nullable=True),
    sa.Column('largeHeight', sa.Integer(), nullable=True),
    sa.Column('largeWidth', sa.Integer(), nullable=True),
    sa.Column('item_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['item_id'], ['item.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('offer',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('condition', sa.String(length=200), nullable=True),
    sa.Column('offer_price_amount', sa.Integer(), nullable=True),
    sa.Column('offer_price_formatted', sa.String(length=40), nullable=True),
    sa.Column('prime_eligible', sa.Boolean(), nullable=True),
    sa.Column('availability', sa.String(length=200), nullable=True),
    sa.Column('item_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['item_id'], ['item.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('offer')
    op.drop_table('image')
    op.drop_table('item')
    op.drop_table('variation')
    op.drop_table('parent_item')
    ### end Alembic commands ###