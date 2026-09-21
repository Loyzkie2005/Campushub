-- CampusHub product inventory columns (PostgreSQL)
-- Run on the Kamatera / production database after deploying migration 0011.

ALTER TABLE campushub_product
    ADD COLUMN IF NOT EXISTS expiry_date DATE NULL;

COMMENT ON COLUMN campushub_product.expiry_date IS
    'Optional best-before / expiry date for perishable marketplace items (FIFO).';

COMMENT ON COLUMN campushub_product.stock IS
    'Available quantity. Inventory status (Low Stock, Out of Stock, etc.) is computed in the API.';

-- Optional index for inventory / expiry reports
CREATE INDEX IF NOT EXISTS idx_campushub_product_expiry_date
    ON campushub_product (expiry_date)
    WHERE expiry_date IS NOT NULL;
