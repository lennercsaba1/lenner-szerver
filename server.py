from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import urllib.parse
import base64
import time

DB_FILE = "adatbazis.json"
ADMIN_SECRET = "lenneradmin123"  # Ezzel a jelszóval tudsz majd belépni az admin felületre
UPLOAD_FOLDER = "uploads"

# Mappa létrehozása a képeknek, ha még nem létezik
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def load_users():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}

def save_users(users):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

class SimpleServer(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query = urllib.parse.parse_qs(parsed_path.query)

        if path == "/admin":
            password = query.get("pass", [""])[0]
            if password != ADMIN_SECRET:
                self.send_response(401)
                self.end_headers()
                self.wfile.write("Helytelen admin jelszó! Használd a ?pass=JELSZO formátumot.".encode('utf-8'))
                return

            users = load_users()
            
            # Lementett képek listázása az admin oldalon, hogy közvetlenül is látsd őket
            images = []
            if os.path.exists(UPLOAD_FOLDER):
                images = os.listdir(UPLOAD_FOLDER)

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()

            html = f"""
            <html>
            <head><title>Lenner Admin Panel</title></head>
            <body style="font-family: Arial; background: #121212; color: #fff; padding: 20px;">
                <h1 style="color: #FF8C00;">Lenner Gumiszerviz - Regisztrált Ügyfelek</h1>
                <table border="1" cellpadding="10" style="border-collapse: collapse; border-color: #444; margin-bottom: 30px;">
                    <tr><th>Felhasználónév</th><th>Jelszó (Plain)</th></tr>
            """
            for user, pwd in users.items():
                html += f"<tr><td>{user}</td><td>{pwd}</td></tr>"
            html += """
                </table>
                
                <h2 style="color: #FF8C00;">Feltöltött Képek (Uploads)</h2>
                <ul>
            """
            for img in images:
                html += f"<li>{img}</li>"
            if not images:
                html += "<li>Még nincsenek feltöltött képek.</li>"
            html += """
                </ul>
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

        users = load_users()

        if self.path == "/register":
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
            save_users(users)
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write("Sikeres regisztracio".encode('utf-8'))

        elif self.path == "/login":
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

        elif self.path == "/upload":
            # Új végpont az appból jövő képek fogadására
            try:
                username = data.get("username", "ismeretlen")
                image_base64 = data.get("image")

                if not image_base64:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write("Nincs kep adat!".encode('utf-8'))
                    return

                # Base64 string dekódolása bináris képbájtokká
                image_bytes = base64.b64decode(image_base64)

                # Egyedi fájlnév generálása (felhasználónév + időbélyeg)
                filename = f"{username}_{int(time.time())}.jpg"
                filepath = os.path.join(UPLOAD_FOLDER, filename)

                # Kép kiírása és mentése a szerver tárhelyére
                with open(filepath, 'wb') as f:
                    f.write(image_bytes)

                print(f"Sikeres képmentés: {filepath}")
                self.send_response(200)
                self.end_headers()
                self.wfile.write("Kép sikeresen fogadva".encode('utf-8'))

            except Exception as e:
                print(f"Hiba a kép mentésekor: {e}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"Szerver hiba: {str(e)}".encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    server = HTTPServer(('0.0.0.0', port), SimpleServer)
    print(f"A szerver fut a {port}-es porton...")
    server.serve_forever()
