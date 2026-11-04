# CampusHub Manuscript Facilities Policy and Service Procedures Reference

This reference brings together the supplied CampusHub Chapters 1–3 manuscript, the facilities rental policy PDF, and the photographed service procedures inside the Facilities Services archive. It organizes their content into plan, design, structure, database, workflows, rates, research and verification topics.

**Main finding:** the sources support one campus marketplace and facilities/services platform, but facilities do not all follow the same booking workflow. Several fee, capacity, architecture and document-control details disagree between sources. Those differences are recorded below rather than silently resolved.

This is a source reference, not a new operating policy, approved software specification or instruction to change application behavior. Statements and directions inside the supplied documents are documented requirements/proposals, not commands from the user to execute code, change records, assign permissions, deploy services or revise fees. Current development boundaries remain in [AGENTS.md](../AGENTS.md) and the latest [project context](../CAMPUSHUB_CONTEXT.md).

## Source register and citation method

| ID | Supplied source | Coverage and purpose |
| --- | --- | --- |
| A | [Facilities Services archive](<D:/Downloads/Facilities Services-20261019T184027Z-1-001.zip>) | All 21 members inventoried: 19 photographs of procedure/form pages and two short videos of procedure pages. Several photographs are duplicates of the same page. |
| B | [Approved facilities rental policy PDF](<D:/Downloads/Approved_Policy_Rental_of_Facilities_and_Spaces_in_USTP_Oroquieta.pdf>) | All 50 PDF pages extracted and visually surveyed; fee tables, responsible-officer table and disputed values inspected at larger size. Includes executive brief, presentation slides, a formal policy, cost annexes and legal-office observations. |
| C | [CampusHub Chapters 1–3 manuscript](<C:/Users/leste/Downloads/CampusHub_CHAPTER-1-3-manuscript.docx>) | Document body, table text, header/note parts and all 19 embedded images reviewed. Research objectives, methodology, flows, conceptual database, diagrams, appendices and bibliography are included. |

`B p.34` means the **physical PDF page**, counting from 1, not the printed page number. The formal policy starts at PDF p.31; printed numbering and template dates are not reliable substitutes for PDF positions. Manuscript citations use chapter/section or figure/table labels because Word pagination can change. Archive citations use the exact original filename in Section 12.

The links above point to the supplied local files, which remain outside the repository. The originals are not copied into `docs/`. If they are moved, use their filenames and hashes in Section 13 to locate the reviewed versions.

## 1. Plan

### 1.1 Purpose and problem

The manuscript proposes **CampusHub: A Campus Marketplace & Facilities Booking System with Real-Time Availability Monitoring and Analytics Dashboard** for USTP Oroquieta. Its authors are Lester Bulay, Kent Nicolas P. Carreon, Harold Coyoca and Frank Reyben S. Sabit, for the 2026 BSIT capstone/research project. [C, title page]

The reported problems are decentralized product selling through social media/private messages, manual booking calendars/logbooks, delayed coordination, possible overlapping reservations, inconsistent transaction records, limited reporting and difficulty understanding buying patterns. The policy likewise seeks standardized rental procedures, fee assessment, accountability and protection of university resources. These are the sources' stated motivations, not new findings from a live-system audit. [C §§1.1–1.2, 3.3; B pp.1, 5–8, 31–33]

### 1.2 Objectives

The manuscript's general objective is to design, develop and evaluate the integrated system. Its specific objectives cover a centralized marketplace/booking platform, reporting and analytics, functionality/usability/user-satisfaction evaluation, and content-based personalized recommendations. Later objectives also describe association-rule mining for product bundles. **Personalized recommendations and Apriori product associations are separate objectives** and should be reconciled consistently across the manuscript. [C §§1.3, 3.4, system objectives]

### 1.3 Development approach

The manuscript uses Agile stages: Plan, Design, Develop, Test, Deploy, Review and Launch. Its Gantt chart spans February–November 2026. These are the manuscript's described/planned activities; the figure does not establish that every phase has been completed, deployed or accepted. [C §3.1, Figure 1; §3.4.6, Figure 7]

| Stage | Meaning for CampusHub | Evidence to retain |
| --- | --- | --- |
| Plan | Define actors, approved facilities/services, marketplace scope, institutional workflows and limitations | Agreed requirements and source locations |
| Design | Map screens, API boundaries, permissions, records, documents and separate facility workflows | Reviewed diagrams, forms and resolved rule decisions |
| Develop | Implement through existing Django/Flutter/chat responsibilities | Reviewed source and feature guides |
| Test | Check functionality, ownership, calculations, scheduling, usability and failures | Actual isolated test results and evaluation data |
| Deploy | Configure an identified release in the intended environment | Build/revision, deployment and recovery evidence |
| Review | Collect and assess stakeholder feedback | Recorded feedback, issues and resulting decisions |
| Launch | Obtain institutional approval and user acceptance | Acceptance/training/turnover records |

### 1.4 Scope and limitations

The manuscript limits the system to selected USTP Oroquieta departments/facilities, requires an internet connection, excludes online payment gateways and describes manual payment outside the system. It does not establish offline transactions or a multi-institution platform. [C §§1.5, 3.4.5]

The current project separately requires Django to own marketplace, bookings, authentication, roles, reports and decision support; FastAPI is chat-only. No document review here changes that boundary. No new ML service, online gateway, courier integration, record or migration is authorized by the manuscript. [Project rules; see conflict C01 below]

