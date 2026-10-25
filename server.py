import os
import time
import random
from flask import Flask, request, jsonify

app = Flask(__name__)

# Memóriában tárolt adatok (Élesben használhatsz SQLite/PostgreSQL adatbázist)
users = {
    # "admin": "1234"
}

# SMS ellenőrző kódok: { "+36301234567": {"code": "123456", "expires": timestamp} }
verification_codes = {}

# Várakozó SMS-ek sora a saját telefonodnak
pending_sms_queue = []

# Chat üzenetek
chat_messages = []


@app.route('/', methods=['GET'])
def index():
    return jsonify({"status": "ok", "message": "Lenner Gumiszerviz Szerver Működik!"}), 200


# 1. Bejelentkezés
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Hiányzó felhasználónév vagy jelszó"}), 400

    if users.get(username) == password:
        return jsonify({"message": "Sikeres bejelentkezés"}), 200
    else:
        return jsonify({"error": "Helytelen felhasználónév vagy jelszó"}), 401


# 2. SMS kód kérése regisztrációhoz
@app.route('/request_sms', methods=['POST'])
def request_sms():
    data = request.get_json(silent=True) or {}
    phone = data.get('phone')

    if not phone:
        return jsonify({"error": "Telefonszám megadása kötelező"}), 400

    # 6-jegyű kód generálása
    code = str(random.randint(100000, 999999))
    verification_codes[phone] = {
        "code": code,
        "expires": time.time() + 300  # 5 percig érvényes
    }

    # Betesszük a várakozási sorba az SMS-t
    pending_sms_queue.append({
        "phone": phone,
        "message": f"Lenner Műhely: A regisztrációs kódod: {code}"
    })

    print(f"[SMS KÉRÉS] Telefonszám: {phone} -> Kód: {code}")
    return jsonify({"status": "ok", "message": "SMS kód elküldve a sorba"}), 200


# 3. A te saját telefonod (SMS Gateway) innen kéri le a küldendő SMS-eket
@app.route('/get_pending_sms', methods=['GET'])
def get_pending_sms():
    global pending_sms_queue
    if pending_sms_queue:
        sms = pending_sms_queue.pop(0)  # Kiveszi a legrégebbi SMS-t
        return jsonify(sms), 200
    return jsonify(None), 200


# 4. Regisztráció véglegesítése (kód ellenőrzéssel)
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    username = data.get('username')
    password = data.get('password')
    phone = data.get('phone')
    code = data.get('code')

    if not username or not password or not phone or not code:
        return jsonify({"error": "Minden mező kitöltése kötelező!"}), 400

    # Ellenőrizzük, létezik-e már a felhasználónév
    if username in users:
        return jsonify({"error": "Ilyen felhasználónév már létezik!"}), 409

    # SMS kód ellenőrzése
    saved_info = verification_codes.get(phone)
    if not saved_info:
        return jsonify({"error": "Ehhez a telefonszámhoz nem tartozik aktív kód!"}), 400

    if saved_info['code'] != code:
        return jsonify({"error": "Érvénytelen SMS kód!"}), 400

    if time.time() > saved_info['expires']:
        return jsonify({"error": "A kód lejárt! Kérj újat."}), 400

    # Ha minden jó, elmentjük a felhasználót
    users[username] = password
    # Használt kód törlése
    verification_codes.pop(phone, None)

    print(f"[ÚJ REGISZTRÁCIÓ] Felhasználó: {username}, Telefon: {phone}")
    return jsonify({"message": "Sikeres regisztráció!"}), 200


# 5. Élő chat üzenet küldése
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json(silent=True) or {}
    sender = data.get('sender')
    text = data.get('text')

    if sender and text:
        chat_messages.append({"sender": sender, "text": text})
        return jsonify({"status": "ok"}), 200
    return jsonify({"error": "Hiányzó adatok"}), 400


# 6. Chat üzenetek lekérése
@app.route('/get_messages', methods=['POST'])
def get_messages():
    return jsonify(chat_messages), 200


if __name__ == '__main__':
    # Helyi teszteléshez
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
