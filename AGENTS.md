# CampusHub Master Project Context & Engineering Rules

## 1. Project Identification
- **Title**: CampusHub: A Campus Marketplace & Facilities Booking System with Real-Time Availability Monitoring and Analytics Dashboard
- **Institution**: University of Science and Technology of Southern Philippines – Oroquieta Campus (USTP Oroquieta)
- **Project Type**: BSIT Capstone & Research Study (2026)
- **Researchers**: Lester Bulay, Kent Nicolas P. Carreon, Harold Coyoca, Frank Reyben S. Sabit

---

## 2. Technology Stack & Boundaries
- **Web Admin & Main Backend**: Django (Python) — **Primary Single Source of Truth**.
  - All Products, Orders, Facilities, Bookings, Auth, RBAC, Reports, and DSS MUST remain in Django.
- **REST API**: Django REST Framework (DRF) serving mobile & web endpoints.
- **Mobile App**: Flutter / Dart.
- **Database**: PostgreSQL (managed via pgAdmin).
- **Real-Time Chat**: FastAPI (Port 8001) — **strictly for messaging/chat only**. Never move marketplace/booking/auth business logic to FastAPI.

---

## 3. Institutional Design System & Brand Identity
- **Typography**: `Montserrat` for brand headers and logo; clean system/Roboto typography where configured.
- **Strict Brand Palette (ONLY 3 COLORS)**:
  - **Navy Blue**: `#1A1851`
  - **Gold Accent**: `#FCB316`
  - **Neutral White / Light**: `#FFFFFF` / `#f8fafc`
- **Zero AI-Slop Guidelines**:
  - No purple, green, red, teal, or rainbow badges.
  - No random gradients, excessive box shadows, or glassmorphism.
  - No oversized startup KPI cards or gratuitous decorative charts.
  - Institutional, compact tables, disciplined spacing, and university-grade consistency.

---

## 4. User Hierarchy & RBAC
- **Account Types**: Student, Faculty/Employee, Guest/External, Admin.
- **Seller Status is Independent**: Seller access is a permission status, NOT an account type (e.g., Account Type: `Student`, Seller Access: `Approved`).
- **Server-Side Enforcement**: Always enforce RBAC on API/backend views; never rely only on hiding UI elements.
- **Protected Super Admin**: The final active Super Admin must never be deleted, deactivated, or demoted.

---

## 5. Marketplace Module Rules
- **Payment Method**: **CASH ON PICKUP ONLY**.
  - NEVER use Cash on Delivery (COD), Delivery Fees, or online payment gateways.
- **Order Lifecycle**: `Pending` → `Confirmed / Processing` → `Ready for Pickup` → `Completed` (or `Cancelled`).
- **Variants & Inventory**:
  - Stock computed dynamically from active variants when customization is enabled.
  - Clean 2-row inventory layout (`41 pcs` on line 1, `3 variants` on line 2).
  - Never display redundant "In Stock" labels when stock is healthy.
  - Only show `Low Stock` (≤ 5) or `Out of Stock` (0).
- **Category Values**: Clean plain institutional text (no badge/pill containers).
- **Product Approval**: Statuses are `Pending`, `Approved`, `Rejected`, `Archived`. Managed within the Products module.

---

## 6. Facilities & Booking Module Rules
- **Facility Types & Diverse Workflows**:
  1. **Covered Court / Function Hall**: Slot-based / Event reservation with instant conflict detection against academic/event schedules.
  2. **Hostel Accommodation**: Room-based booking with check-in/out dates, guest count (adults/children), nights, room rate, and purpose of stay.
  3. **Training Kitchen / Assessment Center**: Schedule- and assessment-based reservation.
  4. **Commercial Spaces**: Lease application.
  5. **Food Analysis Hub**: Specialized Laboratory Service Request (see ISO procedure below).
- **Facility Statuses**: `Open for Booking`, `Temporarily Unavailable`, `Under Maintenance`, `Inactive` (do not use a generic "Available" which implies all time slots are free).

---

## 7. Laboratory Food Analysis Services (ISO Document: DPM-USTP-Oro-BEU-004)
*Focal Person: Conmar C. Malmis (USTP Oro Business Enterprise Unit - BEU)*

Food Analysis is **NOT** a standard facility reservation. It follows this exact verified workflow:
1. **Client Inquiry**: Client inquires about proximate analysis (protein, carbohydrates, fat, fiber, moisture, calorie, pH, total/insoluble solids).
2. **Sample Submission & Receiving Checklist**: Client presents sample. Administrative Aide inspects sample integrity:
   - Proper sealing
   - Correct volume/quantity (minimum required amount)
   - Temperature compliance
   - No foul smell or leakage
3. **Job Order Issuance**: If sample passes checklist, issue Job Order Request Form (`FM-USTP-Oro-BEU-001`).
4. **Laboratory Resource & Calibration Check**: Coordinate with Laboratory Technician to verify:
   - Availability of reagents and chemicals
   - Equipment calibration and functionality
5. **Acceptance or Disapproval**:
   - If resources available: Accept and log into Service Logbook with turnaround deadline (e.g. 2 weeks).
   - If disapproved: Issue formal written notice with specific reason (ISO compliant).
6. **Execution of Analysis**: Laboratory performs chemical/proximate testing.
7. **Billing & Payment**: Upon completion, Statement of Account (`FM-USTP-Oro-BEU-002`) issued. Client pays at the **Collecting Officer / Cashiering Office** based on Job Order rates. Cashier issues official receipt (OR).
8. **Release of Results**: Client presents OR at lab. Laboratory releases **Certificate of Analysis**.
9. **Client Satisfaction Survey**: Client completes Customer Feedback Form (`FM-USTP-Oro-BEU-Survey`).

---

## 8. Decision Support System (DSS) vs. Analytics
- **Analytics answers "What happened?"**: Historical sales, total order counts, facility utilization graphs.
- **DSS answers "What should the user consider doing next?"**:
  1. **Product Demand Forecasting**: Uses completed order history to forecast demand (e.g. expected next 7 days: 34 units vs. current stock: 20 -> suggest preparing 14 additional units). Shows "Insufficient historical data for reliable forecasting" when data is sparse.
  2. **Market Basket Analysis (Apriori)**: Calculates Support, Confidence, and Lift from completed order item sets to recommend promotional item bundles.
  3. **Alternative Facility Schedule Recommendations**: Suggests non-conflicting available time slots when a requested slot is blocked.
- **Rule**: Never label standard charts as DSS. Never fabricate fake forecast numbers.

---

## 9. Real Data & No AI Fabrication
- All metrics, charts, tables, inventory, reports, and forecasts must derive from actual database records.
- If data does not exist, show clear, honest empty states. Never hardcode fake records.

---

## 10. Required Response Protocol for Code Changes
After every implementation step, always report:
1. **Cause / Reason**
2. **Exact Files Changed**
3. **Changes Made**
4. **How It Works**
5. **Backend / API Behavior**
6. **Database / Migration Impact**
7. **Tests Performed**
8. **Remaining Limitations**
