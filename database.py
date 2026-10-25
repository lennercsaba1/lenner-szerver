import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

DB_FILE = "adatbazis.json"
CHAT_FILE = "chat_uzenetek.json"
LOG_FILE = "chat_naplo.json"

db = None
KEY_PATH = os.path.join(os.path.dirname(__file__), "firebase_key.json")

# Google Firebase Firestore csatlakozás kulcsból vagy környezeti változóból
if os.path.exists(KEY_PATH):
    try:
        cred = credentials.Certificate(KEY_PATH)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("[DATABASE] Google Firebase Firestore sikeresen csatlakoztatva!")
    except Exception as e:
        print(f"[DATABASE HIBA] Firebase indítási hiba: {e}")
elif os.environ.get("FIREBASE_KEY_JSON"):
    try:
        key_dict = json.loads(os.environ.get("FIREBASE_KEY_JSON"))
        cred = credentials.Certificate(key_dict)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("[DATABASE] Google Firebase Firestore ENV-ből csatlakoztatva!")
    except Exception as e:
        print(f"[DATABASE HIBA] Firebase ENV indítási hiba: {e}")


def load_data(file_path):
    if db:
        try:
            doc_id = file_path.replace(".json", "")
            doc_ref = db.collection("rendeles_app").document(doc_id)
            doc = doc_ref.get()
            if doc.exists:
                data = doc.to_dict().get("data")
                if data is not None:
                    return data
        except Exception as e:
            print(f"[FIRESTORE OLVASÁSI HIBA] {file_path}: {e}")

    # Fallback helyi fájlra
    if not os.path.exists(file_path):
        return {} if file_path == DB_FILE else []
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {} if file_path == DB_FILE else []


def save_data(file_path, data):
    if db:
        try:
            doc_id = file_path.replace(".json", "")
            doc_ref = db.collection("rendeles_app").document(doc_id)
            doc_ref.set({"data": data})
        except Exception as e:
            print(f"[FIRESTORE MENTÉSI HIBA] {file_path}: {e}")

    # Mentés helyi fájlba is
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            f.flush()
            try:
                os.fsync(f.fileno())
            except:
                pass
    except Exception as e:
        pass
