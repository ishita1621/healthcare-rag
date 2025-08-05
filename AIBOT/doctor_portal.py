import os
import json
from datetime import datetime
from typing import List, Dict
import streamlit as st
# Inject background image using inline CSS


import os



# Load global style
if os.path.exists("style.css"):
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)




UPLOAD_DIR = "uploads"
SUGGESTIONS_FILE = "suggestions.txt"
BOOKED_FILE = "appointments.json"

# Load appointment records
def load_appointments() -> List[Dict]:
    try:
        with open(BOOKED_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Save updated appointments
def save_appointments(data: List[Dict]):
    with open(BOOKED_FILE, "w") as f:
        json.dump(data, f, indent=2)

# MAIN APP
st.title("🩺 Doctor Portal - Manage Appointments & Prescriptions")

appointments = load_appointments()
pending_appointments = [a for a in appointments if a.get("status") == "Pending"]
accepted_appointments = [a for a in appointments if a.get("status") == "Accepted"]

# SECTION 1: Accept/Reject Appointments
st.header("📋 Appointment Management")

if not pending_appointments and not accepted_appointments:
    st.info("No pending or accepted appointments at the moment.")
else:
    if pending_appointments:
        st.subheader("🕒 Pending Appointments")
        for app in pending_appointments:
            st.write(f"*ID:* {app['id']}")
            st.write(f"*Patient Name:* {app['name']}")
            st.write(f"*Symptoms:* {app['symptoms']}")
            st.write(f"*Urgency Score:* {app['urgency_score']}")
            st.write(f"*Time Recommendation:* {app['time_recommendation']}")
            col1, col2 = st.columns(2)
            if col1.button(f"✅ Accept {app['id']}", key=f"accept_{app['id']}"):
                app['status'] = "Accepted"
                save_appointments(appointments)
                st.success(f"Appointment {app['id']} accepted.")
                st.rerun()
            if col2.button(f"❌ Reject {app['id']}", key=f"reject_{app['id']}"):
                app['status'] = "Rejected"
                save_appointments(appointments)
                st.warning(f"Appointment {app['id']} rejected.")
                st.rerun()

    if accepted_appointments:
        st.subheader("✅ Accepted Appointments & Patient Info")
        for app in accepted_appointments:
            with st.expander(f"Appointment ID: {app['id']} - Patient: {app['name']}"):
                for key, value in app.items():
                    st.write(f"*{key.capitalize().replace('_', ' ')}:* {value}")

# SECTION 2: Prescription Suggestion Tool
st.header("📁 Prescription Viewer & Suggestions")

patient_id = st.text_input("🔍 Enter Patient ID to View Prescriptions", key="dpid")
if patient_id:
    pid_folder = os.path.join(UPLOAD_DIR, patient_id)
    if os.path.isdir(pid_folder):
        files = sorted(os.listdir(pid_folder))
        if not files:
            st.warning("No uploaded files found for this patient.")
        for fname in files:
            st.write(f"*📄 File:* {fname}")
            path = os.path.join(pid_folder, fname)
            with open(path, "rb") as f:
                st.download_button("⬇️ Download", f.read(), file_name=fname)

            key_text = f"sugg_{patient_id}_{fname}"
            key_btn = f"btn_{patient_id}_{fname}"

            if key_text not in st.session_state:
                st.session_state[key_text] = ""

            st.text_area("💬 Your suggestion:", key=key_text)

            def save(pid=patient_id, fn=fname, key=key_text):
                sugg = st.session_state[key].strip()
                if sugg:
                    entry = f"{datetime.now()},{pid},{fn},{sugg}\n"
                    with open(SUGGESTIONS_FILE, "a") as sf:
                        sf.write(entry)
                    st.session_state[f"saved_{key}"] = True

            st.button("📤 Submit Suggestion", key=key_btn, on_click=save)
            if st.session_state.get(f"saved_{key_btn}".replace("btn_", "sugg_"), False):
                st.success("Suggestion recorded ✅")
    else:
        st.warning("Patient folder not found. Please check Patient ID.")