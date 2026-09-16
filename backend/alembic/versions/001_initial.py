"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("role", sa.Enum("operator", "farmer", "admin", name="userrole"), nullable=False, server_default="operator"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone"),
    )
    op.create_index("ix_users_phone", "users", ["phone"], unique=True)

    # Bales
    op.create_table(
        "bales",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bale_id", sa.String(50), nullable=False),
        sa.Column("certificate_id", sa.String(50), nullable=False),
        sa.Column("farmer_id", sa.String(50), nullable=False),
        sa.Column("operator_id", sa.Integer(), nullable=False),
        sa.Column("crop_type", sa.String(50), nullable=False),
        sa.Column("residue_type", sa.String(50), nullable=False),
        sa.Column("declared_weight", sa.Float(), nullable=False),
        sa.Column("moisture", sa.Float(), nullable=True),
        sa.Column("density", sa.Float(), nullable=True),
        sa.Column("hub_id", sa.String(50), nullable=False),
        sa.Column("pool_id", sa.String(50), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("status", sa.Enum("CREATED", "POOLED", "STORED", "WEIGHED", "VERIFIED", "PAID", "DISPATCHED", "DELIVERED", name="balestatus"), nullable=False, server_default="CREATED"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["operator_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bale_id"),
        sa.UniqueConstraint("certificate_id"),
    )
    op.create_index("ix_bales_bale_id", "bales", ["bale_id"], unique=True)
    op.create_index("ix_bales_certificate_id", "bales", ["certificate_id"], unique=True)
    op.create_index("ix_bales_farmer_id", "bales", ["farmer_id"])
    op.create_index("ix_bales_hub_id", "bales", ["hub_id"])
    op.create_index("ix_bales_status", "bales", ["status"])

    # Pools
    op.create_table(
        "pools",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pool_id", sa.String(50), nullable=False),
        sa.Column("hub_id", sa.String(50), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("risk_level", sa.String(20), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pool_id"),
    )
    op.create_index("ix_pools_pool_id", "pools", ["pool_id"], unique=True)
    op.create_index("ix_pools_hub_id", "pools", ["hub_id"])

    # Weigh Events
    op.create_table(
        "weigh_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bale_id", sa.Integer(), nullable=False),
        sa.Column("measured_weight", sa.Float(), nullable=False),
        sa.Column("moisture", sa.Float(), nullable=True),
        sa.Column("density", sa.Float(), nullable=True),
        sa.Column("operator_id", sa.Integer(), nullable=False),
        sa.Column("verified", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("verification_details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["bale_id"], ["bales.id"]),
        sa.ForeignKeyConstraint(["operator_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bale_id"),
    )

    # Transactions
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("transaction_id", sa.String(50), nullable=False),
        sa.Column("bale_id", sa.Integer(), nullable=False),
        sa.Column("buyer_id", sa.String(50), nullable=True),
        sa.Column("verified_weight", sa.Float(), nullable=False),
        sa.Column("reference_rate", sa.Float(), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("status", sa.Enum("PENDING", "COMPLETED", "FAILED", name="transactionstatus"), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["bale_id"], ["bales.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("transaction_id"),
    )
    op.create_index("ix_transactions_transaction_id", "transactions", ["transaction_id"], unique=True)
    op.create_index("ix_transactions_bale_id", "transactions", ["bale_id"])

    # Payments
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("payment_id", sa.String(50), nullable=False),
        sa.Column("transaction_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("provider_reference", sa.String(100), nullable=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("status", sa.Enum("PENDING", "SUCCESS", "FAILED", name="paymentstatus"), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("payment_id"),
        sa.UniqueConstraint("transaction_id"),
    )
    op.create_index("ix_payments_payment_id", "payments", ["payment_id"], unique=True)

    # Documents
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.String(50), nullable=False),
        sa.Column("transaction_id", sa.Integer(), nullable=False),
        sa.Column("document_type", sa.Enum("E_INVOICE", "E_WAY_BILL", "DISPATCH_NOTE", "PAYMENT_RECORD", name="documenttype"), nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="GENERATED"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id"),
    )

    # Custody Events
    op.create_table(
        "custody_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bale_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("location", sa.String(100), nullable=True),
        sa.Column("operator_id", sa.Integer(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["bale_id"], ["bales.id"]),
        sa.ForeignKeyConstraint(["operator_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_custody_events_bale_id", "custody_events", ["bale_id"])
    op.create_index("ix_custody_events_timestamp", "custody_events", ["timestamp"])


def downgrade():
    op.drop_index("ix_custody_events_timestamp", table_name="custody_events")
    op.drop_index("ix_custody_events_bale_id", table_name="custody_events")
    op.drop_table("custody_events")
    op.drop_table("documents")
    op.drop_index("ix_payments_payment_id", table_name="payments")
    op.drop_table("payments")
    op.drop_index("ix_transactions_bale_id", table_name="transactions")
    op.drop_index("ix_transactions_transaction_id", table_name="transactions")
    op.drop_table("transactions")
    op.drop_table("weigh_events")
    op.drop_index("ix_pools_hub_id", table_name="pools")
    op.drop_index("ix_pools_pool_id", table_name="pools")
    op.drop_table("pools")
    op.drop_index("ix_bales_status", table_name="bales")
    op.drop_index("ix_bales_hub_id", table_name="bales")
    op.drop_index("ix_bales_farmer_id", table_name="bales")
    op.drop_index("ix_bales_certificate_id", "bales")
    op.drop_index("ix_bales_bale_id", "bales")
    op.drop_table("bales")
    op.drop_index("ix_users_phone", table_name="users")
    op.drop_table("users")
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS balestatus")
    op.execute("DROP TYPE IF EXISTS transactionstatus")
    op.execute("DROP TYPE IF EXISTS paymentstatus")
    op.execute("DROP TYPE IF EXISTS documenttype")
