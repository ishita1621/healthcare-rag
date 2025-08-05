import os, hashlib, json
import streamlit as st
# Inject background image using inline CSS


import os



# Load global style
if os.path.exists("style.css"):
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)




BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
CREDENTIALS_FILE = os.path.join(DATA_DIR, 'user_credentials.json')
os.makedirs(DATA_DIR, exist_ok=True)

# Initialize empty credentials file if missing
if not os.path.exists(CREDENTIALS_FILE):
    with open(CREDENTIALS_FILE, 'w') as f:
        json.dump({}, f)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def load_creds() -> dict:
    with open(CREDENTIALS_FILE, 'r') as f:
        return json.load(f)

def save_creds(creds: dict):
    with open(CREDENTIALS_FILE, 'w') as f:
        json.dump(creds, f, indent=2)

def validate_login(patient_id: str, password: str) -> bool:
    creds = load_creds()
    entry = creds.get(patient_id)
    return entry and entry["password"] == hash_password(password)

def register_user(patient_id: str, email: str, password: str) -> bool:
    creds = load_creds()
    if patient_id in creds:
        return False
    creds[patient_id] = {
        "patient_id": patient_id,
        "email": email,
        "password": hash_password(password)
    }
    save_creds(creds)
    return True

def change_password(patient_id: str, old_password: str, new_password: str) -> bool:
    creds = load_creds()
    entry = creds.get(patient_id)
    if entry and entry["password"] == hash_password(old_password):
        entry["password"] = hash_password(new_password)
        save_creds(creds)
        return True
    return False