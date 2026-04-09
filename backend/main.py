from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_mail import Mail, Message
from datetime import timedelta, datetime
from functools import wraps
import sqlite3
import os
import random

app = Flask(__name__)
CORS(app, 
     supports_credentials=True, 
     origins=[
         "https://knot.niksoriginals.in",
         "https://admin.knot.niksoriginals.in",
         "https://info.knot.niksoriginals.in"
     ],
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "OPTIONS"])


# --- 1. CONFIGURATION ---
app.secret_key = os.getenv("FLASK_SECRET", "NISO_SECRET_KEY_2026")

app.config.update(
    # Flask-Mail Settings
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv("MAIL_USER", "niksoriginals@gmail.com"), 
    MAIL_PASSWORD=os.getenv("MAIL_PASS", ""), 
    
    # Session Settings
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="None",
    SESSION_COOKIE_SECURE=True,
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8)
)

mail = Mail(app)



ADMIN_USER = "admin"
ADMIN_PASS_HASH = "admin" 

DB_PATH = "/data/nofy.db"

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, email TEXT UNIQUE NOT NULL,
        role TEXT CHECK(role IN ('student', 'admin')) DEFAULT 'student',
        department TEXT)''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS otps (
        email TEXT PRIMARY KEY,
        otp_code TEXT NOT NULL,
        expiry DATETIME NOT NULL)''')

    conn.execute('''CREATE TABLE IF NOT EXISTS resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, type TEXT NOT NULL,
        status TEXT DEFAULT 'Available', needs_approval BOOLEAN DEFAULT 0)''')

    conn.execute('''CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, resource_id INTEGER,
        start_time DATETIME, end_time DATETIME, status TEXT DEFAULT 'Pending',
        FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(resource_id) REFERENCES resources(id))''')

    conn.execute('''CREATE TABLE IF NOT EXISTS marketplace (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, title TEXT,
        description TEXT, type TEXT CHECK(type IN ('Lost', 'Found', 'Sell', 'Trade')),
        image_url TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    conn.commit()
    conn.close()

# --- 3. SECURITY DECORATORS ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin"):
            return jsonify({"error": "Unauthorized: Admin login required"}), 403
        return f(*args, **kwargs)
    return decorated_function

# --- 4. AUTH ROUTES (OTP & ADMIN) ---
@app.route("/")
def home():
    return "✅ Knot is Running"

@app.route("/auth/send-otp", methods=["POST"])
def send_otp():
    print(f"--- [LOG START] send_otp for: {request.json.get('email')} ---")
    
    data = request.json or {}
    email = data.get("email")
    
    if not email or not email.endswith("@its.edu.in"):
        print(f"!!! [ERROR] Invalid Email Domain: {email}")
        return jsonify({"error": "Chup"}), 400

    otp = str(random.randint(100000, 999999))
    expiry = (datetime.now() + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')

    try:
        print(">>> [STEP 1] Connecting to Database...")
        conn = get_db()
        
        print(">>> [STEP 2] Inserting OTP into DB...")
        conn.execute("INSERT OR REPLACE INTO otps (email, otp_code, expiry) VALUES (?, ?, ?)", 
                     (email, otp, expiry))
        conn.commit()
        conn.close()
        print("<<< [SUCCESS] DB Updated.")
        
    except Exception as db_e:
        print(f"!!! [DB ERROR] {str(db_e)}")
        return jsonify({"error": "Database error", "details": str(db_e)}), 500

    try:
        print(f">>> [STEP 3] Sending Email via {app.config['MAIL_SERVER']}...")
        msg = Message('KNOT - Your Secure Login Code', 
                      sender=app.config['MAIL_USERNAME'], 
                      recipients=[email])
        msg.body = f"Your OTP for KNOT Login is: {otp}. It will expire in 5 minutes."
        
        # Ye line 524 timeout ka sabse bada reason ho sakti hai
        mail.send(msg) 
        
        print("<<< [SUCCESS] Email Sent.")
        return jsonify({"success": True, "message": "OTP sent successfully"})
    
    except Exception as e:
        print(f"!!! [MAIL ERROR] {str(e)}")
        return jsonify({"error": "Failed to send email", "details": str(e)}), 500
    
    finally:
        print("--- [LOG END] ---")

@app.route("/auth/verify-otp", methods=["POST"])
def verify_otp():
    data = request.json or {}
    email = data.get("email")
    user_otp = data.get("otp")

    # --- DEMO BYPASS ---
    if user_otp == "123456":
        session["user_email"] = email
        session.permanent = True
        return jsonify({"success": True, "user": email})

    conn = get_db()
    res = conn.execute("SELECT otp_code, expiry FROM otps WHERE email = ?", (email,)).fetchone()
    conn.close()

    if res:
        expiry_dt = datetime.strptime(res['expiry'], '%Y-%m-%d %H:%M:%S')
        if res['otp_code'] == user_otp and datetime.now() < expiry_dt:
            session["user_email"] = email
            session.permanent = True
            return jsonify({"success": True, "user": email})
    
    return jsonify({"error": "Invalid or expired OTP"}), 401

@app.route("/admin/login", methods=["POST"])
def admin_login():
    data = request.json or {}
    if data.get("username") == ADMIN_USER and data.get("password") == ADMIN_PASS_HASH:
        session["admin"] = True
        session.permanent = True
        return jsonify({"success": True})
    return jsonify({"error": "Invalid admin credentials"}), 401

@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.pop("admin", None)
    return jsonify({"success": True})

# --- 5. ADMIN & ANALYTICS ROUTES ---

@app.route("/admin/bookings/pending", methods=["GET"])
@admin_required
def get_pending_bookings():
    conn = get_db()
    query = '''
        SELECT b.id, u.name as user_name, r.name as resource_name, b.start_time, b.end_time, b.status
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        JOIN resources r ON b.resource_id = r.id
        WHERE b.status = 'Pending'
    '''
    rows = conn.execute(query).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route("/admin/analytics", methods=["GET"])
@admin_required
def get_analytics():
    conn = get_db()
    usage = conn.execute('''
        SELECT r.name, COUNT(b.id) as count 
        FROM resources r 
        LEFT JOIN bookings b ON r.id = b.resource_id 
        GROUP BY r.id
    ''').fetchall()
    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    
    return jsonify({
        "resource_usage": [dict(s) for s in usage],
        "total_users": total_users,
        "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

# --- 6. START SERVER ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)