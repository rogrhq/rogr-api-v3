from alembic import op
import sqlalchemy as sa

revision = '0001_create_core'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    pass  # Using ORM create_all in test for MVP

def downgrade():
    pass