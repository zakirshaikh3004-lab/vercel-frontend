from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import uuid
from jose import JWTError, jwt
from datetime import datetime, timedelta
from database import get_db, init_db, pwd_context

app = FastAPI(title="Complaint System")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT settings
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

# Models
class User(BaseModel):
    email: str
    password: str
    name: str = ""
    role: str = "student"

class Complaint(BaseModel):
    title: str
    description: str
    department_id: int
    priority: str = "medium"
    anonymous: bool = False

class Login(BaseModel):
    email: str
    password: str

# Initialize database
init_db()

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_token(email: str):
    expire = datetime.utcnow() + timedelta(hours=24)
    return jwt.encode({"email": email, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["email"]
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

# Routes
@app.post("/register")
def register(user: User):
    db = get_db()
    hashed_password = pwd_context.hash(user.password)
    
    try:
        db.execute(
            "INSERT INTO users (email, name, role, password) VALUES (?, ?, ?, ?)",
            (user.email, user.name, user.role, hashed_password)
        )
        db.commit()
        return {"message": "User created successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Email already exists")

@app.post("/login")
def login(login_data: Login):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (login_data.email,)).fetchone()
    
    if not user or not verify_password(login_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    token = create_token(user["email"])
    return {"token": token, "user": dict(user)}

@app.post("/complaints")
def create_complaint(complaint: Complaint, token: str = Depends(get_current_user)):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (token,)).fetchone()
    
    complaint_id = str(uuid.uuid4())
    user_id = None if complaint.anonymous else user["id"]
    
    db.execute(
        """INSERT INTO complaints 
        (id, title, description, department_id, priority, status, anonymous, user_id) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (complaint_id, complaint.title, complaint.description, complaint.department_id, 
         complaint.priority, "open", complaint.anonymous, user_id)
    )
    db.commit()
    
    return {"message": "Complaint submitted", "complaint_id": complaint_id}

@app.get("/complaints")
def get_complaints(token: str = Depends(get_current_user)):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (token,)).fetchone()
    
    if user["role"] == "admin":
        complaints = db.execute('''
            SELECT c.*, d.name as department_name 
            FROM complaints c 
            JOIN departments d ON c.department_id = d.id
        ''').fetchall()
    else:
        complaints = db.execute('''
            SELECT c.*, d.name as department_name 
            FROM complaints c 
            JOIN departments d ON c.department_id = d.id 
            WHERE c.user_id = ?
        ''', (user["id"],)).fetchall()
    
    return [dict(comp) for comp in complaints]

@app.get("/complaints/anonymous/{complaint_id}")
def get_anonymous_complaint(complaint_id: str):
    db = get_db()
    complaint = db.execute('''
        SELECT c.*, d.name as department_name 
        FROM complaints c 
        JOIN departments d ON c.department_id = d.id 
        WHERE c.id = ? AND c.anonymous = 1
    ''', (complaint_id,)).fetchone()
    
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    return dict(complaint)

@app.put("/complaints/{complaint_id}")
def update_status(complaint_id: str, status: dict, token: str = Depends(get_current_user)):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (token,)).fetchone()
    
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can update status")
    
    db.execute(
        "UPDATE complaints SET status = ? WHERE id = ?",
        (status["status"], complaint_id)
    )
    db.commit()
    
    return {"message": "Status updated"}

@app.get("/departments")
def get_departments():
    db = get_db()
    departments = db.execute("SELECT * FROM departments").fetchall()
    return [dict(dept) for dept in departments]

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
