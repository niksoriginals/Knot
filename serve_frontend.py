import http.server
import socketserver
import os
import sys

from urllib.parse import urlparse

PORT = 3000
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "frontend"))

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

        # Check if the requested clean path maps to an existing .html file (e.g., /login -> /login.html)
        rel_name = clean_path.lstrip("/")
        candidate_file = os.path.join(FRONTEND_DIR, rel_name + ".html")
        if os.path.isfile(candidate_file):
            self.path = "/" + rel_name + ".html" + query

        return super().do_GET()

if __name__ == "__main__":
    if not os.path.exists(FRONTEND_DIR):
        print(f"❌ Frontend directory not found at: {FRONTEND_DIR}")
        sys.exit(1)

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), CleanURLHandler) as httpd:
        print(f"============================================================")
        print(f"🌐 [KNOT FRONTEND] Server running at: http://localhost:{PORT}")
        print(f"📁 Serving static files from: {FRONTEND_DIR}")
        print(f"============================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down frontend server...")
            httpd.server_close()
