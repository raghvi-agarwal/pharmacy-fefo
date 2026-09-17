
# AI Assistance Log — PharmFEFO Hackathon

This log documents all prompts, architectural decisions, implementation steps, and troubleshooting sessions conducted with AI assistance during the 2.5-hour hackathon build.

---

## 1. Project Initialization & Architecture Setup

### User Prompt
Build a Pharmacy Inventory and Automated FEFO (First-Expiry-First-Out) Dispensing System for a 2.5-hour hackathon. Stack: FastAPI, SQLite, Vanilla JS/Tailwind CSS frontend.

### AI Design & Guidance
- **Database Architecture:** Designed relational SQLite schema with `users`, `batches`, `dispense_logs`, and `outbox` tables.
- **Authentication:** Standard OAuth2 password bearer flow with SHA-256 password hashing and JWT access tokens.
- **FEFO Logic:** Dispensing queries active, non-expired batches ordered strictly by `expiry_date ASC`, decrementing batch quantities iteratively until the order quantity is fulfilled.
- **Initial File Structure:**
  - `main.py`: FastAPI server, database connection handlers, authentication endpoints, FEFO dispensing routes.
  - `seed.py`: Automated demo data populating initial batches (including valid, expiring soon, and already expired items) and a default `admin` user.
  - `static/index.html`: Responsive Tailwind CSS single-page interface for login, inventory metrics, stock table, and manual FEFO dispensing.
  - `README.md` & `REASONING.md`: Technical documentation, setup guide, and architectural decision logs.

---

## 2. Core Feature Implementation

### Core Workflows Established
1. **Batch Tracking:** Adding and viewing batches with unique batch codes, medicine names, stock quantities, and ISO expiry dates.
2. **FEFO Inventory Aggregation:** `GET /api/inventory/summary` splits inventory into sellable versus expired stock based on the current date.
3. **Automated Batch Deduction:** `/api/dispense` enforces inventory verification, validates available stock, deducts iteratively across multiple batches if necessary, and logs transactions to `dispense_logs`.

---

## 3. Hackathon Twists Implementation

### Level 1 — Twist T2 (Automation: Scheduled/Clock Job)
- **Requirement:** A daily job that flags batches expiring within 7 days and quarantines expired ones, reporting counts. Graded via `POST /clock`.
- **Implementation:**
  - Added `POST /clock` in `main.py`.
  - Executes SQL queries calculating current date thresholds (`today` and `today + 7 days`).
  - Sets `status = 'QUARANTINED'` for all records where `expiry_date <= today`.
  - Aggregates counts of active batches expiring within the 7-day window.
  - Returns `{"flagged_expiring_soon": count, "quarantined_today": count}`.

### Level 2 — Twist T4 (Messy Data Ingestion & Sanitization)
- **Requirement:** Import messy batch lists containing null values, quantities like `'10 units'`, non-standard date formats (`dd/mm/yyyy` vs ISO), and duplicate batch rows, returning `{ imported, deduped, rejected }`. Graded via `POST /api/batches/import`.
- **Implementation:**
  - Added `POST /api/batches/import` accepting a raw JSON array.
  - Sanitizes `quantity` by stripping non-numeric substrings like `'units'`.
  - Parses dates supporting both `dd/mm/yyyy` and `YYYY-MM-DD` formats, converting them into standard ISO strings.
  - Validates required fields against `None` / empty values (increments `rejected` counter on missing data or invalid conversions).
  - Queries `batches` table for existing `batch_code` entries to prevent duplicates (increments `deduped` counter).
  - Inserts valid sanitized records with default `status = 'ACTIVE'` (increments `imported` counter).

### Level 3 — Twist T1 (Notification Integration: Low-Stock Outbox)
- **Requirement:** Trigger a re-order alert when in-date stock for a medicine drops below a defined safety threshold. Graded via `GET /outbox`.
- **Implementation:**
  - Added `outbox` table: `id`, `medicine_name`, `message`, `created_at`.
  - Integrated safety buffer check (`LOW_STOCK_THRESHOLD = 20`) inside `/api/dispense`.
  - When remaining sellable stock falls below the threshold post-dispensing, inserts a notification record into `outbox`.
  - Added `GET /outbox` returning pending re-order alerts formatted as JSON dictionaries.

---

## 4. Troubleshooting, Port Configuration & Verification

### Database Migration & File Locks
- **Issue:** Encountered `sqlite3.OperationalError: no such table: users` after resetting `pharmacy.db` to accommodate new schema columns.
- **Resolution:** Executed `python -c "import main"` to invoke `init_db()` and generate clean tables before executing `python seed.py`.
- **Issue:** Windows port conflict `[WinError 10048] only one usage of each socket address is normally permitted` when running Uvicorn.
- **Resolution:** Ran PowerShell command `Stop-Process -Name python -Force` to clear zombie processes and bound the server cleanly on port 8080.

### Environment & Routing Clarifications
- **Issue:** Loading frontend via port 5500 (Live Server) resulted in `Failed to connect to backend server`.
- **Resolution:** Clarified that Live Server cannot proxy FastAPI routes. Pointed browser directly to `http://127.0.0.1:8080`, allowing FastAPI's static mount to serve `index.html` while providing immediate API access.
- **Curl Parsing Nuance:** Identified that PowerShell strips unescaped double quotes inside single quotes during inline curl requests; verified that raw Python grading requests send well-formed JSON natively.

---

## 5. Verification & Submission

- Verified `POST /clock` returned `{"flagged_expiring_soon": 1, "quarantined_today": 2}` against seeded data.
- Verified `GET /outbox` schema and integration.
- Committed all application code, database seeds, frontend assets, reasoning documents, and AI logs to GitHub.