## 2. Design

### 2.1 System design described in the manuscript

The proposed system is client–server: a Flutter mobile client and browser-based administrative dashboard communicate with a Python/Django REST backend and PostgreSQL. Figure 2 shows authentication/authorization, booking/facility/marketplace/account services, logs, cash transactions, reports and notification outputs. Email and SMS/push are drawn as external-service concepts; the illustration is not evidence that all channels are implemented or currently delivering messages. [C §3.4, Figure 2]

The manuscript mentions Figma, Canva and Draw.io for interface design, prototypes, ERDs and flowcharts. It includes registration, login, marketplace and booking flowcharts, an Agile illustration, a Gantt chart, ERDs, a use-case diagram, context diagram and level-1 DFD. It is not a complete screen-by-screen UI specification. [C software requirements; Figures 1–13]

### 2.2 Current implementation design reference

For actual colors, component structure, current typography and navigation, use [web UI/UX rules](web-ui-ux-guidelines.md), [mobile typography](mobile-typography.md), [mobile design](../campushub/DESIGN.md) and [the system overview](campushub-system-overview.md). These are current project references, not styling rules extracted from the old manuscript.

The accepted mobile Home/navigation font roles are Inter headings 600, menu labels 500, KPI numbers 700 and descriptions 400, with the existing SugarPie wordmark, Montserrat profile identity and Poppins default elsewhere. The latest seller Home places Suggested Product Bundles below the KPI cards. This review does not restyle that interface.

### 2.3 Design consequences of the source workflows

The sources imply different forms and states, rather than one universal room-booking form:

- Event venues need purpose, date/time, capacity, approval, fees/deposit, inspections and release/clearance records.
- Hostel accommodation needs rooms, occupancy and stay dates, with check-in/key handling and post-use inspection.
- Commercial spaces need an application, required permits, review and a written lease/concession agreement.
- Food Analysis needs sample receiving, laboratory-resource checks, job order, analysis, later billing and receipt-controlled release.
- BPP NC II needs candidate prerequisites, assessor availability, assessment scheduling, payment, preparation, safety orientation and certification/results.

An operational facility being open does not mean that a requested slot, room, sample or assessment has been approved. These design implications are explanatory; they do not declare every corresponding field/state implemented.

## 3. Structure and responsibilities

### 3.1 Manuscript actors

| Actor as described | Manuscript responsibilities | Qualification for the current project |
| --- | --- | --- |
| Super Admin | Users/roles, system oversight, reports and analytics | Preserve server-side permissions and protection of the final active Super Admin |
| Department Admin / Admin | Marketplace products, seller/product approvals, orders and reports | Use existing Marketplace Admin scope; diagram labels are not new grants |
| Cashier / Facility Admin | Facility schedules, booking approval, prices, payment verification and reports | Actual collecting, coordination and approval duties must follow assigned permissions and institutional workflow |
| Student | Browse/buy, cart, bookings, profile, messages and approved selling | Selling requires independent seller approval |
| Faculty/Employee | Facility access and applicable eligibility | Account type alone does not establish entitlement to every discount |
| Guest/External | Browse/buy and permitted facility requests | General guest access does not override hostel's internal-client restriction |
| Seller | Approved selling and seller analytics/bundle information | Permission status, not a replacement account type |

Sources: C §3.4, users/roles and Figures 11–12; B pp.32, 37–41. Some manuscript descriptions combine roles; do not merge current backend permissions simply because a diagram does.

### 3.2 Responsible offices in the policy and procedures

The policy's officer table assigns the Head of the Business Enterprise Unit to hostel, Function Hall, canteen/stall spaces, vendo/photocopying spaces and Covered Court; the Food Analysis Hub Coordinator and Assessment Center Coordinator cover their respective services. [B p.37]

The photographed procedures additionally identify Administrative/Booking Staff, BEU Head/Manager or authorized approver, facility/laboratory coordinators, technicians/assessors, maintenance/security and the Collecting Officer/Cashiering Unit. Printed focal persons include Conmar C. Malmis and Rosela M. Narzabal. Those printed names identify the supplied documents; they do not automatically assign today's application staff roster or signing authority. [A procedure pages]

### 3.3 Current project organization

