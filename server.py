from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import urllib.parse

DB_FILE = "adatbazis.json"
CHAT_FILE = "chat_uzenetek.json"
RENDELES_FILE = "rendelesek.json"
ADMIN_SECRET = "lenneradmin123"  # Admin jelszó a műhelyi géphez

def load_data(file_path):
    if not os.path.exists(file_path):
        return {} if file_path == DB_FILE else []
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {} if file_path == DB_FILE else []

def save_data(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

class SimpleServer(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query = urllib.parse.parse_qs(parsed_path.query)

        # Műhelyi Admin Panel
        if path == "/admin":
            password = query.get("pass", [""])[0]
            if password != ADMIN_SECRET:
                self.send_response(401)
                self.end_headers()
                self.wfile.write("Helytelen admin jelszó! Használd a ?pass=JELSZO formátumot.".encode('utf-8'))
                return

            users = load_data(DB_FILE)
            chats = load_data(CHAT_FILE)
            rendelesek = load_data(RENDELES_FILE)

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()

            html = f"""
            <html>
            <head>
                <title>Lenner Műhely Admin Panel</title>
                <meta http-equiv="refresh" content="5"> <!-- 5 másodpercenként frissül, hogy látsd az új üzeneteket -->
                <style>
                    body {{ font-family: Arial; background: #121212; color: #fff; padding: 20px; }}
                    h1, h2 {{ color: #FF8C00; }}
                    table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; background: #1E1E1E; }}
                    th, td {{ border: 1px solid #444; padding: 10px; text-align: left; }}
                    th {{ background: #222; }}
                    .card {{ background: #1E1E1E; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
                </style>
            </head>
            <body>
                <h1>Lenner Gumiszerviz - Műhely Vezérlőpult</h1>
                
                <div class="card">
                    <h2>Regisztrált Felhasználók ({len(users)})</h2>
                    <table>
                        <tr><th>Felhasználónév</th><th>Jelszó</th></tr>
            """
            for user, pwd in users.items():
                html += f"<tr><td>{user}</td><td>{pwd}</td></tr>"
            html += """
                    </table>
                </div>

                <div class="card">
                    <h2>Aktív Élő Chat Üzenetek</h2>
                    <table>
                        <tr><th>Küldő / Felhasználó</th><th>Üzenet</th></tr>
            """
            if isinstance(chats, list):
                for msg in chats:
                    html += f"<tr><td><b>{msg.get('sender', 'Ismeretlen')}</b></td><td>{msg.get('text', '')}</td></tr>"
            html += """
                    </table>
                </div>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write("Nem talalhato".encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
        except:
            self.send_response(400)
            self.end_headers()
            self.wfile.write("Hibas JSON".encode('utf-8'))
            return

        if self.path == "/register":
            users = load_data(DB_FILE)
            username = data.get("username")
            password = data.get("password")
            
            if not username or not password:
                self.send_response(400)
                self.end_headers()
                self.wfile.write("Hianyzo adatok".encode('utf-8'))
                return
                
            if username in users:
                self.send_response(409)
                self.end_headers()
                self.wfile.write("Mar letezik ilyen felhasznalo".encode('utf-8'))
                return
                
            users[username] = password
            save_data(DB_FILE, users)
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write("Sikeres regisztracio".encode('utf-8'))

        elif self.path == "/login":
            users = load_data(DB_FILE)
            username = data.get("username")
            password = data.get("password")
            
            if username in users and users[username] == password:
                self.send_response(200)
                self.end_headers()
                self.wfile.write("Sikeres belepes".encode('utf-8'))
            else:
                self.send_response(401)
                self.end_headers()
                self.wfile.write("Helytelen adatok".encode('utf-8'))

        elif self.path == "/chat":
            # Üzenetek mentése a szerverre
            chats = load_data(CHAT_FILE)
            if not isinstance(chats, list):
                chats = []
            chats.append(data)
            save_data(CHAT_FILE, chats)
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write("Uzenet elmentve".encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    server = HTTPServer(('0.0.0.0', port), SimpleServer)
    print(f"A szerver fut a {port}-es porton...")
    server.serve_forever()
