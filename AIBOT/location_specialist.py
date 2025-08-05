import urllib.parse
import streamlit as st
# Inject background image using inline CSS


import os



# Load global style
if os.path.exists("style.css"):
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)



# Map some keywords to specialists
SPECIALIST_KEYWORDS = {
    "cardiologist": ["chest pain", "heart", "cardiac", "palpitations", "blood pressure", "cardiovascular"],
    "dermatologist": ["rash", "skin", "acne", "eczema", "psoriasis", "itching", "blister"],
    "neurologist": ["headache", "migraine", "seizure", "dizziness", "numbness", "stroke", "neuropathy"],
    "orthopedic": ["bone", "fracture", "joint", "arthritis", "sprain", "back pain"],
    "pulmonologist": ["breathing", "asthma", "cough", "lung", "bronchitis", "shortness of breath"],
    "gastroenterologist": ["stomach", "abdominal pain", "diarrhea", "constipation", "nausea", "vomiting", "liver"],
    "psychiatrist": ["depression", "anxiety", "suicide", "mental health", "stress"],
    "general practitioner": []  # fallback if no match
}

def infer_specialist(symptoms: str) -> str:
    symptoms_lower = symptoms.lower()
    scores = {specialist: 0 for specialist in SPECIALIST_KEYWORDS}

    for specialist, keywords in SPECIALIST_KEYWORDS.items():
        for keyword in keywords:
            if keyword in symptoms_lower:
                scores[specialist] += 1

    # Pick the specialist with the highest keyword match count
    best_specialist = max(scores, key=scores.get)

    # If no keyword matched (all zero), fallback to General Practitioner
    if scores[best_specialist] == 0:
        return "General Practitioner"
    return best_specialist.capitalize()

def generate_google_maps_link(location: str, specialist: str) -> str:
    base_url = "https://www.google.com/maps/search/"
    query = f"{specialist} near {location}"
    url = base_url + urllib.parse.quote(query)
    return url