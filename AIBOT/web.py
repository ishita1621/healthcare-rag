import streamlit as st
import os
import re
import json
import difflib
import faiss
import pickle
import numpy as np
from transformers import pipeline
from sentence_transformers import SentenceTransformer
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from util import validate_login, register_user, change_password

# Load style
if os.path.exists("style.css"):
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# App Config
st.set_page_config(page_title="Smart Healthcare Chatbot (LLM + RAG)", page_icon="🩺")

# Session State Init
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "patient_id" not in st.session_state:
    st.session_state.patient_id = ""

# Load RAG components
@st.cache_resource
def load_rag():
    loader = PyPDFLoader("data/Symptom_Disease_Specialist_Summary.pdf")
    documents = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(documents)
    texts = [chunk.page_content for chunk in chunks]

    # Debug print
    print(f"Total chunks loaded: {len(texts)}")
    for i, chunk in enumerate(texts[:5]):
        print(f"Chunk {i} →", chunk[:300])

    # Check if 'fever' appears
    fever_chunks = [c for c in texts if "fever" in c.lower()]
    print("Fever found in chunks:", len(fever_chunks))
    if fever_chunks:
        print(fever_chunks[0][:300])

    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = embedder.encode(texts)
    index = faiss.IndexFlatL2(embeddings[0].shape[0])
    index.add(embeddings)

    qa_pipeline = pipeline("question-answering", model="deepset/roberta-base-squad2")
    return texts, index, embedder, qa_pipeline

chunks, index, embedder, qa_pipeline = load_rag()

# Normalize vague or user-friendly questions to structured ones
def normalize_question(user_input):
    if "i have" in user_input.lower():
        # Try to normalize advice-seeking to condition-query
        symptom = user_input.lower().replace("what can i do if i have ", "").replace("?", "").strip()
        return f"What are the possible conditions related to {symptom}?"
    return user_input

# QA function using Hugging Face + RAG
# QA function using Hugging Face + RAG
def answer_with_llm(symptom):
    query_embedding = embedder.encode([symptom])
    D, I = index.search(np.array(query_embedding), k=3)
    top_chunks = [chunks[i] for i in I[0]]

    print("Top chunks returned by FAISS:")
    for chunk in top_chunks:
        print(chunk[:300])
    
    answers = []
    for context in top_chunks:
        result = qa_pipeline(question=symptom, context=context)
        print("LLM Raw Output:", result)  # 🧠 See the raw answer even if it's filtered

        if result["score"] > 0.1:  # 🔽 Lowered threshold to allow more answers
            answers.append((result["answer"], result["score"]))

    if answers:
        best = max(answers, key=lambda x: x[1])
        return best[0]
    return None

# Login UI
if not st.session_state.logged_in:
    st.title("Smart Healthcare Portal (LLM + RAG)")

    tab1, tab2, tab3 = st.tabs(["Login", "Sign Up", "Change Password"])

    with tab1:
        st.subheader("Patient Login")
        pid = st.text_input("Patient ID", key="login_pid")
        pw = st.text_input("Password", type="password", key="login_pw")
        if st.button("Login"):
            if validate_login(pid, pw):
                st.session_state.logged_in = True
                st.session_state.patient_id = pid
                st.success("✅ Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials.")

    with tab2:
        st.subheader("New Patient Registration")
        new_pid = st.text_input("Choose Patient ID", key="signup_pid")
        new_email = st.text_input("Your Email", key="signup_email")
        new_pw = st.text_input("Password", type="password", key="signup_pw")
        confirm_pw = st.text_input("Confirm Password", type="password", key="signup_confirm")
        if st.button("Register"):
            if new_pw != confirm_pw:
                st.error("Passwords don't match!")
            elif register_user(new_pid, new_email, new_pw):
                st.success("Registered successfully! Please log in.")
            else:
                st.error("Patient ID already exists.")

    with tab3:
        st.subheader("Change Password")
        ch_pid = st.text_input("Patient ID", key="change_pid")
        old_pw = st.text_input("Current Password", type="password", key="change_old")
        new_pw2 = st.text_input("New Password", type="password", key="change_new")
        confirm_pw2 = st.text_input("Confirm New Password", type="password", key="change_confirm")
        if st.button("Change Password"):
            if new_pw2 != confirm_pw2:
                st.error("New passwords don't match!")
            elif change_password(ch_pid, old_pw, new_pw2):
                st.success("Password changed successfully!")
            else:
                st.error("Incorrect Patient ID or password.")
else:
    st.markdown(f"""
    <div style="text-align: center;">
        <h1>AI-Powered Healthcare Chatbot (LLM + RAG)</h1>
        <p>Welcome, <b>{st.session_state.patient_id}</b>! Describe your symptoms, and get expert-level triage support.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.patient_id = ""
        st.rerun()

    user_input = st.text_input("Enter your symptom or question:")

    if user_input:
        with st.spinner("Analyzing with LLM..."):
            question = normalize_question(user_input)
            response = answer_with_llm(question)
            if response:
                st.success(f"💡 LLM Suggestion: {response}")
                if st.button("Book Appointment"):
                    st.session_state.symptom_to_forward = user_input
                    st.switch_page("pages/main.py")
            else:
                st.warning("No relevant information found.")
