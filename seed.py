import sqlite3
import hashlib
from datetime import date, timedelta

DB_FILE = "pharmacy.db"

def seed():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Default demo user: admin / admin123
    admin_pw_hash = hashlib.sha256("admin123".encode("utf-8")).hexdigest()
    cur.execute("""
        INSERT OR IGNORE INTO users (id, username, hashed_password)
        VALUES (1, 'admin', ?)
    """, (admin_pw_hash,))

    today = date.today()
    d_expired_long = (today - timedelta(days=90)).isoformat()
    d_expired_recent = (today - timedelta(days=5)).isoformat()
    d_soon_1 = (today + timedelta(days=7)).isoformat()
    d_soon_2 = (today + timedelta(days=21)).isoformat()
    d_future_1 = (today + timedelta(days=120)).isoformat()
    d_future_2 = (today + timedelta(days=365)).isoformat()

    sample_batches = [
        # Paracetamol: Expired, near-expiry, and long-dated
        ("PARA-EXP-01", "Paracetamol 500mg", 40, d_expired_recent),
        ("PARA-SOON-02", "Paracetamol 500mg", 25, d_soon_1),
        ("PARA-LATER-03", "Paracetamol 500mg", 100, d_future_1),

        # Amoxicillin: Near-expiry and long-dated
        ("AMOX-SOON-01", "Amoxicillin 250mg", 30, d_soon_2),
        ("AMOX-SAFE-02", "Amoxicillin 250mg", 75, d_future_2),

        # Cetirizine: Fully expired (to test rejection)
        ("CET-EXP-01", "Cetirizine 10mg", 50, d_expired_long),

        # Ibuprofen: Sellable batches
        ("IBU-FRESH-01", "Ibuprofen 400mg", 60, d_future_1),
        ("IBU-FRESH-02", "Ibuprofen 400mg", 90, d_future_2),
    ]

    cur.execute("DELETE FROM batches")
    cur.execute("DELETE FROM dispense_logs")

    cur.executemany("""
        INSERT INTO batches (batch_code, medicine_name, quantity, expiry_date)
        VALUES (?, ?, ?, ?)
    """, sample_batches)

    conn.commit()
    conn.close()
    print("Database seeded successfully with demo user (admin/admin123) and sample FEFO batches!")

if __name__ == "__main__":
    seed()