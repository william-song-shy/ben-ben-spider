"""superadmin

Revision ID: 8be9fbb4d1b2
Revises: ae76d24072a7
Create Date: 2021-02-27 03:55:23.046319

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8be9fbb4d1b2'
down_revision = 'ae76d24072a7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('super_admin', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('super_admin')

    # ### end Alembic commands ###