Application business services remain in Django under `backend/core/`, with domain modules including marketplace and facilities. Flutter screens/services/models/widgets are under `campushub/lib/module_app/`. FastAPI messaging is under `backend/chat_service/`. PostgreSQL model/migration ownership must be checked in existing code; do not rebuild the schema from a manuscript diagram. See [backend architecture](../backend/core/modules/ARCHITECTURE.md) and [whole-project structure](campushub-system-overview.md#folder-structure-and-ownership).

### 3.4 Technology and infrastructure requirements

The manuscript's Table 2 lists HTML5, CSS version `5.01`, JavaScript `ES2025`, Python `3.14.4` and DART `v3.116`. These are transcribed source entries requiring editorial/version verification, not the repository's current dependency declarations. Table 3 describes mobile devices, browser-capable administrative computers, backend/database servers and stable Wi-Fi/LAN/mobile data in general terms; it does not provide a measured production-capacity benchmark. Table 4 describes database, mobile, backend and design tools. Actual installation and deployment choices must come from the current project manifests, lockfiles and deployment documentation. [C Tables 2–4]

## 4. Database

### 4.1 Conceptual entities shown in the manuscript

These are **proposed diagram/narrative entities**, not a verified inventory of current Django tables, primary keys or migrations. Singular/plural labels differ in the manuscript itself. [C §3.5.1, Figures 8–10]

| Domain | Conceptual records | Relationships and intended purpose |
| --- | --- | --- |
| Facilities | FACILITY, ROOMS, BOOKINGS | A facility can have rooms; a booking links a user to a facility and, where applicable, a room |
| Facility accounting | FACILITY_PAYMENTS | Payment/receipt records linked to a booking, separate from booking status |
| Facility history | FACILITY_AVAILABILITY_LOG, FACILITY_FEEDBACK | Recorded availability changes, and facility/user feedback; reconcile the feedback relationship between prose and diagram |
| Products | PRODUCTS | Department/seller, description, category, price, stock and images |
| Shopping | CART, CART_ITEMS | A user's cart and product quantities |
| Orders | ORDERS, ORDER_ITEMS / ORDERS_ITEMS | Buyer/seller order and its item/quantity/price details |
| Order accounting | ORDER_PAYMENT / ORDERS_PAYMENT | Order payment amount/status and timestamps |
| Inventory and reviews | INVENTORY_MOVEMENTS, PRODUCT_FEEDBACK | Stock movement history and recorded product feedback |
| Identity and access | USERS, DEPARTMENTS, ROLE, USER_ROLE | User identity, organizational relation and role assignment |
| Communication and audit | CHAT, NOTIFICATION, ACTIVITY_LOGS | Messages, user-facing notifications and activity history |

The ERDs show UUID identifiers and proposed relationships. This review does not establish that the working database uses those exact keys or table names. Chat ownership must be reconciled with the existing chat-only service, rather than moving production chat records into Django merely to match the drawing.

### 4.2 Additional records implied by the institutional workflows

The procedures call for reservation/calendar logs, approved/disapproved requests, job orders, Statements of Account, official receipts, inspections, damage/refund records, sample receiving/rejection, reagent/equipment traceability, orientation logs, assessment results, contracts, permits and satisfaction surveys. These are record requirements to trace against existing implementation. They are not an instruction to add one new table per paper form or to create migrations without a schema review.

Keep booking/application approval, payment evidence, fulfillment/service progress and document release distinguishable. A booking row must not become paid simply because a client submitted a request, and a laboratory result must not become released simply because analysis finished.

## 5. Facilities policy and client eligibility

### 5.1 Policy context

The PDF contains material labelled policy proposal as well as visible approval stamps. The stamps identify BOR Resolution No. 91, series 2026; the formal policy lists submission January 22, 2026. The printed form-template date `03.17.25` is separate metadata and should not be substituted for policy approval/effectivity. The policy says effectivity follows Board of Regents approval. This review records the supplied copy; it does not independently authenticate a BOR register or check for later amendments. [B pp.3, 28–31, 34, 41, 45–47]

The policy cites RA 10919, COA rules, BOR 172 s. 2025 (Panaon), BOR 141 s. 2025 (Claveria), university rules and related financial/utility references. These are citations **within the supplied document**, not independently researched statements of current law. [B pp.1, 22, 31, 41]

### 5.2 Eligibility and discounts

| Category | What the policy says | Important boundary |
| --- | --- | --- |
| Internal clients | Faculty, retirees, staff, students, recognized student organizations and university offices requesting official university-related use | General facilities such as halls/courts have a stated 50% rental discount; specialized services follow their own structures |
| Immediate family | Legally recognized spouse, parents and children of faculty/staff | Stated 20% discount applies only to Function Hall and Covered Court, subject to verification/availability |
| External clients | Outside individuals, groups, organizations or agencies | Formal request, documents, approval and required payment before use |
| Hostel users | Schedule explicitly says internal clients only | Do not assume every guest/external account can book accommodation |
| Specialized laboratory/assessment clients | Service-specific requirements and fee structures | Do not apply the general 50% discount to all laboratory/assessment fees |

Sources: B pp.9, 32–35, 38–39. Eligibility evidence, activity purpose and approved exceptions are separate from an account's displayed role. No stacking rule is established here; do not invent cumulative discounts.

### 5.3 Use and accounting controls

The policy requires approved purposes, reservations/approval, campus safety rules, cleanliness, careful equipment use, adherence to the authorized time including setup/dismantling, and coordination with custodians. Damage/loss/additional cleaning can be charged. The university can deny/cancel unsafe, noncompliant or conflicting activities. [B pp.38–39]

Collections must use authorized university payment channels, be supported by official receipts, be recorded/deposited appropriately and retained for audit. Refundable damage deposits are distinct from rental income; remaining deposits can be returned after assessment. Rate adjustments require the stated recommendation/endorsement/approval process. These source requirements do not authorize an app user to alter fees. [B p.39]

The legal-office observations call for written lease/concession agreements, independent-concessionaire status, required permits, official collection controls, reporting and clarification of the accounting classification of rental income. The appended memo changes topic to **USTP Jasaan** on p.49 and continues on p.50. Its parking amounts must not be imported as Oroquieta rental rates. [B pp.48–50]

## 6. Rates deposits and financial assumptions

Amounts below are a transcription/comparison of supplied sources. They are not live configuration, a new approved price list or authorization to overwrite existing charges. Conflicting entries remain explicit.

### 6.1 Facility and commercial-space schedule

| Item | Amounts stated in the source | Terms and source location |
| --- | --- | --- |
| Hostel individual | PHP 800 per person/night | Internal clients; airconditioned room, bedding and CR; six rooms, two persons per room; PDF pp.9, 33 |
| Hostel paired booking | PHP 500 per person/night for two-person room booking | Annex wording also uses group rate; retain the booking basis, not a fabricated per-room price; pp.9, 33, 43 |
| Hostel damage deposit | PHP 500 flat | pp.9, 33 |
| Function Hall | PHP 6000 first four hours; PHP 1000 per additional hour | Includes stated furnishings/basic sound; full payment two days before event; pp.11, 34 |
| Function Hall deposit |40% of PHP 6000 in formal table; slide says 40% based on proposed fees | The formal base yields PHP 2400 by arithmetic, not a separately quoted source amount; reconcile applicable base before configuration; pp.11, 34 |
| Function Hall capacity |30–50 persons in slide; 30–40 in formal table | **Unresolved conflict**, pp.11, 34 |
| Lessee-developed canteen space | PHP 3000/month | Separate electric meter; prior campus approval and renewable one-year contract subject to evaluation; pp.13, 34 |
| Standard 3m² stall | PHP 1500/month regular term; PHP 750/month midyear | Water PHP 400/month; source also states PHP 400/m² for area exceeding 3m² without fully explaining the charging formula; pp.13, 34 |
| Wi-Fi vendo space | PHP 300/month/machine | Separate electric meter; pp.15, 34 |
| Photocopying/printing space | PHP 800/month regular term in slide; PHP 500/month in formal table; PHP 300/month midyear in both | **Unresolved regular-term conflict**, pp.15, 34 |
| Covered Court package | PHP 3000 first four hours; PHP 500/additional hour | Weekend availability stated, separate electric meter, capacity 300–500; pp.16, 34 |
| Covered Court hourly | PHP 700/hour as a separately listed rental option | Do not silently combine this with the four-hour package; pp.16, 34 |
| Covered Court chairs | PHP 10/chair | For inside activity only; pp.16, 34 |

### 6.2 Food Analysis charges

| Analysis | Main schedule | Annex C | Finding |
| --- | --- | --- | --- |
| Moisture | PHP 604.80 | PHP 604.80 | Agrees |
| Ash | Not listed in the main schedule | PHP 644.00 | Annex and photographed laboratory scope include Ash |
| Fat | PHP 644.00 | PHP 1008.00 | **Conflicting charge** |
| Protein | PHP 806.40 | PHP 806.40 | Agrees |
| Fiber | PHP 1299.20 | PHP 1299.20 | Agrees |

Sources: B pp.18, 34–35, 45; A laboratory scope photo `IMG_20261011_215432_688.jpg`. The annex labels its rates per analysis/per sample and links its cost basis to a FASTLAB price list. The supplied FASTLAB reference is not independently retrieved here. Do not relabel the main schedule's Fat charge as Ash without institutional correction.

Samples must be labelled and acceptable; unsuitable samples may be rejected. Turnaround depends on laboratory capacity. Results are described as confidential and for research/quality assessment. Do not present the blank turnaround field on the Job Order as a universal fixed deadline. [B pp.18, 35; A Job Order form]

### 6.3 BPP NC II charges

The presentation lists PHP 1700/candidate and PHP 1455 for USTP students, describing the latter as 15% discounted. Annex D's prose instead states a PHP 255 discount and **PHP 1445** final fee, which matches `1700 ×0.85`. However, the same annex's revenue table still uses **PHP 1455**. The formal main table lists PHP 1700/pax for BFPT third-year students rather than clearly repeating the student discount. Record all these discrepancies; do not select a value automatically. [B pp.20, 27, 35, 46]

The document describes fees as nonrefundable once scheduled, rescheduling only for valid reasons with prior notice, TESDA/safety compliance, charges for damaged/lost items, and materials supplied by the center. Annex D cites an assessment-fee reference; that national fee claim is not independently verified in this review. [B pp.20, 35, 46]

### 6.4 Cost annexes and projections are not collected revenue

| Source section | Information contained | Correct interpretation |
| --- | --- | --- |
| Setup/infrastructure, p.23 | PHP 5000 metering estimate and PHP 551753 estimated equipment/supplies; accommodation subtotal PHP 283253 and Function Hall subtotal PHP 268500 | Budget/cost estimates, not purchases verified against current records |
| Hostel, pp.24, 42–44 | Six rooms/two people per room, utility/consumable assumptions,800/500 pricing analysis; annual projections PHP 82500, PHP 136500 and PHP 219000 | Projection table uses PHP 250, different from the rental schedule; do not use it as a customer rate or actual sales |
| Function Hall, pp.25, 44 | Five illustrative events at PHP 6000, gross PHP 30000, operating expenses PHP 16136 and net PHP 13864 | Assumed annual scenario, not five confirmed bookings |
| Food Analysis, pp.26, 45 |60% cost allocation and 40% margins; 20 samples per analysis; annual margin PHP 34899.20 | Modelled margins/sample counts, not actual laboratory activity |
| Assessment, pp.27, 46 |100 student and 25 outside candidates; PHP 188000 gross, PHP 150300 operating expenses, PHP 37700 net | Scenario uses the disputed student fee; not actual candidate counts or collection totals |

These policy planning figures must not be inserted into CampusHub dashboards as live metrics, forecasts or research results.

## 7. Service procedures from the archive

### 7.1 Covered Court Rental

The photographed manual is titled **Covered Court Rental**, code `DPM-USTP-Oro-BEU-002`. Its sequence is request/availability check, purpose/capacity/compliance review and approval/disapproval, booking confirmation and reservation slip/contract, payment through the Collecting Officer/Cashiering Unit, pre-event coordination/inspection/monitoring, then post-use inspection, damage assessment and refund of the remaining deposit. [A files 205657–205824; see Section 12]

Records include the request/job order, booking calendar, approved/disapproved form, reservation slip, official receipt, setup/inspection checklists, monitoring log, damage report and refund slip. Multiple photos repeat page 2; they are not separate workflow versions established by this review.

### 7.2 Lease of Space

The lease manual covers canteen spaces, food stalls, vending and photocopying/printing operations. It also visibly uses code `DPM-USTP-Oro-BEU-002`, the same code shown on the court manual. That document-control collision must be clarified, not corrected by guessing a new code. [A `IMG_20261011_213043_666.jpg` and related pages]

Its process is:

1. Receive a Letter of Intent and attachments.
2. Prepare/submit the BEU recommendation to the Campus Director or approving authority.
3. Notify the applicant of approval/disapproval.
4. Prepare the Contract of Lease/Agreement based on approved terms.
5. Obtain Campus Director/applicant signatures, notarize at the lessee's stated expense, and provide the notarized copy.

The notes name Business Permit, Sanitary Permit and food-stall staff Health ID requirements. The policy/legal memo additionally names BIR registration and other applicable permits. Commercial lease records include the letter, permits, recommendation, Notice of Award and signed contract. This is an application/contract process, not an ordinary short-duration reservation. [A files 213043–213147; B pp.39, 48–49]

### 7.3 Hostel Accommodation and Function Hall Services

Code `DPM-USTP-Oro-BEU-001` describes reservation receipt, availability/purpose/capacity review, BEU/authorized approval, confirmation/job order, fees/deposit and official receipt, pre-use preparation, check-in/event monitoring, post-use inspection, damage/additional-charge assessment, remaining-deposit refund and client feedback. Hostel use includes key issuance/retrieval. [A files 213527, 213550, 213614]

The note on payment says “within 48 hours before the event,” while the policy Function Hall table says full payment two days before the event. Preserve the wording difference until a clear cutoff is established; do not invent a late-payment window. The photos' page counters are inconsistent (first pages say1of2/2 of 2 while a further page says 3 of 3). The extra photographed page contains important notes and records and was included in this review.

Required records include reservation slip/calendar, Job Order `FM-USTP-ORO-BEU-001`, OR, inspection/sanitation checklists, clearance/refund slip, satisfaction survey and key logbook. No universal online-payment behavior is specified.

### 7.4 Laboratory Food Analysis Services

Code `DPM-USTP-Oro-BEU-004`, with Conmar C. Malmis printed as focal person, covers moisture, ash, fat, protein and fiber in the photographed scope. The service is not a standard venue reservation. [A files 215432, 215706, 215753]

The documented sequence and records are:

1. Receive inquiry/sample and verify integrity such as proper sealing, temperature and volume before acceptance; complete the Job Order request.
2. Check pending/ongoing laboratory work and availability of reagents/materials; identify the requested work and schedule.
3. Assign the technician and submit to the BEU Manager for approval; record nonacceptance/refusal and its reason when appropriate.
4. Perform analysis and document it in the Service/Production Logbook.
5. After completion, calculate prescribed fees from the recorded work and issue a Statement of Account reviewed/signed by the BEU Manager.
6. Prepare the Order of Payment; payment is made through the Cashiering Office, which issues the OR.
7. Release analyzed samples/results upon presentation of the OR, with completion recorded in the logbook/SOA.
8. Collect client satisfaction feedback.

The process table names Certificate of Analysis. The evidence list also includes sample receipt/rejection, reagent inventory/expiry and traceability records. Notes require reagent lot numbers and equipment IDs in the service logbook. The project rules additionally retain readiness/calibration and sample-integrity checks, written reasons for refusal and receipt-controlled release. Broader inquiry examples in project guidance do not create a tariff for an analysis absent from the supplied schedule.

Billing after analysis is a substantive difference from venue pre-use payment and BPP pre-assessment collection. Do not enforce one payment sequence across all service types.

### 7.5 Training Kitchen Laboratory Assessment Center BPP NC II

Code `DPM-USTP-Oro-BEU-005` covers training/competency assessment, demonstrations, evaluation and result/certification release for internal/external clients. [A files 220321, 220343, 220420]

The process receives/reviews registration and prerequisite documents, checks facility and TESDA-accredited assessor availability, confirms the assessment schedule, assesses/collects payment and issues OR, prepares the kitchen/equipment, conducts orientation and assessment, evaluates/releases results or certification to qualified candidates, then collects satisfaction feedback.

Notes include checking ingredient expiry and calibrated ovens/scales; candidate health/safety orientation and the right to appeal assessment results; sanitation, readiness, equipment and incident records. Evidence includes Job Order, SOA, approved/disapproved schedule log, OR, orientation log, pre-assessment checklist, assessment records, result/certification and satisfaction survey. Assessment readiness is more than a room being free.

### 7.6 Shared Job Order Request form

The blank form photo `IMG_20261011_220636_703.jpg` shows `FM-USTP-ORO-BEU-01` in its header, while other pages use 001/01 variants. Preserve the photographed form's fields and clarify the controlled identifier rather than silently normalizing it.

Fields include Job Order number/date, client name, optional gender-preference choices, address, phone/email, requested job/service, a Laboratory Analysis turnaround field, details/items, specimen/product receipt date/time, required service date/time and four signature roles:

| Form column | Printed role |
| --- | --- |
| Filled-out by | Client |
| Assisted by | Administrative Aide |
| Verified by | Personnel In-charge |
| Approved by | BEU Manager |

Requested-service choices include Equipment Rental, Facility Rental, Hotel Accommodation, Training Center, Laboratory Analysis, BPP NC II Assessment and an additional blank choice. A listed checkbox does not on its own establish that every service is enabled in the current catalog.

## 8. Research methodology and evaluation

The manuscript describes mixed methods: stakeholder interviews and observation for existing processes, plus questionnaires for preferences, willingness to use and perceived usability. It names purposive sampling with 30 students, one facility-reservation personnel member and two administrators:33 described participants in total. This is the manuscript's sample description, not newly collected responses or evidence that all evaluation stages are complete. [C §§3.1–3.2]

It names frequency counts, percentages, availability-test success, transaction speed, booking validation, mean/frequency summaries and the System Usability Scale. The supplied appendices contain interview questions and photographs; they do not supply completed raw survey results, a final SUS score or a reproduced full scored SUS instrument. Do not generate scores or declare usability success from those photos. [C §3.2; appendices]

The admin interview guide covers product selling, approval/control, transaction issues, monitoring/records, communication, validation and accountability. Student questions cover buying/selling behavior, messaging/order/payment difficulties, booking experience and preferred integrated features. Images are described as interview evidence by the manuscript; no identities are inferred from faces.

The literature/application review compares marketplace and scheduling products and cites related campus systems. Its comparison table is the researchers' assessment, not an independently tested review of Facebook Marketplace, Calendly or Google Calendar. The reference list has 11 entries; several names cited earlier, including Martia et al., Zakariah/Jamaluddin, Abdullah et al. and Beck et al., need a manuscript bibliography check. No external paper or product claim was independently validated in this task. [C Chapter 2, §3.1 and bibliography]

## 9. Reconciliation register

| ID | Difference found | Source locations | Required clarification or treatment |
| --- | --- | --- | --- |
| C01 | Manuscript software table allows FastAPI recommendations/clustering/forecasting/sentiment; current project restricts it to chat | C software requirements; AGENTS §2 | Keep current Django ownership; revise/clarify manuscript rather than moving business services |
| C02 | Content-based recommendations versus association-rule product bundles are described in different objectives | C §§1.3, 3.4 | Document the distinct algorithms, inputs and approved scope; do not use the names interchangeably |
| C03 | Diagram actor/role labels and self-selected registration language can imply broader privileges | C users/roles, registration/use-case prose | Maintain independent seller approval and backend-enforced administrative grants |
| C04 | Function Hall capacity 30–50 versus 30–40 | B pp.11, 34 | Confirm the authoritative capacity before changing validation/catalog data |
| C05 | Photocopying/printing regular rent PHP 800 versus PHP 500 | B pp.15, 34 | Resolve the controlling rate; midyear PHP 300 agrees |
| C06 | Fat analysis PHP 644 versus PHP 1008; Ash appears in annex/scope but not main schedule | B pp.18, 34–35, 45; A laboratory scope | Confirm the lab's controlled tariff and enabled analysis list |
| C07 | BPP student fee PHP 1455 versus PHP 1445; formal table labels and annex revenue table differ | B pp.20, 27, 35, 46 |15% of1700 is255, leaving1445, but arithmetic does not authorize replacing a published fee |
| C08 | Hostel projections use PHP 250 while rental schedule/pricing analysis uses800/500 | B pp.24, 33, 43 | Treat the250 figure as a projection assumption, not a booking tariff |
| C09 | Function Hall deposit basis described generally on slide and specifically as40% of6000 in formal table | B pp.11, 34 | Confirm deposit base, discount treatment and additional-hour handling |
| C10 | “Within 48 hours before” versus full payment two days before | A hostel/function notes; B p.34 | Establish the actual cutoff and exception handling; preserve source wording meanwhile |
| C11 | Court and lease manuals both display DPM…002; Job Order identifiers use 01/001; hostel page totals differ | A source headers/form | Obtain controlled document/version identifiers; do not confuse a separate SOA form numbered002 with a Job Order variant |
| C12 | DFD process numbers in prose do not match the embedded diagram's assignments | C §3.5.4, Figure 13 | Align diagram, process descriptions and data stores in the manuscript |
| C13 | Proposed UUID ERDs, feedback relationships and chat placement are not a current schema export | C Figures 8–10 and narratives | Compare with existing models/migrations before any database change |
| C14 | Software versions and terminology need editorial verification, including CSS version `5.01` and DART `v3.116` | C Table 2 | Compare with actual manifests/lockfiles; do not treat manuscript entries as installation requirements |
| C15 | Manuscript alternates proposed/future work and completed-work tense; supplied Gantt is not an acceptance record | C Chapters1/3, Figure 7 | Make study status consistent using actual development/evaluation evidence |
| C16 | Appended legal memo includes another campus and unresolved accounting-classification questions | B pp.48–50 | Keep Oroquieta and Jasaan comments separate; obtain the appropriate accounting determination |

General venue prepayment versus later Food Analysis billing is a legitimate workflow distinction in the sources, not a reason to overwrite one procedure with another. The same applies to general internal discounts versus specialized assessment/laboratory charges.

## 10. Applying this reference to the existing project

This section maps source questions to existing code for future review; it does not claim full policy compliance or modify implementation.

| Existing file and function | Inputs and outputs | Relationship to this reference |
| --- | --- | --- |
| `backend/core/modules/facilities/mobile_services.py:13` - `active_services()` | Existing configured, nonarchived/open service resources -> catalog queryset | Determines which configured services are published, not a new list inferred from source photos |
| Same file, line20 - `serialize_service(resource)` | Existing Facility/configuration -> allowlisted fields and human-readable information | Publishes recorded pricing, turnaround, sample and assessment/lease information without using the source PDF as runtime configuration |
| Same file, lines85/90 - `service_list` / `service_detail` | Existing GET request/resource ID -> current JSON catalog | Catalog availability does not approve a sample, assessment or lease |
| `backend/core/modules/facilities/booking_workflow_views.py:118` - `detail_data(request, booking)` | Existing authorized booking/context -> record details, payment/document/inspection/signing/completion information | Review how existing records support procedural evidence; do not create new state transitions from this summary |
| `backend/core/modules/facilities/job_order_signature_views.py:76` - `owner(request, booking_id)` | Existing signed owner-session proof -> permitted booking/client or denial | Signature access is record/actor scoped; printed form roles do not grant arbitrary users signing rights |

Read flow:

```text
Current configured Facility/service records
  -> existing Django catalog/booking authorization and helpers
  -> serialized catalog or booking detail response
  -> existing Flutter screen / web view / document renderer
```

A future policy reconciliation should trace confirmed fee/version/eligibility decisions into the existing configuration and validation path, with isolated tests and audit evidence. Do not hardcode the disputed values from Section 6 into templates or mobile cards. Database relationships in Section 4 remain conceptual until compared with actual models.

Example: when investigating the BPP student rate, compare B p.20 and p.46, locate the actual configured service pricing, and inspect the serializer that displays it. Record the discrepancy without saving a changed fee. This separates source verification, stored configuration and presentation.

For overall project ownership, navigation and verified change history, use the [system overview](campushub-system-overview.md), [service configuration guide](service-configuration.md), [booking guide](booking-module-chatgpt-context.md) and [mobile services guide](mobile-services-navigation.md).

## 11. Safe review and acceptance checklist

This is a suggested read-only learning exercise and future verification plan, not a test result:

1. Open B pp.34, 45 and 46 and compare the rate rows with Section 6. Verify every cited conflicting amount against the page image, not OCR alone.
2. Open A's laboratory pages and trace request -> readiness/approval -> analysis -> SOA -> cashier/OR -> release. Compare with the BPP pay-before-assessment flow.
3. Open manuscript Figures 8–10 and identify the conceptual booking/payment/user relations. Do not execute migrations or rename current tables to match the drawing.
4. Follow `active_services -> serialize_service -> service_list/service_detail` in source. Explain why a public catalog row does not imply an approved booking, accepted sample or paid request.
5. Record unresolved questions with source ID/page or exact photo filename. Keep proposed decisions separate from accepted institutional corrections.
6. Before any later implementation change, add evidence for relevant permission, calculation, conflict, inspection, receipt, release and error-path tests using isolated fixtures. This documentation task did not perform those runtime tests.

## 12. Complete source inventory

### 12.1 Archive members

All filenames below are under the archive's `Facilities Services/` directory.

| Filename | Content reviewed |
| --- | --- |
| `IMG_20261011_205657_651.jpg` | Covered Court title/scope and first workflow page |
| `IMG_20261011_205741_425.jpg` | Court payment, inspections, refund and notes |
| `IMG_20261011_205746_944.jpg` | Repeated court continuation/notes page |
| `IMG_20261011_205757_106.jpg` | Repeated court continuation/notes page |
| `IMG_20261011_205824_024.jpg` | Court records/evidence page |
| `IMG_20261011_213043_666.jpg` | Lease purpose/scope and application steps |
| `IMG_20261011_213114_198.jpg` | Lease contract/signing and notes |
| `IMG_20261011_213115_435.jpg` | Repeated lease contract/notes page |
| `IMG_20261011_213147_855.jpg` | Lease supporting-record list |
| `IMG_20261011_213527_526.jpg` | Hostel/Function Hall first procedure page |
| `IMG_20261011_213550_428.jpg` | Hostel/Function Hall payment, use, inspection/refund and feedback steps |
| `IMG_20261011_213614_550.jpg` | Hostel/Function Hall detailed notes and evidence list |
| `IMG_20261011_215432_688.jpg` | Laboratory scope, risks, forms and initial request steps |
| `IMG_20261011_215706_017.jpg` | Laboratory approval, analysis, billing, payment/release and sample notes |
| `IMG_20261011_215753_200.jpg` | Laboratory detailed notes and records |
| `VID_20261011_215701.mp4` |3.25-second laboratory-page clip; reviewed through 1 fps frame extraction |
| `IMG_20261011_220321_334.jpg` | Assessment Center scope/risks and initial steps |
| `IMG_20261011_220343_766.jpg` | Assessment preparation, execution, results and initial notes |
| `IMG_20261011_220420_594.jpg` | Assessment readiness/orientation/result notes and records |
| `VID_20261011_220404.mp4` |1.43-second assessment-page clip; reviewed through 1 fps frame extraction |
| `IMG_20261011_220636_703.jpg` | Blank shared Job Order Request form |

The clips' readable content overlaps photographed pages and includes motion blur. Their audio tracks were subjected to a local automatic speech check, but the very short clips produced inconsistent low-confidence language/text guesses. No spoken policy requirement or verbatim audio transcript is asserted from them. Visual frame review and the clearer photographs support the procedural descriptions.

### 12.2 Policy page map

| PDF pages | Content |
| --- | --- |
|1–2 | Executive brief and prepared-by page |
|3–8 | Presentation cover, outline, rationale, objectives and summary |
|9–21 | Facility/service fee slides and photographs |
|22–27 | Cited bases, setup estimates and revenue/cost scenarios |
|28–30 | Effectivity, requested action and presentation closing |
|31–33 | Formal policy background, definitions, discount categories and hostel schedule |
|34–35 | Remaining facility/service rates and conditions |
|36–37 | Facility photographs, principles and responsible officers |
|38–39 | General conditions, commercial requirements, income management and review |
|40–41 | Stakeholders, cited bases and effectivity |
|42–46 | Annexes A–D: hostel, Function Hall, laboratory and assessment cost analysis |
|47 | Secretariat action form |
|48–50 | Legal-office observations, including separate Jasaan discussion |

### 12.3 Manuscript coverage

Chapter 1 covers background/problem/objectives/significance/scope/terms. Chapter 2 covers literature, the related-applications comparison and synthesis. Chapter 3 covers mixed methods, Agile, data gathering, current processes, proposed architecture/roles/tools, system flows, scope/timeline and conceptual design. Appendices include interview questions and photographs, followed by the bibliography.

All 19 embedded images were surveyed: logo; Agile and architecture illustrations; four flowcharts; Gantt chart; three ERD images; use-case, context and DFD images; and five interview photographs. Text extraction included 548 body/table paragraphs and the supplied header/footnote/endnote parts. Word page numbers were not used as stable source locators.

## 13. Review record and limitations

### 13.1 Original-file fingerprints

| Source | Bytes | SHA256 |
| --- | --- | --- |
| A ZIP |56834167 |`9f10e43a9acb2308f7ca40648b6d9b37a215959652f1afde71865fa8798b5a4e` |
| B PDF |14513039 |`e2abdaa4cad2a6f101d752e082ff79d27e90eb328cd11de813f6faef4fee3338` |
| C DOCX |2372348 |`1ee4dd4cd886f5723efcb437b4073c7944790140b296596ae25d2f76540f2dd7` |

### 13.2 Processing and verification

The review used read-only source access, archive/member inventory, DOCX XML/table-text extraction and embedded-image inspection, PDF text extraction plus rendered-page inspection, OCR of all 19 photographs and sampled video frames. Critical conflicting amounts were checked against larger page images. Temporary extraction/OCR/render/audio material is under ignored `scratch/source-review-20261028/`; it is not part of the final Markdown deliverable or production assets. Reader packages were isolated from CampusHub's dependency files.

OCR is not authoritative where handwriting, rotation, blur or table alignment is unclear. Source numbering/code inconsistencies are retained. Audio recognition was not reliable enough to quote. The original Word layout was not independently reflowed into a page-accurate edition; citations therefore use its sections/figure labels. Referenced laws, TESDA/FASTLAB issuances, bibliography entries, policy amendments, live database values and deployed behavior were not independently verified.

### 13.3 Change report

1. **Cause / reason:** the user requested a Markdown reference after reading the three supplied sources.
2. **Exact files changed:** `docs/campushub-source-reference.md:1` (this new reference) and the newest entry at `CAMPUSHUB_CONTEXT.md:3`. Temporary reading artifacts stay in ignored scratch storage.
3. **Changes made:** consolidated plan/design/structure/database material, institutional workflows, fees/discounts, research content, source inventories and unresolved differences with traceable locations.
4. **How it works:** readers follow source IDs and page/section/filename locators to the original evidence, then use the existing source-code/guide map for any separately authorized implementation review. This Markdown is not read by runtime pricing or approval logic.
5. **Backend / API behavior:** unchanged. No application logic, endpoint, permission, catalog or dashboard was modified.
6. **Database / migration impact:** none. No live connection, record write, migration, fee update or staff assignment was performed.
7. **Checks performed:** source completeness, filename/page/figure coverage, critical-value visual checks, Markdown structure/local links and original-file fingerprints were checked. No CampusHub runtime tests were run because this task changes documentation only.
8. **Remaining limitations:** documented disagreements require the appropriate institutional/source correction; this review does not resolve them by authority or certify policy/legal compliance, research validity, full implementation or deployment readiness.
