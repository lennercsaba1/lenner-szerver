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

        # 1. Háttér API végpont az üzenetek lekéréséhez
        if path == "/admin_api_messages":
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
            return

        # 2. Admin felület főoldal
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
                
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
                return

            users = load_data(DB_FILE)
            chats = load_data(CHAT_FILE)

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()

            html = f"""
            <html>
            <head>
                <title>Lenner Műhely Admin Panel</title>
                <style>
                    body {{ font-family: Arial; background: #121212; color: #fff; padding: 20px; margin: 0; }}
                    h1, h2 {{ color: #FF8C00; }}
                    table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; background: #1E1E1E; }}
                    th, td {{ border: 1px solid #444; padding: 10px; text-align: left; }}
                    th {{ background: #222; }}
                    .card {{ background: #1E1E1E; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
                    input, button {{ padding: 8px; margin: 4px 0; background: #222; color: #fff; border: 1px solid #FF8C00; border-radius: 4px; }}
                    button {{ background: #FF8C00; color: #000; font-weight: bold; cursor: pointer; }}

                    /* Jobb alsó sarok értesítő buborék */
                    #float-notification {{
                        position: fixed;
                        bottom: 20px;
                        right: 20px;
                        width: 200px;
                        height: 45px;
                        background: #D35400;
                        color: #fff;
                        border-radius: 8px;
                        display: none;
                        align-items: center;
                        justify-content: center;
                        font-weight: bold;
                        cursor: pointer;
                        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
                        z-index: 1000;
                        text-align: center;
                        font-size: 14px;
                        padding: 5px;
                    }}
                    .blinking {{
                        animation: blink 1s infinite;
                    }}
                    @keyframes blink {{
                        0% {{ opacity: 1; }}
                        50% {{ opacity: 0.3; }}
                        100% {{ opacity: 1; }}
                    }}

                    /* Felugró Chat Ablak közvetlenül a buborék felett */
                    #chat-modal {{
                        position: fixed;
                        bottom: 75px;
                        right: 20px;
                        width: 450px;
                        height: 480px;
                        background: #1E1E1E;
                        border: 2px solid #FF8C00;
                        border-radius: 10px;
                        display: none;
                        flex-direction: column;
                        box-shadow: 0 5px 15px rgba(0,0,0,0.7);
                        z-index: 1001;
                    }}
                    #chat-header {{
                        background: #222;
                        padding: 10px 15px;
                        color: #FF8C00;
                        font-weight: bold;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        border-top-left-radius: 8px;
                        border-top-right-radius: 8px;
                    }}
                    #chat-body {{
                        flex: 1;
                        padding: 15px;
                        overflow-y: auto;
                        display: flex;
                        flex-direction: column;
                        gap: 10px;
                    }}
                    .message-bubble {{
                        padding: 8px 12px;
                        border-radius: 6px;
                        max-width: 80%;
                        font-size: 14px;
                    }}
                    .msg-user {{ background: #333; align-self: flex-start; }}
                    .msg-admin {{ background: #FF8C00; color: #000; align-self: flex-end; font-weight: bold; }}
                    #chat-footer {{
                        padding: 10px;
                        background: #222;
                        display: flex;
                        gap: 5px;
                    }}
                    #chat-footer input {{
                        flex: 1;
                    }}
                </style>
                <script>
                    let currentChatUser = "";
                    let isChatOpen = false;

                    // Háttérben ellenőrizzük az üzeneteket
                    setInterval(function() {{
                        fetch('/admin_api_messages?pass={ADMIN_SECRET}')
                        .then(res => res.json())
                        .then(chats => {{
                            let unread = chats.filter(c => !c.read && c.sender !== "Lenner Műhely");
                            let notif = document.getElementById('float-notification');
                            
                            if (unread.length > 0) {{
                                let latest = unread[unread.length - 1];
                                currentChatUser = latest.sender;
                                
                                // Ha le van csukva az ablak, újra elindítjuk a villogást és kiírjuk, hogy új üzenet
                                if (!isChatOpen) {{
                                    notif.innerText = "Új üzenet: " + currentChatUser;
                                    notif.classList.add('blinking');
                                    notif.style.display = 'flex';
                                }}
                            }}

                            // Ha nyitva van a chat ablak, frissítjük a buborékokat
                            if (isChatOpen && currentChatUser) {{
                                renderChatMessages(chats, currentChatUser);
                            }}
                        }}).catch(e => {{}});
                    }}, 3000);

                    function handleNotificationClick() {{
                        let notif = document.getElementById('float-notification');
                        let modal = document.getElementById('chat-modal');

                        if (isChatOpen) {{
                            // Lecsukás
                            modal.style.display = 'none';
                            isChatOpen = false;
                        }} else {{
                            // Megnyitás: leáll a villogás, tisztán csak a név marad
                            notif.classList.remove('blinking');
                            notif.innerText = currentChatUser;
                            modal.style.display = 'flex';
                            isChatOpen = true;

                            if(currentChatUser) {{
                                document.getElementById('chat-title').innerText = "Chat: " + currentChatUser;
                                fetch('/admin_api_messages?pass={ADMIN_SECRET}')
                                .then(res => res.json())
                                .then(chats => {{
                                    renderChatMessages(chats, currentChatUser);
                                    fetch('/admin?pass={ADMIN_SECRET}&action=ack&user=' + encodeURIComponent(currentChatUser));
                                }});
                            }}
                        }}
                    }}

                    function closeChatCompletely(event) {{
                        event.stopPropagation();
                        document.getElementById('chat-modal').style.display = 'none';
                        document.getElementById('float-notification').style.display = 'none';
                        isChatOpen = false;
                        currentChatUser = "";
                    }}

                    function renderChatMessages(chats, username) {{
                        let body = document.getElementById('chat-body');
                        let html = '';
                        chats.forEach(msg => {{
                            if (msg.sender === username || (msg.sender === "Lenner Műhely" && msg.target === username)) {{
                                let isMe = (msg.sender === "Lenner Műhely");
                                let bubbleClass = isMe ? "msg-admin" : "msg-user";
                                let senderName = isMe ? "Én (Műhely)" : msg.sender;
                                html += `<div class="message-bubble ${{bubbleClass}}"><small style="display:block; font-size:10px; opacity:0.7;">${{senderName}}</small>${{msg.text}}</div>`;
                            }}
                        }});
                        body.innerHTML = html;
                        body.scrollTop = body.scrollHeight;
                    }}

                    function sendAdminReply() {{
                        let input = document.getElementById('reply-text');
                        let text = input.value.trim();
                        if(!text || !currentChatUser) return;

                        fetch('/admin?pass={ADMIN_SECRET}&action=reply&user=' + encodeURIComponent(currentChatUser) + '&text=' + encodeURIComponent(text))
                        .then(() => {{
                            input.value = '';
                            fetch('/admin_api_messages?pass={ADMIN_SECRET}')
                            .then(res => res.json())
                            .then(chats => renderChatMessages(chats, currentChatUser));
                        }});
                    }}
                </script>
            </head>
            <body>
                <h1>Lenner Gumiszerviz - Műhely Vezérlőpult</h1>
                
                <div class="card">
                    <h2>Műhely Információk</h2>
                    <p>A rendszer készen áll. Új üzenet érkezésekor a jobb alsó sarokban villogó buborék jelenik meg.</p>
                </div>

                <div class="card">
                    <h2>Regisztrált Felhasználók ({len(users)})</h2>
                    <table>
                        <tr><th>Felhasználónév</th><th>Jelszó</th><th>Akció</th></tr>
            """
            for user, pwd in users.items():
                html += f"<tr><td>{user}</td><td>{pwd}</td><td><button onclick=\"currentChatUser='{user}'; document.getElementById('float-notification').innerText='{user}'; document.getElementById('float-notification').classList.remove('blinking'); document.getElementById('float-notification').style.display='flex'; document.getElementById('chat-modal').style.display='flex'; isChatOpen=true; document.getElementById('chat-title').innerText='Chat: {user}'; fetch('/admin_api_messages?pass={ADMIN_SECRET}').then(r=>r.json()).then(c=>renderChatMessages(c,'{user}'));\">Üzenet küldése</button></td></tr>"
            html += f"""
                    </table>
                </div>

                <!-- Jobb alsó sarok értesítő buborék -->
                <div id="float-notification" onclick="handleNotificationClick()">
                    Új üzenet
                </div>

                <!-- Felugró Chat Párbeszéd Panel közvetlenül a buborék felett -->
                <div id="chat-modal">
                    <div id="chat-header">
                        <span id="chat-title">Chat</span>
                        <button onclick="closeChatCompletely(event)" style="background: #444; color: #fff; padding: 2px 8px; margin:0;">X</button>
                    </div>
                    <div id="chat-body">
                        <!-- Ide jönnek a buborékok -->
                    </div>
                    <div id="chat-footer">
                        <input type="text" id="reply-text" placeholder="Írd be a választ..." onkeydown="if(event.key==='Enter') sendAdminReply();">
                        <button onclick="sendAdminReply()">Küldés</button>
                    </div>
                </div>

            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))

        # Segéd funkció a chat olvasottá tételhez háttérből
        elif path == "/admin" and query.get("action") == ["ack"]:
            target_user = query.get("user", [""])[0]
            chats = load_data(CHAT_FILE)
            for msg in chats:
                if msg.get("sender") == target_user:
                    msg["read"] = True
            save_data(CHAT_FILE, chats)
            self.send_response(200)
            self.end_headers()
            return
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
