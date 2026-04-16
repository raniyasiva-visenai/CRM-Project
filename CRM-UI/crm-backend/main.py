from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from typing import Optional, List
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# --- CONFIG ---
SECRET_KEY = "iris_secret_key_change_me"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Load Database Config from main project
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'CRM')))
from config.db import DB_CONFIG

app = FastAPI(title="CRM Admin API")

# Enable CORS for React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str
    role: str

# --- DB HELPERS ---
def get_db():
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()

# --- AUTH ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # MOCK AUTH for now - In production, check against 'users' table
    if form_data.username == "admin" and form_data.password == "Raniya@123":
        access_token = create_access_token(data={"sub": form_data.username, "role": "admin"})
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(status_code=400, detail="Incorrect username or password")

# --- DASHBOARD ENDPOINTS ---
@app.get("/stats")
def get_dashboard_stats():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Lead Counts
    cur.execute("SELECT status, COUNT(*) as count FROM leads GROUP BY status")
    lead_stats = cur.fetchall()
    
    # Builder Success/Failure
    cur.execute("""
        SELECT status, COUNT(*) as count 
        FROM lead_crm_distribution 
        GROUP BY status
    """)
    dist_stats = cur.fetchall()
    
    # Recent Failures (Alerts)
    cur.execute("""
        SELECT b.builder_name, l.first_name, d.status, d.submitted_at, d.crm_response
        FROM lead_crm_distribution d
        JOIN builders b ON d.builder_id = b.builder_id
        JOIN leads l ON d.lead_id = l.lead_id
        ORDER BY d.submitted_at DESC LIMIT 10
    """)
    recent = cur.fetchall()
    
    conn.close()
    return {
        "leads": lead_stats,
        "distribution": dist_stats,
        "recent_activity": recent
    }

@app.get("/leads")
def get_leads(limit: int = 50):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT 
            l.*,
            (SELECT string_agg(DISTINCT b.builder_name, ', ') 
             FROM lead_crm_distribution d 
             JOIN builders b ON d.builder_id = b.builder_id 
             WHERE d.lead_id = l.lead_id) as selected_builders,
            (SELECT string_agg(DISTINCT b.builder_name, ', ') 
             FROM lead_crm_distribution d 
             JOIN builders b ON d.builder_id = b.builder_id 
             WHERE d.lead_id = l.lead_id AND d.status = 'SUCCESS') as success_builders,
            (SELECT string_agg(DISTINCT b.builder_name, ', ') 
             FROM lead_crm_distribution d 
             JOIN builders b ON d.builder_id = b.builder_id 
             WHERE d.lead_id = l.lead_id AND d.status IN ('FAILED', 'DUPLICATE')) as failed_builders
        FROM leads l
        ORDER BY l.created_at DESC 
        LIMIT %s
    """, (limit,))
    leads = cur.fetchall()
    conn.close()
    return leads

@app.get("/builders")
def get_builders_status():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT b.builder_name, b.crm_type, 
               COUNT(CASE WHEN d.status = 'SUCCESS' THEN 1 END) as success,
               COUNT(CASE WHEN d.status = 'FAILED' THEN 1 END) as failures,
               COUNT(CASE WHEN d.status = 'DUPLICATE' THEN 1 END) as duplicates
        FROM builders b
        LEFT JOIN lead_crm_distribution d ON b.builder_id = d.builder_id
        GROUP BY b.builder_id, b.builder_name, b.crm_type
        ORDER BY success DESC
    """)
    builders = cur.fetchall()
    conn.close()
    return builders

@app.get("/alerts")
def get_alerts():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT an.alert_id, an.alert_type, an.sent_time, 
               b.builder_name, l.first_name, l.last_name, l.mobile, 
               d.crm_response, d.attempt_count
        FROM alert_notifications an
        JOIN leads l ON an.lead_id = l.lead_id
        JOIN builders b ON an.builder_id = b.builder_id
        JOIN lead_crm_distribution d ON an.distribution_id = d.distribution_id
        ORDER BY an.sent_time DESC LIMIT 50
    """)
    alerts = cur.fetchall()
    conn.close()
    return alerts

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
