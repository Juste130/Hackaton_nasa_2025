"""
Simple HTTP server to serve the frontend
"""
import http.server
import socketserver
import os
from pathlib import Path

def serve_frontend(port=3000):
    """Serve the frontend on specified port"""
    
    # Change to frontend directory
    frontend_dir = Path(__file__).parent / "frontend"
    if not frontend_dir.exists():
        print(f"Frontend directory not found: {frontend_dir}")
        return
    
    os.chdir(frontend_dir)
    
    # Create server
    Handler = http.server.SimpleHTTPRequestHandler
    
    # Add CORS headers
    class CORSRequestHandler(Handler):
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            super().end_headers()
    
    with socketserver.TCPServer(("", port), CORSRequestHandler) as httpd:
        print(f"🌐 Frontend server running at http://localhost:{port}")
        print(f"📁 Serving from: {frontend_dir}")
        print("📊 Make sure your API is running on http://localhost:8000")
        print("\nPress Ctrl+C to stop")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Frontend server stopped")

if __name__ == "__main__":
    serve_frontend()