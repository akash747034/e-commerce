"""add_payments_shipments_returns_refunds

Revision ID: 0fe26db9d722
Revises: 991be6e92c20
Create Date: 2026-10-15 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0fe26db9d722'
down_revision: Union[str, Sequence[str], None] = '991be6e92c20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Payments table
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            payment_gateway VARCHAR(50) NOT NULL,
            transaction_id VARCHAR(255) UNIQUE,
            amount NUMERIC(12, 2) NOT NULL,
            currency VARCHAR(10) NOT NULL DEFAULT 'INR',
            status VARCHAR(30) NOT NULL DEFAULT 'pending',
            payment_response TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            deleted_at DATETIME,
            CONSTRAINT ck_payments_amount_nonnegative CHECK (amount >= 0)
        )
    """))

    # 2. Shipments table
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS shipments (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            carrier VARCHAR(100) NOT NULL,
            tracking_number VARCHAR(100) NOT NULL UNIQUE,
            tracking_url VARCHAR(500),
            status VARCHAR(50) NOT NULL DEFAULT 'label_created',
            shipped_at DATETIME,
            estimated_delivery DATETIME,
            delivered_at DATETIME,
            notes TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            deleted_at DATETIME
        )
    """))

    # 3. Return Requests table
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS return_requests (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            order_item_id INTEGER REFERENCES order_items(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            reason VARCHAR(100) NOT NULL,
            comment TEXT,
            status VARCHAR(30) NOT NULL DEFAULT 'pending',
            admin_notes TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            deleted_at DATETIME
        )
    """))

    # 4. Refunds table
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS refunds (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            payment_id INTEGER REFERENCES payments(id) ON DELETE SET NULL,
            return_request_id INTEGER REFERENCES return_requests(id) ON DELETE SET NULL,
            amount NUMERIC(12, 2) NOT NULL,
            refund_method VARCHAR(50) NOT NULL DEFAULT 'gateway',
            gateway_refund_id VARCHAR(255) UNIQUE,
            status VARCHAR(30) NOT NULL DEFAULT 'pending',
            reason VARCHAR(255),
            notes TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            deleted_at DATETIME,
            CONSTRAINT ck_refunds_amount_positive CHECK (amount > 0)
        )
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DROP TABLE IF EXISTS refunds"))
    conn.execute(sa.text("DROP TABLE IF EXISTS return_requests"))
    conn.execute(sa.text("DROP TABLE IF EXISTS shipments"))
    conn.execute(sa.text("DROP TABLE IF EXISTS payments"))
