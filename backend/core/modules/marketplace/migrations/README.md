# Marketplace migrations index

**Schema owner:** `api` app (`backend/core/api/migrations/`)

This module folder holds admin UI templates and business logic. It does **not** own database tables yet.

| Migration | What it adds |
|-----------|----------------|
| `0004_passwordresetcode_productinteraction.py` | Product interactions (early) |
| `0006_product_image_url_textfield.py` | Product image field |
| `0007_marketplaceorder.py` | Orders |
| `0010_add_product_code.py` | Product code |
| `0012_product_customization.py` | Variations / customization JSON |

**Models:** `api.models` — `Product`, `MarketplaceOrder`, `SellerRequest`, `ProductInteraction`

**Services:** `modules/marketplace/services/` — inventory, customization, images, recommendations

**New migrations:** Add product/order changes under `api/migrations/` until a full app split is planned.
