from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('users', sa.Column('last_login', sa.DateTime, default=sa.func.now()))

def downgrade():
    op.drop_column('users', 'last_login')