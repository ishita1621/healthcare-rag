import os
import streamlit as st
from datetime import datetime
import streamlit as st
# Inject background image using inline CSS


import os


# Load global style
if os.path.exists("style.css"):
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)



def run_prescription_module(force_patient_id: str = None):
    st.subheader("📄 Upload Prescription & View Suggestions")

    UPLOAD_DIR = "uploads"
    SUGGESTIONS_FILE = "suggestions.txt"
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Step 1: Patient ID
    if force_patient_id:
        patient_id = force_patient_id
        st.info(f"🔒 Viewing prescriptions for Patient ID: **{patient_id}**")
    else:
        patient_id = st.text_input("🔍 Enter Patient ID to View Prescriptions")
        if not patient_id:
            return

    # Step 2: Upload file
    uploaded = st.file_uploader("Upload prescription", type=["pdf", "png", "jpg", "jpeg"], key=f"upl_{patient_id}")

    if "last_uploaded" not in st.session_state:
        st.session_state.last_uploaded = None

    if uploaded:
        if st.session_state.last_uploaded != uploaded.name:
            pid_folder = os.path.join(UPLOAD_DIR, patient_id)
            os.makedirs(pid_folder, exist_ok=True)
            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded.name}"
            save_path = os.path.join(pid_folder, filename)
            with open(save_path, "wb") as f:
                f.write(uploaded.getbuffer())
            st.session_state.last_uploaded = uploaded.name
            st.success(f"✅ Uploaded successfully as `{filename}`")

    # Step 3: Show existing suggestions
    st.markdown("---")
    st.header("🧑‍⚕️ Suggestions from Doctor")

    if os.path.exists(SUGGESTIONS_FILE):
        with open(SUGGESTIONS_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(",", 3)
                if len(parts) == 4:
                    ts, pid, fname, sugg = parts
                    if pid == patient_id:
                        st.write(f"**📄 File:** {fname}")
                        st.write(f"💬 **Suggestion:** {sugg}")
                        st.caption(f"🕒 Submitted at {ts}")
