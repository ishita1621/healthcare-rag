import streamlit as st
# Inject background image using inline CSS


import json
import os
from datetime import datetime
from typing import Dict, List
from prescription_portal import run_prescription_module



from location_specialist import infer_specialist, generate_google_maps_link
if os.path.exists("style.css"):
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ------------------- Configuration -------------------
BOOKED_FILE = "appointments.json"

# ------------------- Offline Symptom Analysis -------------------
def analyze_symptoms_offline(symptoms: str) -> Dict[str, str]:
    symptoms_lower = symptoms.lower().strip()

    emergency_keywords = [
        'chest pain', 'heart attack', 'difficulty breathing', 'can\'t breathe',
        'severe bleeding', 'unconscious', 'suicide', 'overdose', 'stroke',
        'severe head injury', 'broken bone', 'severe burn'
    ]
    high_urgency_keywords = [
        'high fever', 'severe pain', 'intense pain', 'can\'t walk',
        'severe headache', 'vomiting blood', 'severe nausea', 'dehydrated',
        'severe diarrhea', 'severe allergic reaction', 'swollen', 'infection'
    ]
    medium_urgency_keywords = [
        'fever', 'headache', 'nausea', 'vomiting', 'diarrhea', 'pain',
        'cough', 'cold', 'flu', 'sore throat', 'earache', 'rash',
        'tired', 'fatigue', 'dizzy', 'stomach ache'
    ]
    low_urgency_keywords = [
        'checkup', 'routine', 'physical', 'vaccination', 'prescription',
        'mild pain', 'slight discomfort', 'general consultation'
    ]

    urgency_score = 5
    time_recommendation = "Next day"
    notes = "Please consult with healthcare provider for proper diagnosis"
    key_symptoms = symptoms[:50] + "..." if len(symptoms) > 50 else symptoms

    if any(keyword in symptoms_lower for keyword in emergency_keywords):
        urgency_score = 9
        time_recommendation = "IMMEDIATE - Go to Emergency Room"
        notes = "⚠️ EMERGENCY: Seek immediate medical attention or call emergency services!"
    elif any(keyword in symptoms_lower for keyword in high_urgency_keywords):
        urgency_score = 8
        time_recommendation = "Same-day"
        notes = "High priority - Schedule appointment today or visit urgent care"
    elif any(keyword in symptoms_lower for keyword in medium_urgency_keywords):
        urgency_score = 6
        time_recommendation = "Within 1-2 days"
        notes = "Schedule appointment soon for evaluation and treatment"
    elif any(keyword in symptoms_lower for keyword in low_urgency_keywords):
        urgency_score = 3
        time_recommendation = "Within 1-2 weeks"
        notes = "Routine consultation - schedule at your convenience"

    if 'severe' in symptoms_lower:
        urgency_score = min(urgency_score + 2, 10)
    if 'mild' in symptoms_lower:
        urgency_score = max(urgency_score - 1, 1)

    return {
        "urgency_score": str(urgency_score),
        "time_recommendation": time_recommendation,
        "key_symptoms": key_symptoms,
        "notes": f"{notes} (AI-powered assessment)"
    }

# ------------------- Utility Functions -------------------
def ensure_data_file():
    if not os.path.exists(BOOKED_FILE):
        with open(BOOKED_FILE, "w") as f:
            json.dump([], f)

def get_urgency_color(score: int) -> str:
    if score >= 8:
        return "🔴"
    elif score >= 5:
        return "🟡"
    else:
        return "🟢"

def book_appointment(name: str, age: str, location: str, symptoms: str, hospital: str, suggestion: Dict[str, str]) -> bool:
    try:
        ensure_data_file()
        with open(BOOKED_FILE, "r") as f:
            data = json.load(f)

        appointment = {
            "id": len(data) + 1,
            "name": name,
            "age": age,
            "location": location,
            "symptoms": symptoms,
            "preferred_hospital": hospital,
            "urgency_score": suggestion["urgency_score"],
            "time_recommendation": suggestion["time_recommendation"],
            "key_symptoms": suggestion["key_symptoms"],
            "notes": suggestion["notes"],
            "booking_time": datetime.now().isoformat(),
            "status": "Pending"
        }

        data.append(appointment)

        with open(BOOKED_FILE, "w") as f:
            json.dump(data, f, indent=2)

        return True
    except Exception as e:
        st.error(f"❌ Failed to book appointment: {str(e)}")
        return False

