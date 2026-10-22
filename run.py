import os
import sys
import time
import subprocess
import threading
import webbrowser
import socketserver
import http.server
from urllib.parse import urlparse

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
REQUIREMENTS_FILE = os.path.join(BACKEND_DIR, "requirements.txt")

FRONTEND_PORT = 3000
BACKEND_PORT = 5000

def check_and_install_requirements():
    """Ensure all required Python packages are installed."""
    print("=" * 60)
    print("🚀 KNOT ECOSYSTEM - INITIALIZING")
    print("=" * 60)
    print("📦 [1/3] Checking dependencies...")

    required_modules = ["flask", "requests", "flask_cors", "resend"]
    missing = []
    for mod in required_modules:
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)

    if missing:
        print(f"⚠️  Missing packages detected: {', '.join(missing)}")
        print("⬇️  Installing requirements from backend/requirements.txt...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", REQUIREMENTS_FILE
            ])
            print("✅ Dependencies successfully installed!")
        except Exception as e:
            print(f"❌ Error installing dependencies: {e}")
            print(f"👉 Please run manually: pip install -r backend/requirements.txt")
            sys.exit(1)
    else:
        print("✅ All dependencies are already installed.")

class CleanURLHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        clean_path = parsed.path.rstrip("/")
        query = ("?" + parsed.query) if parsed.query else ""

        # Root request maps to index.html
        if not clean_path or clean_path == "":
            self.path = "/index.html" + query
            return super().do_GET()

        # Check if the requested clean path maps to an existing .html file (e.g. /login -> /login.html)
        rel_name = clean_path.lstrip("/")
        candidate_file = os.path.join(FRONTEND_DIR, rel_name + ".html")
        if os.path.isfile(candidate_file):
            self.path = "/" + rel_name + ".html" + query

        return super().do_GET()

    def log_message(self, format, *args):
        # Keep terminal clean; uncomment if request-level logs are desired
        pass

def start_frontend_server():
    """Run the frontend HTTP server with clean URL support."""
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("", FRONTEND_PORT), CleanURLHandler) as httpd:
            httpd.serve_forever()
    except Exception as e:
        print(f"❌ Frontend server error: {e}")

def main():
    check_and_install_requirements()

    print("\n🌐 [2/3] Starting Frontend Server (Port 3000)...")
    frontend_thread = threading.Thread(target=start_frontend_server, daemon=True)
    frontend_thread.start()

    print("⚙️  [3/3] Starting Backend Server (Port 5000)...")
    backend_env = os.environ.copy()
    backend_env["FLASK_ENV"] = "development"
    backend_env["PYTHONUNBUFFERED"] = "1"

    backend_process = subprocess.Popen(
        [sys.executable, "main.py"],
        cwd=BACKEND_DIR,
        env=backend_env
    )

    time.sleep(2)

    app_url = f"http://localhost:{FRONTEND_PORT}"
    print("\n" + "=" * 60)
    print("🎉 KNOT IS RUNNING SUCCESSFULLY!")
    print("=" * 60)
    print(f"👉 Frontend App : {app_url}")
    print(f"👉 Backend API  : http://localhost:{BACKEND_PORT}")
    print("💡 Test OTP and logs will appear below.")
    print("🛑 Press Ctrl+C in this terminal to stop both servers.")
    print("=" * 60 + "\n")

    try:
        webbrowser.open(app_url)
    except Exception:
        pass

    try:
        backend_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping servers...")
        backend_process.terminate()
        try:
            backend_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            backend_process.kill()
        print("✅ Servers stopped cleanly. Goodbye!")

if __name__ == "__main__":
    main()
