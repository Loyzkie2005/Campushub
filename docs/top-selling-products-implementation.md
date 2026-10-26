# Top Selling Products: UI and sales/association separation

## Cause / reason

Build the compact product list from the supplied reference using real database records. Keep the requested title, **Top Selling Products**. The later functionality brief also requires a visible rank and sales amount, so each row includes the thumbnail when present, ranked product name, plain category, units sold, and a smaller sales amount beneath the units. **Units Sold** means the sum of quantities, not the number of orders.

The existing Super Admin ranking already included single-product completed, paid orders. Detailed Analytics used a separate query that could split the same product across historical names and show eight rows. Its association extractor also grouped legacy NULL order codes together. These inconsistencies were corrected.

## Exact files changed

Approximate lines and nearby anchors for this implementation:

| File | Line / anchor | Change |
| --- | --- | --- |
| `backend/templates/dashboard/partials/marketplace_analytics.html` | 10, `dashboard-top-selling` | Light-blue trophy container; product/units/sales heading; conditional real thumbnails; ranked name and category; quantity and sales amount. |
| `backend/static/components/css/admin_marketplace_overview.css` | 67, `.marketplace-card-symbol` | Compact 40px thumbnails, thin row separators, readable categories, right-aligned quantities and sales. Rows use two columns when the image is absent or hidden. |
| `backend/static/components/js/admin_dashboard_filter.js` | 26, `loadProductImage`; 156, product rendering | Matching filter/refresh rendering, thumbnail authentication, hide failed images, safe text rendering and empty heading visibility. |
| `backend/templates/dashboard/pages/admin_dashboard.html` | 18 / 593, asset includes | CSS and filter script cache version `20261004-product-list`. |
| `backend/core/modules/reports/dashboard_marketplace.py` | 9, `top_selling_products` | Add category and recorded seller metadata to the existing aggregate; no change to ranking or five-product limit. |
| `backend/core/modules/marketplace/services/analytics.py` | 94, `valid_sales_queryset`; 259, `_top_products`; 558, `_market_basket` | Exclude zero-quantity invalid sales; reuse the five-product ranking in Detailed Analytics; prevent NULL codes becoming artificial baskets. |
| `backend/core/modules/reports/dashboard_periods.py` | 176, `revenue_orders` | Use the same canonical completed/paid sales queryset for Super Admin metrics and rankings. |
| `backend/core/modules/reports/test_dashboard_marketplace.py` | 105, image/category test; 125, single-item test; 137, invalid quantity test | Verify metadata, image endpoint, deleted products, independent single-item rankings, and invalid quantities; extend isolated review fixtures. |
| `backend/core/modules/reports/tests.py` | 140, valid sales test; 158, parent variants; 173, NULL codes; 183, combo test | Check all lifecycle exclusions, consistent top-five ranking, no artificial baskets, combo identity, and singleton association input. |
| `scratch/dashboard-global-review/check-ranking.cjs` | Product assertions | Verify quantities, categories, image token, image failure, empty headings, and safe labels during actual API refresh. |
| `scratch/dashboard-global-review/prepare-ranking-visual.cjs` | `measure` and fixture preparation | Render actual templates using isolated test data and measure row content, real test-image dimensions, and visible rows. |
| `scratch/dashboard-global-review/verify-ranking-visual.cjs` | Browser case assertions | Check nine responsive/state cases, including 375px. |
| `scratch/dashboard-global-review/render-product-list.ps1` | Browser case list | Local headless Chrome rendering for the above cases. |
| `docs/top-selling-products-implementation.md` | This report | Implementation, validation, limitations, and manual scenarios. |

## Changes made / how it works

The card displays up to five actual sold products. It never adds sample products, synthetic images, or filler rows. A product with no image shows its text directly; a failed image is hidden. The existing honest empty message, **No completed product sales yet.**, remains when there are no qualifying sales. Images reuse the permission-aware product image endpoint, with the active admin tab token added only to same-origin URLs. Product/category text is escaped on server render and inserted with DOM text nodes on refresh.

The ranking database query groups surviving products by parent product ID, so options and historical names do not create separate ranks. Deleted products retain their recorded names. It calculates `Sum(quantity)` and `Sum(total_price)`, sorts by descending quantity, descending sales, then stable product identity, and limits to five. No association analysis is needed to appear in this list. The summaries still use two aggregate queries rather than a query per product.

## Backend / API behavior

The canonical sales filter is:

```python
MarketplaceOrder.objects.filter(
    status=MarketplaceOrder.STATUS_COMPLETED,
    payment_status=MarketplaceOrder.PAYMENT_PAID,
    quantity__gt=0,
).annotate(analytics_at=Coalesce("completed_at", "paid_at", "created_at"))
```

