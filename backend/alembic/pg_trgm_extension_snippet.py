"""enable pg_trgm extension

This must run before the trigram GIN indexes on leads.name / leads.company
can be created. If you generate the initial migration with
`alembic revision --autogenerate`, paste this into that migration's
upgrade()/downgrade() rather than running it separately — autogenerate
won't detect the missing extension on its own.
"""

from alembic import op


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")


def downgrade():
    op.execute("DROP EXTENSION IF EXISTS pg_trgm;")
