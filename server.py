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

            # Válasz küldése
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

            # Admin megnyitásakor olvasottá tesszük a régieket, hogy ne szóljon a riasztás
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
                </style>
                <script>
                    // Háttérben lekérdezzük az üzeneteket JSON-ben, így nem rántjuk szét az oldalt és a gépelést sem töröljük ki!
                    setInterval(function() {{
                        let activeInput = document.activeElement;
                        // HA éppen belemértél egy szövegmezőbe és gépelsz, SEMMI CSETRE SEM FRISSÍTÜNK!
                        if (activeInput && activeInput.tagName === 'INPUT' && activeInput.type === 'text') {{
                            return; 
                        }}

                        fetch('/admin_api_messages?pass={ADMIN_SECRET}')
                        .then(res => res.json())
                        .then(chats => {{
                            let tbody = document.getElementById('chat-tbody');
                            let rows = '';
                            chats.forEach(msg => {{
                                let sender = msg.sender || 'Ismeretlen';
                                let target = msg.target || 'Mindenki';
                                let text = msg.text || '';
                                let replyForm = '';
                                
                                if (sender !== "Lenner Műhely") {{
                                    replyForm = `<form action="/admin" method="GET">
                                        <input type="hidden" name="pass" value="{ADMIN_SECRET}">
                                        <input type="hidden" name="action" value="reply">
                                        <input type="hidden" name="user" value="${sender}">
                                        <input type="text" name="text" placeholder="Írd be a választ..." required>
                                        <button type="submit">Küldés</button>
                                    </form>`;
                                }} else {{
                                    replyForm = "<i>Admin válasz</i>";
                                }}
                                rows += `<tr><td><b>${sender}</b></td><td>${target}</td><td>${text}</td><td>${replyForm}</td></tr>`;
                            }});
                            if(tbody) tbody.innerHTML = rows;
                        }}).catch(e => {{}});
                    }}, 3000);
                </script>
            </head>
            <body>
                <h1>Lenner Gumiszerviz - Műhely Vezérlőpult</h1>

                <div class="card">
                    <h2>Élő Chat & Válaszadás</h2>
                    <table>
                        <thead>
                            <tr><th>Küldő</th><th>Célzott Ügyfél</th><th>Üzenet</th><th>Válasz küldése</th></tr>
                        </thead>
                        <tbody id="chat-tbody">
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
                        </tbody>
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

        # Külön végpont a háttérbeli JSON chat frissítéshez (ez nem bántja a gépelést)
        elif path == "/admin_api_messages":
            password = query.get("pass", [""])[0]
            if password != ADMIN_SECRET:
                self.send_response(401)
                self.end_headers()
                return
            chats = load_data(CHAT_FILE)
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(chats, ensure_ascii=False).encode('utf-8'))

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
            user_messages = [c for c in chats if c.get("sender") == username or c.get("target"] == username or c.get("sender"] == "Lenner Műhely"]
            
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