The selected date range filters `analytics_at`. Pending, processing, ready-for-pickup, cancelled, unpaid, and zero-quantity records do not enter these analytics. A completed, paid order with a genuine zero price remains valid. Marketplace revenue, completed count, average value, trend, rankings, category aggregation, and existing inventory sales history use the qualifying records. Refresh recalculates current database values; no fabricated numbers or additional sales writes were introduced.

Dashboard `marketplace.top_products` and its existing leader now have additive `category` and `seller_name` fields. Existing `rank`, `id`, `product_name`, `units_sold`, `sales`, image URL, and product URL remain available. Detailed Analytics keeps its existing product response shape but now uses the same grouping and five-row limit.

Frequently Bought Together stays in Detailed Analytics. Its existing routine computes directional support, confidence, and lift from real item sets, after minimum checks of three eligible transactions and two multi-item transactions. It is not called by the Super Admin ranking/refresh or the order-completion handler. The extractor ignores empty/NULL order codes and groups only recorded order codes. It does not combine purchases by buyer, time, category, receipt, or seller.

Predefined combo products remain their sellable parent listing in both ranking and transaction extraction. Their customization/components are never expanded into association evidence.

## Database / migration impact

No model changes or migrations. No production data edits or seeded placeholder records. Tests use an isolated test database; their product names/images exist only in test fixtures and review artifacts.

## Tests performed

77 Django tests passed:

```powershell
.\venv\Scripts\python.exe manage.py test modules.reports.test_dashboard_marketplace modules.reports.test_dashboard_periods modules.reports.test_sales_overview modules.reports.tests --noinput --keepdb
```

The ranking/refresh and global-controls JavaScript checks passed. JavaScript syntax and CSS parsing checks passed. Nine fresh Chrome renders passed: desktop, empty desktop, laptop, medium, mobile, 375px mobile, empty mobile, loading, and API error. Checks covered fitting row content, 40px loaded test images, chart preservation, responsive card alignment, quantities, headings, image failure, and authentication.

Review screenshots are `scratch/dashboard-global-review/ranking-desktop.png` and `ranking-mobile-small.png`. They show isolated test records, not production sales.

## Remaining limitations

**Genuine multi-product FBT cannot be populated from the current checkout schema.** `MarketplaceOrder` holds one product per row and has a unique `order_code`. There is no marketplace `OrderItem` model or shared checkout/transaction field, and marketplace payment is recorded directly on the order. `FacilityPayment` belongs to facility bookings and is not reused for sales. The current Flutter checkout sends individual product orders.

Consequently the current persisted records form singleton baskets, and FBT correctly stays in its insufficient-data state. Adding real multi-product FBT requires an explicit shared checkout record/key, item membership, and corresponding checkout API/mobile changes. Historical baskets cannot be reconstructed reliably from independent orders. This implementation does not invent such links, add a scheduler/rule store, or claim that a full persisted Apriori pipeline has been delivered. The existing pairwise association calculations can be tested independently with genuine item-set inputs.

## Manual test scenarios

Use a development database and orders whose completion/payment timestamps fall within the selected range. Open the dashboard, select that range, and Refresh after each change.

| Scenario | Expected sales behavior | FBT behavior |
| --- | --- | --- |
| 1. One Burger order, quantity 1, completed and paid | Burger appears with 1 unit, its sales amount; revenue, count, average, category and trend update. | No recommendation. |
| 2. Three separate completed/paid orders: Burger, Burger, Coke | Burger totals 2 units, Coke 1; only two rows appear. | No pair inferred from separate orders. |
| 3. Three genuine baskets: Burger+Coke, Burger+Coke, Burger+Fries | Product totals would be Burger 3, Coke 2, Fries 1; ordinary sales do not depend on a rule. | Current checkout cannot record these shared baskets. Verify the existing association calculations using `modules.reports.tests.MarketplaceAnalyticsTests.test_market_basket_support_confidence_and_lift`; a full checkout-to-FBT test requires the schema/API addition described above. |
| 4. Cancelled Burger order | No units, revenue, category or ranking contribution. | Excluded. |
| 5. Pending Burger/Coke orders | Neither contributes yet; processing and ready-for-pickup are also excluded. | Excluded. |
| 6. Completed but unpaid order | Excluded until payment is recorded as paid. On refresh after payment, its actual quantity and amount appear. | Payment alone does not fabricate a pair. |

Also verify a combo order appears as one listing, missing photos create no placeholder tile, broken photo requests hide the image, and a zero-sales range preserves the analytics section and its empty messages. Use Ctrl+F5 once to load the updated asset versions.
