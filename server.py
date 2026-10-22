from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import urllib.parse

DB_FILE = "adatbazis.json"
CHAT_FILE = "chat_uzenetek.json"
ADMIN_SECRET = "lenneradmin123"

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

        if path == "/admin":
            password = query.get("pass", [""])[0]
            if password != ADMIN_SECRET:
                self.send_response(401)
                self.end_headers()
                self.wfile.write("Helytelen admin jelszó!".encode('utf-8'))
                return

            action = query.get("action", [""])[0]

            # Válasz küldésekor elmentjük és visszairányítunk
            if action == "reply":
                target_user = query.get("user", [""])[0]
                reply_text = query.get("text", [""])[0]
                if target_user and reply_text:
                    chats = load_data(CHAT_FILE)
                    chats.append({
                        "sender": "Lenner Műhely",
                        "target": target_user,
                        "text": reply_text,
                        "read": True
                    })
                    save_data(CHAT_FILE, chats)
                
                self.send_response(302)
                self.send_header('Location', f'/admin?pass={ADMIN_SECRET}')
                self.end_headers()
                return

            # Amint megnyitod az admin oldalt, az üzeneteket olvasottá tesszük, így a riasztás azonnal elhallgat
            chats = load_data(CHAT_FILE)
            for msg in chats:
                if msg.get("sender") != "Lenner Műhely":
                    msg["read"] = True
            save_data(CHAT_FILE, chats)

            users = load_data(DB_FILE)

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()

            html = f"""
            <html>
            <head>
                <title>Lenner Műhely Admin Panel</title>
                <style>
                    body {{ font-family: Arial; background: #121212; color: #fff; padding: 20px; }}
                    h1, h2 {{ color: #FF8C00; }}
                    table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; background: #1E1E1E; }}
                    th, td {{ border: 1px solid #444; padding: 10px; text-align: left; }}
                    th {{ background: #222; }}
                    .card {{ background: #1E1E1E; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
                    input, button {{ padding: 8px; margin: 4px 0; background: #222; color: #fff; border: 1px solid #FF8C00; border-radius: 4px; }}
                    button {{ background: #FF8C00; color: #000; font-weight: bold; cursor: pointer; }}
                    .refresh-banner {{ background: #D35400; color: #fff; padding: 10px; border-radius: 5px; margin-bottom: 15px; display: none; text-align: center; font-weight: bold; }}
                </style>
                <script>
                    // Nincs idegesítő auto-frissítés ami törli a szöveget! 
                    // Csak háttérben figyeljük, hogy jött-e új üzenet, és ha igen, kiírunk egy kulturált gombot, amivel frissíthetsz.
                    setInterval(function() {{
                        fetch('/admin?pass={ADMIN_SECRET}&check_only=1')
                        .then(response => response.json())
                        .then(data => {{
                            if (data.has_new) {{
                                document.getElementById('refreshBanner').style.display = 'block';
                            }}
                        }}).catch(e => {{}});
                    }}, 5000);
                </script>
            </head>
            <body>
                <h1>Lenner Gumiszerviz - Műhely Vezérlőpult</h1>
                
                <div id="refreshBanner" class="refresh-banner">
                    Új üzenet érkezett! <a href="/admin?pass={ADMIN_SECRET}" style="color: #fff; text-decoration: underline; margin-left: 10px;">Kattints ide a frissítéshez</a>
                </div>

                <div class="card">
                    <h2>Élő Chat & Válaszadás</h2>
                    <table>
                        <tr><th>Küldő</th><th>Célzott Ügyfél</th><th>Üzenet</th><th>Válasz küldése</th></tr>
            """
            if isinstance(chats, list):
                for msg in chats:
                    sender = msg.get('sender', 'Ismeretlen')
                    target = msg.get('target', 'Mindenki')
                    text = msg.get('text', '')
                    
                    reply_form = ""
                    if sender != "Lenner Műhely":
                        reply_form = f"""
                        <form action="/admin" method="GET">
                            <input type="hidden" name="pass" value="{ADMIN_SECRET}">
                            <input type="hidden" name="action" value="reply">
                            <input type="hidden" name="user" value="{sender}">
                            <input type="text" name="text" placeholder="Írd be a választ..." required>
                            <button type="submit">Küldés</button>
                        </form>
                        """
                    else:
                        reply_form = "<i>Admin válasz</i>"

                    html += f"<tr><td><b>{sender}</b></td><td>{target}</td><td>{text}</td><td>{reply_form}</td></tr>"

            html += f"""
                    </table>
                </div>

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
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
        
        elif path == "/admin" and query.get("check_only"):
            chats = load_data(CHAT_FILE)
            # Megnézzük, van-e olyan üzenet, ami azóta érkezett
            has_unread = any(not c.get("read", False) and c.get("sender") != "Lenner Műhely" for c in chats)
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"has_new": has_unread}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
        except:
            self.send_response(400)
            self.end_headers()
            return

        if self.path == "/register":
            users = load_data(DB_FILE)
            username = data.get("username")
            password = data.get("password")
            if username and password and username not in users:
                users[username] = password
                save_data(DB_FILE, users)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Sikeres regisztracio")
            else:
                self.send_response(400)
                self.end_headers()

        elif self.path == "/login":
            users = load_data(DB_FILE)
            username = data.get("username")
            password = data.get("password")
            if username in users and users[username] == password:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Sikeres belepes")
            else:
                self.send_response(401)
                self.end_headers()

        elif self.path == "/chat":
            chats = load_data(CHAT_FILE)
            if not isinstance(chats, list):
                chats = []
            data["read"] = False
            chats.append(data)
            save_data(CHAT_FILE, chats)
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Uzenet elmentve")

        elif self.path == "/get_messages":
            username = data.get("username", "")
            chats = load_data(CHAT_FILE)
            user_messages = [c for c in chats if c.get("sender") == username or c.get("target") == username or c.get("sender") == "Lenner Műhely"]
            
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(user_messages, ensure_ascii=False).encode('utf-8'))

        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    server = HTTPServer(('0.0.0.0', port), SimpleServer)
    print(f"A szerver fut a {port}-es porton...")
    server.serve_forever()
