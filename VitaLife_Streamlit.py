import streamlit as st
import uuid
import json
import os
from datetime import datetime
import re
import spacy
import time  # Added for retry mechanism
from difflib import get_close_matches
import matplotlib.pyplot as plt
import numpy as np

# Page configuration
st.set_page_config(
    page_title="VitaLife Medical Chatbot",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://medical.example.com',
        'Report a bug': "https://example.com/bug",
        'About': "# VitaLife AI Medical Assistant"
    }
)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'user_profiles' not in st.session_state:
    st.session_state.user_profiles = {}
if 'current_user_id' not in st.session_state:
    st.session_state.current_user_id = str(uuid.uuid4())[:8]
if 'suggestions' not in st.session_state:
    st.session_state.suggestions = []
if 'show_voice' not in st.session_state:
    st.session_state.show_voice = False

# Robust spaCy model loading with retries
nlp = None
max_retries = 3
retry_delay = 5  # seconds

for attempt in range(max_retries):
    try:
        nlp = spacy.load("en_core_web_sm")
        st.toast(f"Medical language model loaded successfully! (Attempt {attempt+1})", icon="✅")
        break
    except Exception as e:
        if attempt < max_retries - 1:
            st.warning(f"Model loading failed, retrying in {retry_delay} seconds... ({attempt+1}/{max_retries})")
            time.sleep(retry_delay)
        else:
            try:
                import en_core_web_sm
                nlp = en_core_web_sm.load()
                st.toast("Loaded medical model from module", icon="✅")
            except:
                st.error(f"Critical error loading medical model: {str(e)}")
                st.error("Please ensure 'en_core_web_sm' is installed. Run:")
                st.code("python -m spacy download en_core_web_sm")
                st.stop()

# Enhanced medical knowledge base (same as before)
MEDICAL_KNOWLEDGE = {
    "headache": {
        "symptoms": ["head pain", "migraine", "tension headache", "throbbing head", "cluster headache"],
        "advice": "Rest in a quiet, dark room. Stay hydrated. Consider over-the-counter pain relievers if appropriate. Apply a cool compress to your forehead.",
        "emergency": False,
        "related": ["migraine", "tension", "sinusitis"]
    },
    "chest_pain": {
        "symptoms": ["chest pain", "heart pain", "chest pressure", "tightness in chest", "angina"],
        "advice": "Seek immediate medical attention for chest pain. Sit down and try to remain calm. Do not attempt to drive yourself to the hospital.",
        "emergency": True,
        "related": ["heart attack", "angina", "pulmonary embolism"]
    },
    "fever": {
        "symptoms": ["high temperature", "fever", "hot", "chills", "sweating"],
        "advice": "Rest, stay hydrated with water or electrolyte solutions, monitor temperature regularly. Use cool compresses. Seek medical care if fever exceeds 103°F (39.4°C) or lasts more than 3 days.",
        "emergency": False,
        "related": ["infection", "flu", "covid-19"]
    },
    "nausea": {
        "symptoms": ["nausea", "vomiting", "sick stomach", "queasy", "upset stomach"],
        "advice": "Rest, sip clear fluids like ginger tea or broth, try bland foods like crackers or toast. Avoid strong smells, fatty foods, and dairy products.",
        "emergency": False,
        "related": ["food poisoning", "morning sickness", "gastroenteritis"]
    },
    "dizziness": {
        "symptoms": ["dizzy", "lightheaded", "vertigo", "unsteady", "woozy"],
        "advice": "Sit or lie down immediately to prevent falls. Stay hydrated. Avoid sudden movements. If accompanied by chest pain or numbness, seek emergency care.",
        "emergency": False,
        "related": ["vertigo", "dehydration", "low blood pressure"]
    },
    "shortness of breath": {
        "symptoms": ["short of breath", "difficulty breathing", "can't catch breath", "wheezing"],
        "advice": "Sit upright in a comfortable position. If severe, call emergency services immediately. Avoid exertion and try to remain calm.",
        "emergency": True,
        "related": ["asthma", "copd", "pneumonia"]
    }
}

# Rest of the application remains unchanged from here...
# [Include all the remaining code exactly as you originally provided]
# [From AUTO_FILL_PATTERNS to the end of the file]