def load_appointments() -> List[Dict]:
    try:
        ensure_data_file()
        with open(BOOKED_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"❌ Failed to load appointments: {str(e)}")
        return []

# ------------------- Streamlit UI -------------------
def main():
    st.set_page_config(
        page_title="AI Doctor Appointment Booking",
        page_icon="🏥",
        layout="centered"
    )

    # Optional CSS for urgency classes
    st.markdown("""
    <style>
    .urgency-high {background-color: #ffcccc; padding: 10px; border-radius: 8px;}
    .urgency-medium {background-color: #fff0b3; padding: 10px; border-radius: 8px;}
    .urgency-low {background-color: #d6f5d6; padding: 10px; border-radius: 8px;}
    .main-header {text-align: center;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 class="main-header">🏥 AI-Powered Doctor Appointment Booking</h1>', unsafe_allow_html=True)
    st.info("🤖 Works offline using intelligent rule-based symptom analysis.")

    tab1, tab2, tab3 = st.tabs([
        "📝 Book Appointment", 
        "📋 View Appointments",
        "ℹ️ About"
    ])

    with tab1:
        book_appointment_tab()
    with tab2:
        view_appointments_tab()
    with tab3:
        about_tab()

def book_appointment_tab():
    st.header("📝 Book New Appointment")

    # Initialize session state keys if not set
    for key in ['form_name', 'form_age', 'form_location', 'form_symptoms', 'form_hospital']:
        if key not in st.session_state:
            st.session_state[key] = ""
    for key in ['show_suggestion', 'current_suggestion', 'appointment_booked', 'last_patient_id']:
        if key not in st.session_state:
            st.session_state[key] = False if key == 'appointment_booked' else None

    with st.form("appointment_form", clear_on_submit=False):
        col1, col2 = st.columns([2, 1])
        with col1:
            name = st.text_input("👤 Patient Name", value=st.session_state.form_name)
        with col2:
            age = st.text_input("🎂 Age", value=st.session_state.form_age)

        location = st.text_input("📍 Your Location", value=st.session_state.form_location)
        # Prefill from chatbot if available
        if "symptom_to_forward" in st.session_state and not st.session_state.form_symptoms:
            st.session_state.form_symptoms = st.session_state.symptom_to_forward

        symptoms = st.text_area("🩺 Describe your symptoms", height=100, value=st.session_state.form_symptoms)

        st.warning("⚠️ For emergencies, call your local emergency number.")
        submitted = st.form_submit_button("🚀 Get Appointment Recommendation", use_container_width=True)

    # Update session state after form submission
    st.session_state.form_name = name
    st.session_state.form_age = age
    st.session_state.form_location = location
    st.session_state.form_symptoms = symptoms

    if submitted:
        if not name or not symptoms:
            st.error("❌ Please provide both name and symptoms.")
            return
        suggestion = analyze_symptoms_offline(symptoms)
        st.session_state.current_suggestion = suggestion
        st.session_state.show_suggestion = True
        st.session_state.appointment_booked = False

    if st.session_state.show_suggestion and st.session_state.current_suggestion:
        suggestion = st.session_state.current_suggestion
        urgency_score = int(suggestion["urgency_score"])
        urgency_emoji = get_urgency_color(urgency_score)

        urgency_class = (
            "urgency-high" if urgency_score >= 8 
            else "urgency-medium" if urgency_score >= 5 
            else "urgency-low"
        )
        st.markdown(f'<div class="{urgency_class}">', unsafe_allow_html=True)
        st.subheader(f"{urgency_emoji} Appointment Recommendation")

        col1, col2 = st.columns(2)
        col1.metric("Urgency Score", f"{urgency_score}/10")
        col1.info(f"📅 Timing: {suggestion['time_recommendation']}")
        col2.write(f"🔍 Key Symptoms: {suggestion['key_symptoms']}")
        col2.write(f"📝 Notes: {suggestion['notes']}")
        st.markdown('</div>', unsafe_allow_html=True)

        if urgency_score >= 9:
            st.error("🚨 EMERGENCY: Please seek immediate help.")

        if location and symptoms:
            specialist = infer_specialist(symptoms)
            maps_link = generate_google_maps_link(location, specialist)
            st.success(f"🔎 Suggested Specialist: **{specialist}**")
            st.markdown(f"🗺️ [Find nearby {specialist}s in Google Maps]({maps_link})", unsafe_allow_html=True)

        st.markdown("---")

        hospital = st.text_input("🏥 Preferred Hospital (optional)", value=st.session_state.form_hospital)
        st.session_state.form_hospital = hospital

        col1, col2 = st.columns([3, 1])
        col1.write("Ready to confirm booking?")
        if col2.button("📅 Book Appointment", use_container_width=True, disabled=st.session_state.appointment_booked):
            if book_appointment(name, age, location, symptoms, hospital, suggestion):
                st.session_state.appointment_booked = True
                st.success("🎉 Appointment successfully booked!")
                st.balloons()

                appointments = load_appointments()
                if appointments:
                    st.session_state.last_patient_id = str(appointments[-1]["id"])  # Save for upload module

                # Reset form state
                for key in ['form_name', 'form_age', 'form_location', 'form_symptoms', 'form_hospital']:
                    st.session_state[key] = ""

                st.session_state.show_suggestion = False
                st.session_state.current_suggestion = None

                st.info("Form reset. You can enter a new appointment.")

    # ✅ Show prescription upload module after booking (not on click)
    if st.session_state.get("appointment_booked") and st.session_state.get("last_patient_id"):
        run_prescription_module(st.session_state["last_patient_id"])





import pandas as pd

def view_appointments_tab():
    st.header("📋 Booked Appointments")

    appointments = load_appointments()
    if not appointments:
        st.info("📝 No appointments booked yet.")
        return

    valid_appointments = [a for a in appointments if "urgency_score" in a]
    if not valid_appointments:
        st.warning("No appointments with urgency data available.")
        return

    # Show appointment status alerts
    for appt in valid_appointments:
        if appt["status"] == "Accepted":
            st.success(f"✅ Your appointment with ID #{appt['id']} has been accepted.")
        elif appt["status"] == "Rejected":
            st.error(f"❌ Your appointment with ID #{appt['id']} has been rejected.")

    # Group by appointment for display
    for appt in valid_appointments:
        with st.expander(f"📄 Appointment #{appt['id']} - {appt['name']} ({appt['status']})"):
            st.write(f"**Age:** {appt['age']}")
            st.write(f"**Location:** {appt['location']}")
            st.write(f"**Symptoms:** {appt['symptoms']}")
            st.write(f"**Urgency Score:** {appt['urgency_score']}")
            st.write(f"**Time Recommendation:** {appt['time_recommendation']}")
            st.write(f"**Preferred Hospital:** {appt['preferred_hospital']}")
            st.write(f"**Booked On:** {appt['booking_time']}")
            st.write(f"**AI Notes:** {appt['notes']}")

            # 👉 NEW: Load doctor suggestions from file
            suggestions = []
            SUGGESTIONS_FILE = "suggestions.txt"
            patient_id = str(appt["id"])
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
                                suggestions.append((ts, fname, sugg))

            if suggestions:
                st.markdown("---")
                st.subheader("🧑‍⚕️ Suggestions from Doctor")
                for ts, fname, sugg in suggestions:
                    st.write(f"📄 **File:** {fname}")
                    st.write(f"💬 **Suggestion:** {sugg}")
                    st.caption(f"🕒 Submitted at {ts}")
            else:
                st.info("No suggestions from the doctor yet.")



def about_tab():
    st.header("ℹ️ About This App")
    st.markdown("""
    This AI-powered doctor appointment booking system:
    - Works offline with rule-based symptom urgency analysis.
    - Suggests medical specialists based on symptoms.
    - Provides Google Maps links to find nearby specialists.
    - Allows booking appointments and viewing them later.
    """)

if __name__ == "__main__":
    main()

