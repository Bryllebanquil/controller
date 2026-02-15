from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

VAULT_FILE = "vault.txt"

def ensure_vault():
    if not os.path.exists(VAULT_FILE):
        open(VAULT_FILE, "w", encoding="utf-8").close()

def save_entry(site, username, password):
    ensure_vault()
    with open(VAULT_FILE, "a", encoding="utf-8") as f:
        f.write(f"{site}|{username}|{password}\n")

def read_entries():
    ensure_vault()
    data = []
    with open(VAULT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("|", 2)
            if len(parts) == 3:
                site, user, pwd = parts
                data.append({"site": site, "username": user, "password": pwd})
    return data

@app.route("/")
def home():
    return "Vault API Running"

@app.route("/save", methods=["POST"])
def save_password():
    data = request.get_json(force=True, silent=True) or {}
    site = data.get("site")
    username = data.get("username")
    password = data.get("password")
    if not site or not username or not password:
        return jsonify({"status": "error"}), 400
    save_entry(site, username, password)
    return jsonify({"status": "saved"})

@app.route("/get", methods=["GET"])
def get_all():
    return jsonify(read_entries())

if __name__ == "__main__":
    print("Vault running -> http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000)
