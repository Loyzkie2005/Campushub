"""Initial batch drafts use the existing product, movement and FIFO ledger."""
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
import re

from django.utils import timezone

from .inventory import validate_stock_quantity


MAX_QUANTITY = 2147483647


def validate_initial_batches(raw, *, method, product_type, stock):
    """Return normalized receipt rows; None preserves the legacy API contract."""
    if raw is None:
        return None
    if method != "fifo" or product_type != "single":
        raise ValueError("Initial batches require Batch Inventory on a single product.")
    if not isinstance(raw, list) or not 1 <= len(raw) <= 100:
        raise ValueError("Enter between 1 and 100 initial batches.")
    rows = []
    for number, row in enumerate(raw, 1):
        if not isinstance(row, dict):
            raise ValueError(f"Batch {number}: enter a valid batch.")
        quantity = validate_stock_quantity(row.get("quantity"))
        if not 1 <= quantity <= MAX_QUANTITY:
            raise ValueError(f"Batch {number}: quantity must be a positive whole number within the supported limit.")
        raw_date = row.get("received_date")
        if not isinstance(raw_date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw_date):
            raise ValueError(f"Batch {number}: select a valid received date (YYYY-MM-DD).")
        try:
            received_date = date.fromisoformat(raw_date)
        except ValueError as exc:
            raise ValueError(f"Batch {number}: select a valid received date.") from exc
        if received_date < date(1900, 1, 1) or received_date > timezone.localdate():
            raise ValueError(f"Batch {number}: received date must be between 1900 and today.")
        expiry = row.get("expiry_date")
        if expiry not in (None, ""):
            if not isinstance(expiry, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", expiry):
                raise ValueError(f"Batch {number}: select a valid expiry date (YYYY-MM-DD).")
            try:
                expiry = date.fromisoformat(expiry)
            except ValueError as exc:
                raise ValueError(f"Batch {number}: select a valid expiry date.") from exc
            if expiry < timezone.localdate():
                raise ValueError(f"Batch {number}: expiry date must be today or later.")
        cost = row.get("unit_cost")
        notes = ""
        if cost not in (None, ""):
            # Currency is recorded explicitly in existing receipt notes. There
            # is no batch-cost column or new accounting calculation/schema.
            if isinstance(cost, bool) or not re.fullmatch(r"\d{1,8}(\.\d{1,2})?", str(cost)):
                raise ValueError(f"Batch {number}: enter a nonnegative unit cost with up to two decimals.")
            try:
                notes = f"Unit cost: PHP {Decimal(str(cost)):.2f}"
            except InvalidOperation as exc:
                raise ValueError(f"Batch {number}: enter a valid unit cost.") from exc
        if expiry:
            # Preserve optional batch metadata in the same existing receipt
            # notes as unit cost. This does not change FIFO or expiry allocation.
            notes = "\n".join(filter(None, [notes, f"Expiry date: {expiry.isoformat()}"]))
        rows.append({"quantity": quantity,
                     "received_at": timezone.make_aware(datetime.combine(received_date, time.min)),
                     "notes": notes})
    total = sum(row["quantity"] for row in rows)
    if total > MAX_QUANTITY or total != stock:
        raise ValueError("Stock must equal the batch total and stay within the supported quantity limit.")
    return rows


def save_initial_batches(product, rows, account, source):
    """Called inside listing creation's atomic transaction, including pending listings.

    Product.save invokes the same inventory/FIFO hooks as later receipts. This
    entry point is limited to a newly created zero-stock product; regular stock
    receiving keeps its approved-product rule in fifo.receive.
    """
    if product.stock or product.inventory_method != "fifo" or product.inventory_skus.get(variant_name="").batches.exists():
        raise ValueError("Initial batches can only be saved on a new empty Batch Inventory product.")
    for number, row in enumerate(rows, 1):
        product.stock += row["quantity"]
        product._inventory_kind = "receipt"
        product._inventory_actor = (account.get_full_name().strip() or account.username)[:150]
        product._inventory_notes = row["notes"] or None
        product._fifo_receipt = {"reference": f"Initial batch {number}",
                                 "received_at": row["received_at"],
                                 "user_id": account.pk if source == "admin" else None}
        product.save(update_fields=["stock", "updated_at"])
