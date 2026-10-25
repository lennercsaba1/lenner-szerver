import os
import time
import random
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, Response, redirect

from database import load_data, save_data, DB_FILE, CHAT_FILE, LOG_FILE
from admin_template import get_admin_html

app = Flask(__name__)

ADMIN_SECRET = "lenneradmin123"
user_last_activity = {}

# Memóriában tárolt SMS kódok és elküldendő SMS sor
verification_codes = {}
pending_sms_queue = []


@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "ok", "message": "Lenner Gumiszerviz Szerver Működik!"}), 200


# ==========================================
# ADMIN PANEL VÉGPONTOK (/admin)
# ==========================================

@app.route('/admin', methods=['GET'])
def admin():
    password = request.args.get("pass", "")
    if password != ADMIN_SECRET:
        return "Helytelen admin jelszó!", 401

    action = request.args.get("action", "")

    if action == "ack":
        target_user = request.args.get("user", "")
        chats = load_data(CHAT_FILE)
        for msg in chats:
            if msg.get("sender") == target_user:
                msg["read"] = True
        save_data(CHAT_FILE, chats)
        return "OK", 200

    if action == "reply":
        target_user = request.args.get("user", "")
        reply_text = request.args.get("text", "")
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
        return "OK", 200

    if action == "delete_user":
        target_user = request.args.get("user", "")
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
        return redirect(f"/admin?pass={ADMIN_SECRET}")

    if action == "clear_chat":
        target_user = request.args.get("user", "")
        if target_user:
            chats = load_data(CHAT_FILE)
            filtered_chats = [c for c in chats if c.get("sender") != target_user and c.get("target") != target_user]
            save_data(CHAT_FILE, filtered_chats)
        return redirect(f"/admin?pass={ADMIN_SECRET}")

    # Admin HTML felület összeállítása
    users = load_data(DB_FILE)
    user_count = len(users) if isinstance(users, dict) else 0
    users_table_html = ""
    now = datetime.now()

    if isinstance(users, dict):
        user_list = []
        for u, pwd in users.items():
            is_online = False
            if u in user_last_activity:
                is_online = (now - user_last_activity[u]) < timedelta(seconds=60)
            user_list.append((u, pwd, is_online))

        sorted_users = sorted(user_list, key=lambda u: (not u[2], u[0].lower()))

        for idx, (u, pwd_data, is_online) in enumerate(sorted_users, 1):
            if isinstance(pwd_data, dict):
                pwd = pwd_data.get("password", "")
                phone_num = pwd_data.get("phone", u)
                full_name = pwd_data.get("name", "") or "-"
                zip_c = pwd_data.get("zip", "")
                city_c = pwd_data.get("city", "")
                street_c = pwd_data.get("street", "")
                h_num = pwd_data.get("house_number", "")
                fl_door = pwd_data.get("floor_door", "")

                addr_parts = [p for p in [f"{zip_c} {city_c}".strip(), f"{street_c} {h_num}".strip(), fl_door] if p]
                full_address = ", ".join(addr_parts) if addr_parts else "-"
            else:
                pwd = str(pwd_data)
                phone_num = u
                full_name = "-"
                full_address = "-"

            display_name = f"Ügyfél #{idx}"
            dot_class = "status-dot status-online" if is_online else "status-dot status-offline"
            users_table_html += f"""<tr data-user-row data-username="{u}">
                <td>
                    <div class="user-row-wrapper">
                        <span id="status-dot-{u}" class="{dot_class}" title="Státusz" data-online="{1 if is_online else 0}"></span>
                        {display_name}
                    </div>
                </td>
                <td>{pwd}</td>
                <td>
                    <button onclick="createOrUpdateBubble('{u}', false); toggleUserChat('{u}');">Chat nyitása</button>
                    <button class="btn-log" onclick="toggleLoggedChats('{u}')">Naplózott beszélgetés</button>
                    <button class="btn-title-tab" onclick="toggleUserTitleTab('{u}')">Adatok</button>

                    <div id="data-panel-{u}" class="data-panel">
                        <div style="display: flex; flex-direction: column; gap: 4px;">
                            <div><strong>Név:</strong> {full_name}</div>
                            <div><strong>Elérhetőség:</strong> {phone_num}</div>
                            <div><strong>Cím:</strong> {full_address}</div>
                        </div>
                    </div>
                </td>
                <td>
                    <div style="display: flex; align-items: center; width: 100%;">
                        <button class="btn-invoice-tab" onclick="toggleUserInvoiceTab('{u}')">Számla kiállítás</button>
                        <div style="margin-left: auto; display: flex; gap: 5px;">
                            <button class="btn-clear-chat" onclick="confirmClearChat('{u}')">Chat törlése</button>
                            <button class="btn-delete" onclick="confirmDelete('{u}')">X Törlés</button>
                        </div>
                    </div>

                    <div id="invoice-panel-{u}" class="invoice-panel">
                        <div style="display: flex; flex-direction: column; gap: 4px;">
                            <div><strong>Számla kiállítás panel</strong></div>
                        </div>
                    </div>
                </td>
            </tr>"""

    html = get_admin_html(user_count, ADMIN_SECRET, users_table_html)
    return Response(html, mimetype='text/html')


