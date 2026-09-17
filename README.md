# PharmFEFO — Pharmacy Batch & FEFO Dispensing Management

A compliance-first inventory management web application designed for neighbourhood pharmacies to enforce First-Expiry-First-Out (FEFO) dispensing, track real-time sellable stock, and issue automated near-expiry alerts.

---

## Key Features
- **Strict FEFO Dispensing:** Automatically selects and depletes the oldest in-date batch first.
- **Zero Expired Dispense Policy:** Expired stock is isolated and strictly excluded from active/sellable stock counts.
- **Instant In-Date Checker:** Quick search answering questions like *"Do we have Paracetamol in date?"*.
- **Audit Logging:** Live audit history tracking batch-level stock deductions.
- **Expiry Warnings:** Proactive alert banner highlighting any batches expiring within 30 days.
- **Batch Tracking & Search:** Full search, column sorting, and pagination across all active batches.
- **Role-based Authentication:** Pharmacist registration and login.
- **Product Landing Page:** Complete overview with target audience, key capabilities, and future roadmap.

---

## Tech Stack
- **Backend:** Python 3, FastAPI, SQLite, Pydantic, Python-Jose (JWT)
- **Frontend:** Vanilla JS, HTML5, Tailwind CSS (CDN)
- **Database:** SQLite (persisted locally as `pharmacy.db`)

---

## Setup & Running Locally

1. **Install Dependencies:**
   ```bash
   pip install fastapi uvicorn pydantic python-jose[cryptography] python-multipart