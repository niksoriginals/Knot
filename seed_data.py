import sqlite3
import os

DB_CANDIDATES = ["nofy.db", "backend/nofy.db", "/data/knot.db"]

def get_db_path():
    for path in DB_CANDIDATES:
        if os.path.exists(path):
            return path
    # Default to nofy.db in backend or root
    return "backend/nofy.db" if os.path.isdir("backend") else "nofy.db"

def seed():
    db_path = get_db_path()
    print(f">> Seeding Indian College Sample Data into: {db_path}...")
    
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA foreign_keys = ON;')
    conn.row_factory = sqlite3.Row

    # Ensure tables exist
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, email TEXT UNIQUE NOT NULL,
        role TEXT CHECK(role IN ('student', 'admin','hod', 'dean')) DEFAULT 'student',
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

    # 1. SAMPLE USERS
    sample_users = [
        ("Nikhil Yadav (Lead Dev)", "nikso@its.edu.in", "admin", "Computer Science & Engg"),
        ("System Administrator", "admin@its.edu.in", "admin", "Campus IT & Infrastructure"),
        ("Dr. Sanjay Mishra", "sanjay.mishra@its.edu.in", "hod", "Computer Science & Engg"),
        ("Prof. Rajesh Kumar", "rajesh.dean@its.edu.in", "dean", "Academic Affairs"),
        ("Aarav Sharma", "aarav.sharma_cse25@its.edu.in", "student", "CSE - 3rd Year"),
        ("Priya Singh", "priya.singh_it24@its.edu.in", "student", "Information Tech - 4th Year"),
        ("Rohit Verma", "rohit.verma_ece26@its.edu.in", "student", "Electronics & Comm - 2nd Year"),
        ("Ananya Gupta", "ananya.gupta_me25@its.edu.in", "student", "Mechanical - 3rd Year")
    ]

    for name, email, role, dept in sample_users:
        conn.execute('''
            INSERT INTO users (name, email, role, department) 
            VALUES (?, ?, ?, ?)
            ON CONFLICT(email) DO UPDATE SET name=excluded.name, role=excluded.role, department=excluded.department
        ''', (name, email, role, dept))

    # 2. SAMPLE RESOURCES
    sample_resources = [
        ("Dr. APJ Abdul Kalam Auditorium", "Auditorium", "Available", 1),
        ("Chanakya Seminar Hall (Block B)", "Seminar Hall", "Available", 1),
        ("Turing AI & High-Performance Lab", "Computer Lab", "Available", 0),
        ("Robotics & IoT Innovation FabLab", "Innovation Lab", "Available", 1),
        ("Main Campus Cricket & Football Ground", "Sports Ground", "Available", 1),
        ("Central Library Discussion Room 3", "Study Room", "Available", 0),
        ("VLSI & Embedded Systems Design Lab", "Electronics Lab", "Available", 0),
        ("Mechanical CAD/CAM 3D Printing Studio", "Workshop", "Available", 1),
        ("Campus Open-Air Amphitheatre", "Cultural Arena", "Available", 1),
        ("Badminton Indoor Court 1 (Sports Block)", "Sports", "Available", 0)
    ]

    res_count = conn.execute("SELECT COUNT(*) as cnt FROM resources").fetchone()['cnt']
    if res_count == 0:
        conn.executemany("INSERT INTO resources (name, type, status, needs_approval) VALUES (?, ?, ?, ?)", sample_resources)

    # Fetch User & Resource IDs for references
    user_nikso = conn.execute("SELECT id FROM users WHERE email='nikso@its.edu.in'").fetchone()['id']
    user_aarav = conn.execute("SELECT id FROM users WHERE email='aarav.sharma_cse25@its.edu.in'").fetchone()['id']
    user_priya = conn.execute("SELECT id FROM users WHERE email='priya.singh_it24@its.edu.in'").fetchone()['id']
    user_rohit = conn.execute("SELECT id FROM users WHERE email='rohit.verma_ece26@its.edu.in'").fetchone()['id']

    res_audi = conn.execute("SELECT id FROM resources WHERE name LIKE '%Auditorium%'").fetchone()['id']
    res_lab = conn.execute("SELECT id FROM resources WHERE name LIKE '%Turing%'").fetchone()['id']
    res_iot = conn.execute("SELECT id FROM resources WHERE name LIKE '%Robotics%'").fetchone()['id']

    # 3. SAMPLE MARKETPLACE (Lost, Found, Sell, Trade)
    sample_market = [
        (user_aarav, "Boat Airdopes 141 (Black Case)", "Bhul gaya Nescafe canteen ke bench pe lunch break ke time (1:30 PM). Black silicon cover laga hai. Agar kisi ko mile toh please contact karo!", "Lost"),
        (user_rohit, "Blue Fastrack Bag with Maths-3 Notes", "Room 204 me desk 3 pe reh gaya tha after lecture. Register me important internal assignments hain, please return kar do.", "Lost"),
        (user_priya, "Casio Scientific Calculator fx-991ES Plus", "Physics Lab (Block A) me 3rd bench pe mila hai. Claim karne ke liye apna roll number aur serial number verify karein.", "Found"),
        (user_nikso, "Titan Neo Silver Metal Watch", "Found on 2nd floor Block C washroom washbasin around 4 PM. Contact with proof of purchase.", "Found"),
        (user_priya, "1st Year Engineering Books + Mini Drafter Combo", "Engineering Physics, Basic Electrical, Maths-1 by HK Dass + Omega mini drafter with sheet holder. All in mint condition. ₹450 only.", "Sell"),
        (user_aarav, "Casio fx-991CW (Latest ClassWiz Calculator)", "Bought last semester, mint condition, original box and warranty card available. Upgrading for GATE prep. ₹750.", "Sell"),
        (user_rohit, "Let Us C (Yashavant Kanetkar) + Data Structures Book", "Want to trade for Core Java Volume 1 or Python for Data Analysis book for semester 4.", "Trade"),
        (user_nikso, "Kadence Frontier Acoustic Guitar 39-inch", "Hostel room me space issue hai. String condition new, with water-resistant bag, capo and plectrums. ₹1,800.", "Sell")
    ]

    market_count = conn.execute("SELECT COUNT(*) as cnt FROM marketplace").fetchone()['cnt']
    if market_count == 0:
        conn.executemany("INSERT INTO marketplace (user_id, title, description, type) VALUES (?, ?, ?, ?)", sample_market)

    # 4. SAMPLE BOOKINGS (for Admin Approvals and Analytics)
    sample_bookings = [
        (user_aarav, res_audi, "2026-10-24 10:00", "2026-10-24 14:00", "Pending"),
        (user_rohit, res_iot, "2026-10-25 14:00", "2026-10-25 17:00", "Pending"),
        (user_priya, res_lab, "2026-10-23 09:00", "2026-10-23 12:00", "Confirmed")
    ]

    booking_count = conn.execute("SELECT COUNT(*) as cnt FROM bookings").fetchone()['cnt']
    if booking_count == 0:
        conn.executemany("INSERT INTO bookings (user_id, resource_id, start_time, end_time, status) VALUES (?, ?, ?, ?, ?)", sample_bookings)

    conn.commit()
    conn.close()
    print("[SUCCESS] Indian College Sample Data successfully seeded!")

if __name__ == "__main__":
    seed()
