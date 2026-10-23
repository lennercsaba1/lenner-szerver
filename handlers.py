from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
from datetime import datetime

from database import load_data, save_data, DB_FILE, CHAT_FILE, LOG_FILE
from admin_template import get_admin_html

ADMIN_SECRET = "lenneradmin123"

class SimpleServer(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query = urllib.parse.parse_qs(parsed_path.query)

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

        if path == "/admin_api_logs":
            password = query.get("pass", [""])[0]
            if password != ADMIN_SECRET:
                self.send_response(401)
                self.end_headers()
                return
            logs = load_data(LOG_FILE)
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(logs, ensure_ascii=False).encode('utf-8'))
            return

        if path == "/admin":
            password = query.get("pass", [""])[0]
            if password != ADMIN_SECRET:
                self.send_response(401)
                self.end_headers()
                self.wfile.write("Helytelen admin jelszó!".encode('utf-8'))
                return

            action = query.get("action", [""])[0]

            if action == "reply":
                target_user = query.get("user", [""])[0]
                reply_text = query.get("text", [""])[0]
                if target_user and reply_text:
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    new_msg = {
                        "sender": "Lenner Műhely",
                        "target": target_user,
                        "text": reply_text,
                        "timestamp": now_str,
                        "read": True
                    }
                    chats = load_data(CHAT_FILE)
                    chats.append(new_msg)
                    save_data(CHAT_FILE, chats)

                    logs = load_data(LOG_FILE)
                    logs.append(new_msg)
                    save_data(LOG_FILE, logs)
                
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
                return

            if action == "delete_user":
                target_user = query.get("user", [""])[0]
                if target_user:
                    users = load_data(DB_FILE)
                    if target_user in users:
                        del users[target_user]
                        save_data(DB_FILE, users)
                    
                    chats = load_data(CHAT_FILE)
                    filtered_chats = [c for c in chats if c.get("sender") != target_user and c.get("target") != target_user]
                    save_data(CHAT_FILE, filtered_chats)
                
                self.send_response(302)
                self.send_header('Location', f'/admin?pass={ADMIN_SECRET}')
                self.end_headers()
                return

            if action == "clear_chat":
                target_user = query.get("user", [""])[0]
                if target_user:
                    chats = load_data(CHAT_FILE)
                    filtered_chats = [c for c in chats if c.get("sender") != target_user and c.get("target") != target_user]
                    save_data(CHAT_FILE, filtered_chats)
                
                self.send_response(302)
                self.send_header('Location', f'/admin?pass={ADMIN_SECRET}')
                self.end_headers()
                return

            users = load_data(DB_FILE)
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()

            user_count = len(users) if isinstance(users, dict) else 0
            html = get_admin_html(user_count, ADMIN_SECRET)

            if isinstance(users, dict):
                for user, pwd in users.items():
                    html += f"""<tr>
                <td>{user}</td>
                <td>{pwd}</td>
                <td>
                    <button onclick="createOrUpdateBubble('{user}', false); toggleUserChat('{user}');">Chat nyitása</button>
                    <button class="btn-log" onclick="toggleLoggedChats('{user}')">Naplózott beszélgetés</button>
                </td>
                <td style="text-align: right;">
                    <button class="btn-clear-chat" onclick="confirmClearChat('{user}')">Chat törlése</button>
                    <button class="btn-delete" onclick="confirmDelete('{user}')">X Törlés</button>
                </td>
            </tr>"""

            html += """        </table>
    </div>

    <!-- JOBB OLDALI NAPLÓZOTT BESZÉLGETÉS SÁV -->
    <div id="log-sidebar">
        <div id="log-header">
            <span id="log-title">Naplózott beszélgetés</span>
            <div class="log-header-buttons">
                <button onclick="saveLogAsDoc()" style="background: #FF8C00; color: #000; padding: 2px 10px; margin:0; font-weight:bold;">Mentés</button>
                <button onclick="let sb=document.getElementById('log-sidebar'); sb.style.display='none'; currentLogUser='';" style="background: #444; color: #fff; padding: 2px 8px; margin:0;">X</button>
            </div>
        </div>
        <div id="log-body"></div>
    </div>

    <div id="bubbles-container"></div>

    <div id="chat-modal">
        <div id="chat-header">
            <span id="chat-title">Chat</span>
            <button onclick="closeChatCompletely(event)" style="background: #444; color: #fff; padding: 2px 8px; margin:0;">X</button>
        </div>
        <div id="chat-body"></div>
        <div id="chat-footer">
            <input type="text" id="reply-text" placeholder="Írd be a választ..." onkeydown="if(event.key==='Enter') sendAdminReply();">
            <button onclick="sendAdminReply()">Küldés</button>
        </div>
    </div>

</body>
</html>"""
            self.wfile.write(html.encode('utf-8'))

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
            
            if "timestamp" not in data or not data["timestamp"]:
                data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            data["read"] = False
            chats.append(data)
            save_data(CHAT_FILE, chats)

            logs = load_data(LOG_FILE)
            if not isinstance(logs, list):
                logs = []
            logs.append(data)
            save_data(LOG_FILE, logs)
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Uzenet elmentve")

        elif self.path == "/get_messages":
            username = data.get("username", "")
            chats = load_data(CHAT_FILE)
            
            user_messages = [
                c for c in chats 
                if c.get("sender") == username or 
                   (c.get("sender") == "Lenner Műhely" and c.get("target") == username)
            ]
            
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(user_messages, ensure_ascii=False).encode('utf-8'))

        else:
            self.send_response(404)
            self.end_headers()