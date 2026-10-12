# Deferred Post-Purchase & Payment Models

This file preserves the production-ready code and setup instructions for the **Inventory Audit**, **Payment**, **Payment Transactions**, **Invoices**, **Shipments**, and **Refunds** models. 

You can re-integrate these models whenever you are ready to expand from the core shopping flow into advanced payment gateway and fulfillment processing.

---

## 1. `app/models/payment.py`

**Purpose**: High-level record of payment for an order (gateway, amount, currency, status, paid timestamp).

```python
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class Payment(TimestampMixin, Base):
    __tablename__ = "payments"

    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_payments_amount_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    payment_method: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'credit_card', 'upi', 'net_banking', 'cod', 'wallet'
    payment_gateway: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # 'stripe', 'razorpay', 'paypal'
    transaction_id: Mapped[str | None] = mapped_column(
        String(100), unique=True, index=True, nullable=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(
        String(10), default="USD", server_default=text("'USD'"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(30), default="pending", server_default=text("'pending'"), nullable=False, index=True
    )  # 'pending', 'completed', 'failed', 'refunded'
    gateway_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    order: Mapped["Order"] = relationship(back_populates="payments")
    transactions: Mapped[list["PaymentTransaction"]] = relationship(
        back_populates="payment", cascade="all, delete-orphan"
    )
```

---

## 2. `app/models/payment_transaction.py`

**Purpose**: Granular gateway attempt logs (charge, capture, refund attempts, webhooks, error codes).

```python
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class PaymentTransaction(TimestampMixin, Base):
    __tablename__ = "payment_transactions"

    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_payment_transactions_amount_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    payment_id: Mapped[int] = mapped_column(
        ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    transaction_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # 'charge', 'authorization', 'capture', 'refund', 'void'
    gateway_transaction_id: Mapped[str | None] = mapped_column(
        String(100), unique=True, index=True, nullable=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, index=True
    )  # 'pending', 'successful', 'failed'
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    gateway_payload: Mapped[str | None] = mapped_column(Text, nullable=True)

    payment: Mapped["Payment"] = relationship(back_populates="transactions")
```

---

## 3. `app/models/shipment.py`

**Purpose**: Shipping, courier carrier tracking, tracking numbers, and delivery statuses.

```python
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class Shipment(TimestampMixin, Base):
    __tablename__ = "shipments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tracking_number: Mapped[str | None] = mapped_column(
        String(100), unique=True, index=True, nullable=True
    )
    carrier: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # e.g., 'FedEx', 'DHL', 'BlueDart', 'Delhivery'
    status: Mapped[str] = mapped_column(
        String(50),
        default="processing",
        server_default=text("'processing'"),
        nullable=False,
        index=True,
    )  # 'processing', 'shipped', 'in_transit', 'out_for_delivery', 'delivered', 'returned'
    shipping_label_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    estimated_delivery_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    order: Mapped["Order"] = relationship(back_populates="shipments")
```

---

## 4. `app/models/refund.py`

**Purpose**: Customer return requests, item return approvals, and refund tracking.

```python
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class Refund(TimestampMixin, Base):
    __tablename__ = "refunds"

    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_refunds_amount_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("order_items.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default="requested",
        server_default=text("'requested'"),
        nullable=False,
        index=True,
    )  # 'requested', 'approved', 'rejected', 'processed'
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    order: Mapped["Order"] = relationship()
    order_item: Mapped["OrderItem | None"] = relationship()
    user: Mapped["User"] = relationship()
```

---

## 5. `app/models/inventory_log.py`

**Purpose**: Audit trail for stock changes (`+` restock, `-` purchase, `+` cancelled order, `-` damaged).

```python
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class InventoryLog(TimestampMixin, Base):
    __tablename__ = "inventory_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    variant_id: Mapped[int | None] = mapped_column(
        ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True, index=True
    )
    quantity_change: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # e.g., -2 (order placed), +2 (cancelled), +50 (restock)
    reason: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'order_placed', 'order_cancelled', 'refund_restock', 'restock', 'damage'
    reference_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # order number, return id, or batch code

    product: Mapped["Product"] = relationship()
    variant: Mapped["ProductVariant | None"] = relationship()
```

---

## 6. `app/models/invoice.py`

**Purpose**: Formal tax/billing receipts and PDF download links.

```python
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class Invoice(TimestampMixin, Base):
    __tablename__ = "invoices"

    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="ck_invoices_total_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    invoice_number: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    invoice_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=0, server_default=text("0"), nullable=False
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=0, server_default=text("0"), nullable=False
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    pdf_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    billing_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), default="issued", server_default=text("'issued'"), nullable=False
    )  # 'draft', 'issued', 'paid', 'void'

    order: Mapped["Order"] = relationship(back_populates="invoice")
```

---

## How to Restore These Tables Later:

1. **Re-create each `.py` file** in `app/models/` using the code blocks above.
2. **Re-add relationships in `app/models/order.py`**:
   ```python
   payments: Mapped[list["Payment"]] = relationship(
       back_populates="order", cascade="all, delete-orphan"
   )
   shipments: Mapped[list["Shipment"]] = relationship(
       back_populates="order", cascade="all, delete-orphan"
   )
   invoice: Mapped["Invoice | None"] = relationship(
       back_populates="order", uselist=False, cascade="all, delete-orphan"
   )
   ```
3. **Re-export in `app/models/__init__.py`** and import in `alembic/env.py`.
4. **Run Alembic migration**:
   ```bash
   alembic revision --autogenerate -m "add payment, shipment, and inventory models"
   alembic upgrade head
   ```
