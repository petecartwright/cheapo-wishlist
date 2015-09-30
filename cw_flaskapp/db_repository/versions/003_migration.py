from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
item = Table('item', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('ASIN', String(length=40)),
    Column('URL', String(length=1000)),
    Column('list_price_amount', Integer),
    Column('list_price_formatted', String(length=40)),
    Column('name', String(length=400)),
    Column('product_group', String(length=40)),
    Column('date_last_checked', Date),
    Column('parent_id', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['item'].columns['date_last_checked'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['item'].columns['date_last_checked'].drop()
