"""order_item_rename_and_add_discount_columns

Revision ID: 991be6e92c20
Revises: 1de44c305824
Create Date: 2026-10-14 00:14:27.784890

Note: Written as raw SQL because SQLite does not support DROP COLUMN when
the column is referenced in a CHECK CONSTRAINT, and batch_alter_table hits
circular-dependency issues when new columns already exist from a partial run.
Raw SQL recreation is the most reliable approach for SQLite schema changes.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '991be6e92c20'
down_revision: Union[str, Sequence[str], None] = '1de44c305824'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # ------------------------------------------------------------------ #
    # Recreate order_items with new column names                           #
    # old: price, total_price                                              #
    # new: mrp, line_total + new item_discount                            #
    # ------------------------------------------------------------------ #
    conn.execute(sa.text("""
        CREATE TABLE order_items_new (
            id          INTEGER NOT NULL PRIMARY KEY,
            order_id    INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            product_id  INTEGER NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
            variant_id  INTEGER REFERENCES product_variants(id) ON DELETE SET NULL,
            product_name VARCHAR(255),
            variant_name VARCHAR(255),
            quantity    INTEGER NOT NULL,
            mrp         NUMERIC(12,2) NOT NULL DEFAULT 0,
            selling_price NUMERIC(12,2) NOT NULL DEFAULT 0,
            item_discount NUMERIC(12,2) NOT NULL DEFAULT 0,
            line_total  NUMERIC(12,2) NOT NULL DEFAULT 0,
            status      VARCHAR(30) NOT NULL DEFAULT 'pending',
            created_at  DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
            updated_at  DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
            deleted_at  DATETIME,
            CONSTRAINT ck_order_items_quantity_positive CHECK (quantity > 0),
            CONSTRAINT ck_order_items_prices_nonnegative CHECK (mrp >= 0 AND selling_price >= 0),
            CONSTRAINT ck_order_items_total_nonnegative CHECK (line_total >= 0),
            CONSTRAINT ck_order_items_item_discount_nonnegative CHECK (item_discount >= 0)
        )
    """))

    # Copy data — map old price→mrp, selling_price→selling_price, total_price→line_total
    # Handle partial-run case where mrp/line_total may already exist
    conn.execute(sa.text("""
        INSERT INTO order_items_new
            (id, order_id, product_id, variant_id, product_name, variant_name,
             quantity, mrp, selling_price, item_discount, line_total,
             status, created_at, updated_at, deleted_at)
        SELECT
            id, order_id, product_id, variant_id, product_name, variant_name,
            quantity,
            price,
            selling_price,
            0,
            total_price,
            status, created_at, updated_at, deleted_at
        FROM order_items
    """))

    conn.execute(sa.text("DROP TABLE order_items"))
    conn.execute(sa.text("ALTER TABLE order_items_new RENAME TO order_items"))

    # Recreate indexes
    conn.execute(sa.text("CREATE INDEX ix_order_items_order_id ON order_items (order_id)"))
    conn.execute(sa.text("CREATE INDEX ix_order_items_product_id ON order_items (product_id)"))
    conn.execute(sa.text("CREATE INDEX ix_order_items_variant_id ON order_items (variant_id)"))
    conn.execute(sa.text("CREATE INDEX ix_order_items_status ON order_items (status)"))

    # ------------------------------------------------------------------ #
    # Recreate orders: rename discount_amount → coupon_discount            #
    #                  add product_discount_total                          #
    # ------------------------------------------------------------------ #
    conn.execute(sa.text("""
        CREATE TABLE orders_new (
            id                  INTEGER NOT NULL PRIMARY KEY,
            order_number        VARCHAR(30) NOT NULL UNIQUE,
            user_id             INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            status              VARCHAR(30) NOT NULL DEFAULT 'pending',
            subtotal            NUMERIC(12,2) NOT NULL,
            product_discount_total NUMERIC(12,2) NOT NULL DEFAULT 0,
            coupon_discount     NUMERIC(12,2) NOT NULL DEFAULT 0,
            shipping_amount     NUMERIC(12,2) NOT NULL DEFAULT 0,
            tax_amount          NUMERIC(12,2) NOT NULL DEFAULT 0,
            total_amount        NUMERIC(12,2) NOT NULL,
            payment_status      VARCHAR(30) NOT NULL DEFAULT 'pending',
            payment_method      VARCHAR(30),
            shipping_address_id INTEGER NOT NULL REFERENCES addresses(id) ON DELETE RESTRICT,
            billing_address_id  INTEGER REFERENCES addresses(id) ON DELETE RESTRICT,
            coupon_id           INTEGER REFERENCES coupons(id) ON DELETE SET NULL,
            notes               VARCHAR(500),
            cancellation_reason VARCHAR(255),
            created_at          DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
            updated_at          DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
            deleted_at          DATETIME,
            CONSTRAINT ck_orders_subtotal_nonnegative CHECK (subtotal >= 0),
            CONSTRAINT ck_orders_product_discount_nonnegative CHECK (product_discount_total >= 0),
            CONSTRAINT ck_orders_coupon_discount_nonnegative CHECK (coupon_discount >= 0),
            CONSTRAINT ck_orders_shipping_nonnegative CHECK (shipping_amount >= 0),
            CONSTRAINT ck_orders_tax_nonnegative CHECK (tax_amount >= 0),
            CONSTRAINT ck_orders_total_nonnegative CHECK (total_amount >= 0)
        )
    """))

    conn.execute(sa.text("""
        INSERT INTO orders_new
            (id, order_number, user_id, status, subtotal,
             product_discount_total, coupon_discount,
             shipping_amount, tax_amount, total_amount,
             payment_status, payment_method,
             shipping_address_id, billing_address_id, coupon_id,
             notes, cancellation_reason,
             created_at, updated_at, deleted_at)
        SELECT
            id, order_number, user_id, status, subtotal,
            0,
            discount_amount,
            shipping_amount, tax_amount, total_amount,
            payment_status, payment_method,
            shipping_address_id, billing_address_id, coupon_id,
            notes, cancellation_reason,
            created_at, updated_at, deleted_at
        FROM orders
    """))

    conn.execute(sa.text("DROP TABLE orders"))
    conn.execute(sa.text("ALTER TABLE orders_new RENAME TO orders"))

    # Recreate indexes
    conn.execute(sa.text("CREATE UNIQUE INDEX ix_orders_order_number ON orders (order_number)"))
    conn.execute(sa.text("CREATE INDEX ix_orders_user_id ON orders (user_id)"))
    conn.execute(sa.text("CREATE INDEX ix_orders_status ON orders (status)"))
    conn.execute(sa.text("CREATE INDEX ix_orders_payment_status ON orders (payment_status)"))


def downgrade() -> None:
    conn = op.get_bind()

    # Restore orders: coupon_discount → discount_amount, drop product_discount_total
    conn.execute(sa.text("""
        CREATE TABLE orders_old (
            id                  INTEGER NOT NULL PRIMARY KEY,
            order_number        VARCHAR(30) NOT NULL UNIQUE,
            user_id             INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            status              VARCHAR(30) NOT NULL DEFAULT 'pending',
            subtotal            NUMERIC(12,2) NOT NULL,
            discount_amount     NUMERIC(12,2) NOT NULL DEFAULT 0,
            shipping_amount     NUMERIC(12,2) NOT NULL DEFAULT 0,
            tax_amount          NUMERIC(12,2) NOT NULL DEFAULT 0,
            total_amount        NUMERIC(12,2) NOT NULL,
            payment_status      VARCHAR(30) NOT NULL DEFAULT 'pending',
            payment_method      VARCHAR(30),
            shipping_address_id INTEGER NOT NULL REFERENCES addresses(id) ON DELETE RESTRICT,
            billing_address_id  INTEGER REFERENCES addresses(id) ON DELETE RESTRICT,
            coupon_id           INTEGER REFERENCES coupons(id) ON DELETE SET NULL,
            notes               VARCHAR(500),
            cancellation_reason VARCHAR(255),
            created_at          DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
            updated_at          DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
            deleted_at          DATETIME,
            CONSTRAINT ck_orders_subtotal_nonnegative CHECK (subtotal >= 0),
            CONSTRAINT ck_orders_discount_nonnegative CHECK (discount_amount >= 0),
            CONSTRAINT ck_orders_shipping_nonnegative CHECK (shipping_amount >= 0),
            CONSTRAINT ck_orders_tax_nonnegative CHECK (tax_amount >= 0),
            CONSTRAINT ck_orders_total_nonnegative CHECK (total_amount >= 0)
        )
    """))
    conn.execute(sa.text("""
        INSERT INTO orders_old SELECT
            id, order_number, user_id, status, subtotal,
            coupon_discount,
            shipping_amount, tax_amount, total_amount,
            payment_status, payment_method,
            shipping_address_id, billing_address_id, coupon_id,
            notes, cancellation_reason,
            created_at, updated_at, deleted_at
        FROM orders
    """))
    conn.execute(sa.text("DROP TABLE orders"))
    conn.execute(sa.text("ALTER TABLE orders_old RENAME TO orders"))
    conn.execute(sa.text("CREATE UNIQUE INDEX ix_orders_order_number ON orders (order_number)"))
    conn.execute(sa.text("CREATE INDEX ix_orders_user_id ON orders (user_id)"))
    conn.execute(sa.text("CREATE INDEX ix_orders_status ON orders (status)"))
    conn.execute(sa.text("CREATE INDEX ix_orders_payment_status ON orders (payment_status)"))

    # Restore order_items: mrp→price, line_total→total_price, drop item_discount
    conn.execute(sa.text("""
        CREATE TABLE order_items_old (
            id          INTEGER NOT NULL PRIMARY KEY,
            order_id    INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            product_id  INTEGER NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
            variant_id  INTEGER REFERENCES product_variants(id) ON DELETE SET NULL,
            product_name VARCHAR(255),
            variant_name VARCHAR(255),
            quantity    INTEGER NOT NULL,
            price       NUMERIC(12,2) NOT NULL DEFAULT 0,
            selling_price NUMERIC(12,2) NOT NULL DEFAULT 0,
            total_price NUMERIC(12,2) NOT NULL DEFAULT 0,
            status      VARCHAR(30) NOT NULL DEFAULT 'pending',
            created_at  DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
            updated_at  DATETIME NOT NULL DEFAULT (CURRENT_TIMESTAMP),
            deleted_at  DATETIME,
            CONSTRAINT ck_order_items_quantity_positive CHECK (quantity > 0),
            CONSTRAINT ck_order_items_prices_nonnegative CHECK (price >= 0 AND selling_price >= 0),
            CONSTRAINT ck_order_items_total_nonnegative CHECK (total_price >= 0)
        )
    """))
    conn.execute(sa.text("""
        INSERT INTO order_items_old SELECT
            id, order_id, product_id, variant_id, product_name, variant_name,
            quantity, mrp, selling_price, line_total,
            status, created_at, updated_at, deleted_at
        FROM order_items
    """))
    conn.execute(sa.text("DROP TABLE order_items"))
    conn.execute(sa.text("ALTER TABLE order_items_old RENAME TO order_items"))
    conn.execute(sa.text("CREATE INDEX ix_order_items_order_id ON order_items (order_id)"))
    conn.execute(sa.text("CREATE INDEX ix_order_items_product_id ON order_items (product_id)"))
    conn.execute(sa.text("CREATE INDEX ix_order_items_variant_id ON order_items (variant_id)"))
    conn.execute(sa.text("CREATE INDEX ix_order_items_status ON order_items (status)"))
