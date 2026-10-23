import os
import json

DB_FILE = "adatbazis.json"
CHAT_FILE = "chat_uzenetek.json"
LOG_FILE = "chat_naplo.json"

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
        f.flush()
        try:
            os.fsync(f.fileno())
        except:
            pass