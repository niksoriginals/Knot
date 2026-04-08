from flask import Flask, request, jsonify, session
from flask_cors import CORS
from datetime import timedelta
from functools import wraps
import sqlite3
import os
import datetime

app = Flask(__name__)

# 1. CORS Configuration
CORS(
    app,
    supports_credentials=True,
    origins=[
        "https://knot.niksoriginals.in",
        "https://admin.knot.niksoriginals.in",
        "https://info.knot.niksoriginals.in",
    ]
)

# 2. App Config
app.secret_key = os.getenv("FLASK_SECRET", "NISO_SECRET_KEY_2026")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="None",
    SESSION_COOKIE_SECURE=True,
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8)
)

ADMIN_USER = "admin"
ADMIN_PASS_HASH = "admin"
DB_PATH = "/data/knot.db" 

# 3. Database Helpers
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    # Users
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
        role TEXT CHECK(role IN ('student', 'admin')) DEFAULT 'student',
        department TEXT)''')
    # Resources
    conn.execute('''CREATE TABLE IF NOT EXISTS resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, type TEXT NOT NULL,
        status TEXT DEFAULT 'Available', needs_approval BOOLEAN DEFAULT 0)''')
    # Bookings
    conn.execute('''CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, resource_id INTEGER,
        start_time DATETIME, end_time DATETIME, status TEXT DEFAULT 'Pending',
        FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(resource_id) REFERENCES resources(id))''')
    # Marketplace
    conn.execute('''CREATE TABLE IF NOT EXISTS marketplace (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, title TEXT,
        description TEXT, type TEXT CHECK(type IN ('Lost', 'Found', 'Sell', 'Trade')),
        image_url TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

# 4. Security Decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin"):
            return jsonify({"error": "Unauthorized: Admin login required"}), 403
        return f(*args, **kwargs)
    return decorated_function

# --- AUTH ROUTES ---

@app.route("/admin/login", methods=["POST"])
def admin_login():
    data = request.json or {}
    if data.get("username") == ADMIN_USER and data.get("password") == ADMIN_PASS_HASH:
        session["admin"] = True
        session.permanent = True
        return jsonify({"success": True})
    return jsonify({"error": "invalid credentials"}), 401

@app.route("/admin/me", methods=["GET"])
def admin_me():
    return jsonify({"logged_in": session.get("admin", False)})

@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.pop("admin", None)
    return jsonify({"success": True})

# --- ADMIN RESOURCE & BOOKING ROUTES ---

@app.route("/admin/bookings/pending", methods=["GET"])
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

@app.route("/admin/bookings/action", methods=["POST"])
@admin_required
def booking_action():
    data = request.json
    conn = get_db()
    conn.execute("UPDATE bookings SET status = ? WHERE id = ?", (data.get("status"), data.get("id")))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/admin/resources/add", methods=["POST"])
@admin_required
def add_resource():
    data = request.json
    conn = get_db()
    conn.execute("INSERT INTO resources (name, type, needs_approval) VALUES (?, ?, ?)",
                 (data['name'], data['type'], data.get('needs_approval', 0)))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

# --- MARKETPLACE MODERATION ---

@app.route("/admin/marketplace/items", methods=["GET"])
def get_admin_market():
    conn = get_db()
    items = conn.execute("SELECT * FROM marketplace ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify([dict(i) for i in items])

@app.route("/admin/marketplace/delete", methods=["POST"])
@admin_required
def delete_item():
    item_id = request.json.get("id")
    conn = get_db()
    conn.execute("DELETE FROM marketplace WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

# --- ANALYTICS ROUTE ---

@app.route("/admin/analytics", methods=["GET"])
def get_analytics():
    conn = get_db()
    # Resource popularitiy
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

# --- START SERVER ---

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)