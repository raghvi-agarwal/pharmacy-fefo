import sqlite3
import hashlib
from datetime import date, datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from jose import JWTError, jwt

SECRET_KEY = "pharma-secret-builder-round-key"
ALGORITHM = "HS256"
DB_FILE = "pharmacy.db"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
app = FastAPI(title="PharmFEFO")

# --- DATABASE SETUP ---
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_code TEXT NOT NULL,
            medicine_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            expiry_date DATE NOT NULL
        );
        CREATE TABLE IF NOT EXISTS dispense_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_code TEXT NOT NULL,
            medicine_name TEXT NOT NULL,
            units_dispensed INTEGER NOT NULL,
            dispensed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
init_db()

# --- AUTH UTILS ---
def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()

def verify_pw(pw: str, hashed: str) -> bool:
    return hash_pw(pw) == hashed

def create_token(data: dict):
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() + timedelta(hours=8)})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# --- SCHEMAS ---
class UserAuth(BaseModel):
    username: str
    password: str

class BatchCreate(BaseModel):
    batch_code: str
    medicine_name: str
    quantity: int
    expiry_date: str  # YYYY-MM-DD

class DispenseRequest(BaseModel):
    medicine_name: str
    quantity: int

# --- AUTH ENDPOINTS ---
@app.post("/api/auth/register")
def register(user: UserAuth):
    with get_db() as conn:
        try:
            conn.execute(
                "INSERT INTO users (username, hashed_password) VALUES (?, ?)", 
                (user.username.strip(), hash_pw(user.password))
            )
            conn.commit()
            return {"message": "User registered successfully"}
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Username already registered")

@app.post("/api/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    with get_db() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", 
            (form_data.username.strip(),)
        ).fetchone()
        if not user or not verify_pw(form_data.password, user["hashed_password"]):
            raise HTTPException(status_code=400, detail="Invalid credentials")
        token = create_token({"sub": user["username"]})
        return {"access_token": token, "token_type": "bearer"}

# --- INVENTORY & FEFO ENDPOINTS ---
@app.post("/api/batches")
def add_batch(batch: BatchCreate, user: str = Depends(get_current_user)):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO batches (batch_code, medicine_name, quantity, expiry_date) VALUES (?, ?, ?, ?)",
            (batch.batch_code.strip(), batch.medicine_name.strip(), batch.quantity, batch.expiry_date)
        )
        conn.commit()
    return {"message": "Batch added successfully"}

@app.get("/api/batches")
def list_batches(
    search: str = "",
    sort_by: str = "expiry_date",
    order: str = "asc",
    page: int = 1,
    limit: int = 10,
    user: str = Depends(get_current_user)
):
    valid_sorts = {"expiry_date", "medicine_name", "quantity"}
    sort_column = sort_by if sort_by in valid_sorts else "expiry_date"
    sort_dir = "DESC" if order.lower() == "desc" else "ASC"
    offset = (page - 1) * limit

    with get_db() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM batches WHERE medicine_name LIKE ?", (f"%{search}%",)
        ).fetchone()[0]
        
        query = f"""
            SELECT * FROM batches 
            WHERE medicine_name LIKE ? 
            ORDER BY {sort_column} {sort_dir} 
            LIMIT ? OFFSET ?
        """
        rows = conn.execute(query, (f"%{search}%", limit, offset)).fetchall()
        
    return {
        "items": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }

@app.get("/api/inventory/summary")
def get_inventory_summary(search: str = "", user: str = Depends(get_current_user)):
    today_str = date.today().isoformat()
    with get_db() as conn:
        rows = conn.execute("""
            SELECT 
                medicine_name,
                SUM(CASE WHEN expiry_date > ? THEN quantity ELSE 0 END) as sellable_stock,
                SUM(CASE WHEN expiry_date <= ? THEN quantity ELSE 0 END) as expired_stock
            FROM batches
            WHERE medicine_name LIKE ?
            GROUP BY medicine_name
        """, (today_str, today_str, f"%{search}%")).fetchall()
    return [dict(r) for r in rows]

@app.post("/api/dispense")
def dispense_medicine(req: DispenseRequest, user: str = Depends(get_current_user)):
    today_str = date.today().isoformat()
    with get_db() as conn:
        total_sellable = conn.execute("""
            SELECT SUM(quantity) FROM batches 
            WHERE medicine_name = ? AND expiry_date > ? AND quantity > 0
        """, (req.medicine_name.strip(), today_str)).fetchone()[0] or 0

        if total_sellable < req.quantity:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient in-date stock. Available: {total_sellable}, Requested: {req.quantity}"
            )

        # FEFO Ordering: Earliest unexpired batches first
        batches = conn.execute("""
            SELECT id, batch_code, quantity, expiry_date FROM batches
            WHERE medicine_name = ? AND expiry_date > ? AND quantity > 0
            ORDER BY expiry_date ASC
        """, (req.medicine_name.strip(), today_str)).fetchall()

        needed = req.quantity
        breakdown = []

        for b in batches:
            b_id, b_code, b_qty, b_exp = b["id"], b["batch_code"], b["quantity"], b["expiry_date"]
            take = min(b_qty, needed)
            needed -= take
            
            conn.execute("UPDATE batches SET quantity = quantity - ? WHERE id = ?", (take, b_id))
            conn.execute(
                "INSERT INTO dispense_logs (batch_code, medicine_name, units_dispensed) VALUES (?, ?, ?)",
                (b_code, req.medicine_name.strip(), take)
            )
            breakdown.append({"batch_code": b_code, "units": take, "expiry": b_exp})

            if needed == 0:
                break

        conn.commit()
    return {"message": "Dispensed successfully", "breakdown": breakdown}

@app.get("/api/alerts/expiring-soon")
def get_alerts(days: int = 30, user: str = Depends(get_current_user)):
    today = date.today()
    cutoff = (today + timedelta(days=days)).isoformat()
    today_str = today.isoformat()
    with get_db() as conn:
        rows = conn.execute("""
            SELECT batch_code, medicine_name, quantity, expiry_date 
            FROM batches 
            WHERE expiry_date > ? AND expiry_date <= ? AND quantity > 0
            ORDER BY expiry_date ASC
        """, (today_str, cutoff)).fetchall()
    return [dict(r) for r in rows]

@app.get("/api/dispense/logs")
def get_dispense_logs(limit: int = 10, user: str = Depends(get_current_user)):
    with get_db() as conn:
        rows = conn.execute("""
            SELECT id, batch_code, medicine_name, units_dispensed, dispensed_at
            FROM dispense_logs
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()
    return [dict(r) for r in rows]

# Static frontend mount
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_index():
    return FileResponse("static/index.html")