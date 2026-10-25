from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
from datetime import datetime, timedelta

from database import load_data, save_data, DB_FILE, CHAT_FILE, LOG_FILE
from admin_template import get_admin_html

ADMIN_SECRET = "lenneradmin123"

user_last_activity = {}

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

        if path == "/admin_api_status":
            password = query.get("pass", [""])[0]
            if password != ADMIN_SECRET:
                self.send_response(401)
                self.end_headers()
                return
            
            users = load_data(DB_FILE)
            now = datetime.now()
            status_dict = {}
            if isinstance(users, dict):
                for user in users.keys():
                    if user in user_last_activity:
                        is_online = (now - user_last_activity[user]) < timedelta(seconds=60)
                        status_dict[user] = is_online
                    else:
                        status_dict[user] = False

            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(status_dict, ensure_ascii=False).encode('utf-8'))
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
                    
                    if target_user in user_last_activity:
                        del user_last_activity[target_user]
                
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
            
            users_table_html = ""
            now = datetime.now()
            if isinstance(users, dict):
                user_list = []
                for user, pwd in users.items():
                    is_online = False
                    if user in user_last_activity:
                        is_online = (now - user_last_activity[user]) < timedelta(seconds=60)
                    user_list.append((user, pwd, is_online))
                
                sorted_users = sorted(user_list, key=lambda u: (not u[2], u[0].lower()))

                for user, pwd, is_online in sorted_users:
                    dot_class = "status-dot status-online" if is_online else "status-dot status-offline"

                    users_table_html += f"""<tr data-user-row data-username="{user}">
                <td>
                    <div class="user-row-wrapper">
                        <span id="status-dot-{user}" class="{dot_class}" title="Státusz" data-online="{1 if is_online else 0}"></span>
                        {user}
                    </div>
                </td>
                <td>{pwd}</td>
                <td>
                    <button class="btn-title-tab" onclick="toggleUserTitleTab('{user}')">Személyes adatok</button>
                    <button class="btn-log" onclick="toggleLoggedChats('{user}')">Naplózott beszélgetés</button>
                    <button class="btn-title-tab" onclick="alert('Munkalapok megnyitása...')">Munkalapok</button>

                    <div id="data-panel-{user}" class="data-panel">
                        <div style="display: flex; flex-direction: column; gap: 4px;">
                            <div><strong>Elérhetőség:</strong> -</div>
                            <div><strong>Cím:</strong> -</div>
                        </div>
                    </div>
                </td>
                <td style="font-size: 13px; color: #ccc;">-</td>
                <td>
                    <div style="display: flex; align-items: center; width: 100%;">
                        <button class="btn-chat-open" onclick="createOrUpdateBubble('{user}', false); toggleUserChat('{user}');">Chat nyitása</button>
                        <button class="btn-invoice-tab" onclick="toggleUserInvoiceTab('{user}')">Számla kiállítás</button>
                        <div style="margin-left: auto; display: flex; gap: 5px;">
                            <button class="btn-clear-chat" onclick="confirmClearChat('{user}')">X Chat törlése</button>
                            <button class="btn-delete" onclick="confirmDelete('{user}')">X Felhasználó törlése</button>
                        </div>
                    </div>
                    
                    <div id="invoice-panel-{user}" class="invoice-panel">
                        <div style="display: flex; flex-direction: column; gap: 4px;">
                            <div><strong>Számla kiállítás panel</strong></div>
                        </div>
                    </div>
                </td>
            </tr>"""

            html = get_admin_html(user_count, ADMIN_SECRET, users_table_html)
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
                user_last_activity[username] = datetime.now()
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Sikeres belepes")
            else:
                self.send_response(401)
                self.end_headers()

        elif self.path == "/chat":
            username = data.get("sender")
            if username:
                user_last_activity[username] = datetime.now()

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
            if username:
                user_last_activity[username] = datetime.now()

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