@app.route('/admin_api_messages', methods=['GET'])
def admin_api_messages():
    password = request.args.get("pass", "")
    if password != ADMIN_SECRET:
        return jsonify({"error": "Unauthorized"}), 401
    chats = load_data(CHAT_FILE)
    return jsonify(chats), 200


@app.route('/admin_api_logs', methods=['GET'])
def admin_api_logs():
    password = request.args.get("pass", "")
    if password != ADMIN_SECRET:
        return jsonify({"error": "Unauthorized"}), 401
    logs = load_data(LOG_FILE)
    return jsonify(logs), 200


@app.route('/admin_api_status', methods=['GET'])
def admin_api_status():
    password = request.args.get("pass", "")
    if password != ADMIN_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    users = load_data(DB_FILE)
    now = datetime.now()
    status_dict = {}
    if isinstance(users, dict):
        for u in users.keys():
            if u in user_last_activity:
                is_online = (now - user_last_activity[u]) < timedelta(seconds=60)
                status_dict[u] = is_online
            else:
                status_dict[u] = False

    return jsonify(status_dict), 200


# ==========================================
# APP VÉGPONTOK (Login, Register, SMS, Chat)
# ==========================================

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Hiányzó telefonszám vagy jelszó"}), 400

    users = load_data(DB_FILE)
    pwd_entry = users.get(username)
    if isinstance(pwd_entry, dict):
        stored_password = pwd_entry.get("password")
    else:
        stored_password = pwd_entry

    if stored_password and stored_password == password:
        user_last_activity[username] = datetime.now()
        return jsonify({"message": "Sikeres bejelentkezés"}), 200
    else:
        return jsonify({"error": "Helytelen telefonszám vagy jelszó"}), 401


@app.route('/request_sms', methods=['POST'])
def request_sms():
    data = request.get_json(silent=True) or {}
    phone = data.get('phone')

    if not phone:
        return jsonify({"error": "Telefonszám megadása kötelező"}), 400

    code = str(random.randint(100000, 999999))
    verification_codes[phone] = {
        "code": code,
        "expires": time.time() + 300
    }

    pending_sms_queue.append({
        "phone": phone,
        "message": f"Lenner Műhely: A regisztrációs kódod: {code}"
    })

    print(f"[SMS KÉRÉS] Telefonszám: {phone} -> Kód: {code}")
    return jsonify({"status": "ok", "message": "SMS kód elküldve a sorba"}), 200


@app.route('/get_pending_sms', methods=['GET'])
def get_pending_sms():
    global pending_sms_queue
    if pending_sms_queue:
        sms = pending_sms_queue.pop(0)
        return jsonify(sms), 200
    return jsonify(None), 200


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    username = data.get('username')
    password = data.get('password')
    phone = data.get('phone')
    code = data.get('code')

    name = data.get('name', '')
    zip_code = data.get('zip', '')
    city = data.get('city', '')
    street = data.get('street', '')
    house_number = data.get('house_number', '')
    floor_door = data.get('floor_door', '')

    if not username or not password:
        return jsonify({"error": "Minden mező kitöltése kötelező!"}), 400

    users = load_data(DB_FILE)
    if username in users:
        return jsonify({"error": "Ezzel a telefonszámmal már regisztráltak!"}), 409

    if phone and code:
        saved_info = verification_codes.get(phone)
        if not saved_info:
            return jsonify({"error": "Ehhez a telefonszámhoz nem tartozik aktív kód!"}), 400

        if saved_info['code'] != code:
            return jsonify({"error": "Érvénytelen SMS kód!"}), 400

        if time.time() > saved_info['expires']:
            return jsonify({"error": "A kód lejárt! Kérj újat."}), 400

        verification_codes.pop(phone, None)

    # Elmentjük a felhasználót és az összes adatát az adatbázisba
    users[username] = {
        "password": password,
        "phone": phone or username,
        "name": name,
        "zip": zip_code,
        "city": city,
        "street": street,
        "house_number": house_number,
        "floor_door": floor_door
    }
    save_data(DB_FILE, users)

    print(f"[ÚJ REGISZTRÁCIÓ] Név: {name}, Telefon: {phone or username}")
    return jsonify({"message": "Sikeres regisztráció!"}), 200


@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json(silent=True) or {}
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

    return jsonify({"status": "ok"}), 200


@app.route('/get_messages', methods=['POST'])
def get_messages():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    if username:
        user_last_activity[username] = datetime.now()

    chats = load_data(CHAT_FILE)
    if not isinstance(chats, list):
        chats = []

    user_messages = [
        c for c in chats
        if c.get("sender") == username or
           (c.get("sender") == "Lenner Műhely" and c.get("target") == username)
    ]

    return jsonify(user_messages), 200


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
