# PharmFEFO — Pharmacy Batch & FEFO Dispensing Management

A compliance-first inventory management web application designed for neighbourhood pharmacies to enforce First-Expiry-First-Out (FEFO) dispensing, track real-time sellable stock, and issue automated near-expiry alerts.

---

## Key Features
- **Strict FEFO Dispensing:** Automatically selects and depletes the oldest in-date batch first.
- **Zero Expired Dispense Policy:** Expired stock is isolated and strictly excluded from active/sellable stock counts.
- **Batch Tracking & Search:** Full search, column sorting, and pagination across all active batches.
- **Expiry Warnings:** Proactive alert banner highlighting any batches expiring within 30 days.
- **Role-based Authentication:** JWT-secured pharmacist registration and login.
- **Product Landing Page:** Complete overview with target audience, key capabilities, and future roadmap.

---

## Tech Stack
- **Backend:** Python 3, FastAPI, SQLite, Pydantic, Passlib (bcrypt), Python-Jose (JWT)
- **Frontend:** Vanilla JS, HTML5, Tailwind CSS (CDN)
- **Database:** SQLite (persisted locally as `pharmacy.db`)

---

## Setup & Running Locally

1. **Install Dependencies:**
   ```bash
   pip install fastapi uvicorn pydantic python-jose[cryptography] passlib[bcrypt] python-multipart