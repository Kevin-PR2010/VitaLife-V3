import streamlit as st
import uuid
import json
import os
from datetime import datetime
import re
import spacy
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

# Load spaCy model with robust error handling
try:
    nlp = spacy.load("en_core_web_sm")
    st.toast("Medical language model loaded successfully!", icon="✅")
except:
    try:
        import en_core_web_sm
        nlp = en_core_web_sm.load()
        st.toast("Loaded medical model from module", icon="✅")
    except Exception as e:
        st.error(f"Critical error loading medical model: {str(e)}")
        st.stop()

# Enhanced medical knowledge base
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

AUTO_FILL_PATTERNS = {
    r'\b(head\s*hurt|head\s*pain|migraine)\b': 'headache',
    r'\b(chest\s*hurt|heart\s*pain|chest\s*tightness)\b': 'chest pain',
    r'\b(feel\s*hot|high\s*temp|chills)\b': 'fever',
    r'\b(feel\s*sick|want\s*to\s*vomit|upset\s*stomach)\b': 'nausea',
    r'\b(dizzy|lightheaded|vertigo)\b': 'dizziness',
    r'\b(can\'t\s*breathe|short\s*of\s*breath|wheezing)\b': 'shortness of breath'
}

SYMPTOM_MAP = {
    "headache": ["throbbing pain", "sensitivity to light", "temple pressure"],
    "chest pain": ["pain radiating to arm", "sweating", "jaw pain"],
    "fever": ["body aches", "fatigue", "loss of appetite"],
    "nausea": ["abdominal cramps", "loss of appetite", "excess saliva"],
    "dizziness": ["spinning sensation", "loss of balance", "nausea"],
    "shortness of breath": ["rapid breathing", "coughing", "blue lips"]
}

def enhance_input(text):
    """Advanced auto-fill with NLP lemmatization and symptom mapping"""
    doc = nlp(text.lower())
    lemmatized = " ".join([token.lemma_ for token in doc])
    
    # Apply regex patterns
    for pattern, replacement in AUTO_FILL_PATTERNS.items():
        if re.search(pattern, lemmatized):
            return replacement
    
    # Semantic matching
    symptom_scores = {}
    for condition, data in MEDICAL_KNOWLEDGE.items():
        for symptom in data['symptoms'] + data.get('related', []):
            if symptom in lemmatized:
                symptom_scores[condition] = symptom_scores.get(condition, 0) + 1
    
    if symptom_scores:
        return max(symptom_scores, key=symptom_scores.get)
    
    return text

def detect_emergency(text):
    """Enhanced emergency detection with symptom severity analysis"""
    emergency_keywords = [
        'chest pain', 'heart attack', 'can\'t breathe', 'severe pain',
        'unconscious', 'bleeding heavily', 'overdose', 'suicide',
        'choking', 'paralysis', 'severe burn', 'head injury'
    ]
    
    # Severity indicators
    severity_phrases = [
        'excruciating', 'worst ever', 'unbearable', 'severe',
        'sudden intense', 'crippling', 'debilitating'
    ]
    
    text_lower = text.lower()
    emergency_detected = any(keyword in text_lower for keyword in emergency_keywords)
    severe_symptom = any(phrase in text_lower for phrase in severity_phrases)
    
    return emergency_detected or severe_symptom

def generate_suggestions(text):
    """Generate auto-fill suggestions based on partial input"""
    if not text:
        return []
    
    suggestions = []
    
    # Symptom completion
    for condition, symptoms in SYMPTOM_MAP.items():
        for symptom in symptoms:
            if text.lower() in symptom:
                suggestions.append(f"I have {symptom}")
    
    # Medical condition completion
    for condition in MEDICAL_KNOWLEDGE.keys():
        condition_words = condition.split()
        for i in range(1, len(condition_words)+1):
            partial = " ".join(condition_words[:i])
            if text.lower() in partial:
                suggestions.append(f"Information about {condition}")
    
    # Common questions
    common_phrases = [
        "What causes ",
        "How to treat ",
        "Home remedies for ",
        "When to see a doctor for "
    ]
    
    for phrase in common_phrases:
        if text.lower() in phrase.lower():
            suggestions.extend([f"{phrase}{cond}" for cond in MEDICAL_KNOWLEDGE.keys()])
    
    return list(set(suggestions))[:5]  # Return up to 5 unique suggestions

def get_medical_response(query, user_profile=None):
    """Enhanced medical response with NLP and personalized advice"""
    enhanced_query = enhance_input(query)
    
    # Check for emergency
    if detect_emergency(query):  # Use original query for better context
        return {
            'response': "🚨 **MEDICAL EMERGENCY DETECTED** 🚨\n\n"
                        "This appears to be a serious medical situation:\n"
                        "1. **Call emergency services immediately** (911/999/local emergency number)\n"
                        "2. Do NOT drive yourself to the hospital\n"
                        "3. If alone, contact a neighbor or family member\n"
                        "4. Stay on the line with emergency services\n\n"
                        "*This chatbot cannot provide emergency medical assistance*",
            'emergency': True,
            'confidence': 'HIGH',
            'condition': 'Emergency'
        }
    
    # Search knowledge base with NLP similarity
    best_match = None
    best_score = 0
    
    doc_query = nlp(query.lower())
    
    for condition, info in MEDICAL_KNOWLEDGE.items():
        # Check direct symptom matches
        for symptom in info['symptoms']:
            if symptom in query.lower():
                score = len(symptom) * 2  # Higher weight for exact matches
                if score > best_score:
                    best_score = score
                    best_match = info
                    best_match['condition'] = condition
        
        # Semantic similarity
        doc_condition = nlp(condition)
        similarity = doc_query.similarity(doc_condition)
        
        if similarity > 0.7 and similarity > best_score/100:
            best_score = similarity * 100
            best_match = info
            best_match['condition'] = condition
    
    if best_match:
        condition_name = best_match.get('condition', "your symptoms").title()
        response = f"## {condition_name}\n\n"
        response += f"**Advice:** {best_match['advice']}\n\n"
        
        # Add symptom suggestions
        response += "**Commonly Associated Symptoms:**\n"
        symptoms = SYMPTOM_MAP.get(best_match['condition'], [])
        for symptom in symptoms[:3]:
            response += f"- {symptom}\n"
        response += "\n"
        
        if user_profile:
            personalized = "\n**Personalized Recommendations:**\n"
            age = user_profile.get('age', 30)
            
            if 'heart' in condition_name.lower() or 'chest' in condition_name.lower():
                if age > 50:
                    personalized += "- Given your age, cardiac evaluation is especially important\n"
                if user_profile.get('medical_history', '').lower().find('cholesterol') != -1:
                    personalized += "- Your history of high cholesterol increases cardiac risk\n"
            
            if 'fever' in condition_name.lower() or 'infection' in condition_name.lower():
                if user_profile.get('allergies', '').lower().find('penicillin') != -1:
                    personalized += "- Note your penicillin allergy when discussing antibiotics\n"
            
            if personalized != "\n**Personalized Recommendations:**\n":
                response += personalized + "\n"
        
        response += "**Disclaimer:** This is general information only. Always consult a healthcare professional for proper diagnosis and treatment."
        
        return {
            'response': response,
            'emergency': best_match.get('emergency', False),
            'confidence': 'HIGH' if best_score > 50 else 'MEDIUM',
            'condition': condition_name
        }
    else:
        # Try to offer related suggestions
        all_symptoms = [symptom for data in MEDICAL_KNOWLEDGE.values() for symptom in data['symptoms']]
        matches = get_close_matches(query.lower(), all_symptoms, n=3, cutoff=0.4)
        
        if matches:
            suggestion_text = "**Did you mean:**\n" + "\n".join([f"- {m.title()}" for m in matches])
        else:
            suggestion_text = "Please try describing your symptoms in more detail."
        
        return {
            'response': f"## I understand you have a health concern\n\n"
                        f"While I couldn't find specific information, here's what I recommend:\n\n"
                        f"1. Track your symptoms including frequency and triggers\n"
                        f"2. Note any patterns (time of day, after meals, etc.)\n"
                        f"3. Contact your healthcare provider for evaluation\n\n"
                        f"{suggestion_text}\n\n"
                        f"**Disclaimer:** This is not medical advice. Always consult a healthcare professional.",
            'emergency': False,
            'confidence': 'LOW',
            'condition': 'Unknown'
        }

# Header with enhanced design
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
:root {
    --primary: #2c3e50;
    --secondary: #3498db;
    --accent: #e74c3c;
    --light: #ecf0f1;
    --emergency: #c0392b;
}
* {
    font-family: 'Roboto', sans-serif;
}
.header {
    text-align: center;
    padding: 20px;
    background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
    border-radius: 10px;
    margin-bottom: 20px;
    color: white;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
.header h1 {
    margin: 0;
    font-size: 2.5rem;
}
.header p {
    margin: 5px 0;
}
.emergency {
    background-color: #c0392b;
    padding: 10px;
    border-radius: 5px;
    font-weight: bold;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0% { opacity: 0.9; }
    50% { opacity: 0.7; }
    100% { opacity: 0.9; }
}
.chat-you {
    background-color: #e3f2fd;
    border-radius: 15px 15px 0 15px;
    padding: 12px;
    margin: 5px 0;
    max-width: 80%;
    align-self: flex-end;
}
.chat-bot {
    background-color: #f5f5f5;
    border-radius: 15px 15px 15px 0;
    padding: 12px;
    margin: 5px 0;
    max-width: 80%;
    align-self: flex-start;
}
.chat-emergency {
    background-color: #ffebee;
    border: 2px solid #c0392b;
    animation: pulse 1.5s infinite;
}
.suggest-button {
    margin: 3px;
    font-size: 0.85rem;
}
</style>

<div class="header">
    <h1>🏥 VitaLife Medical Assistant</h1>
    <p>AI-Powered Health Companion with Advanced Auto-Fill</p>
    <div class="emergency">⚠️ Not a substitute for professional medical advice</div>
</div>
""", unsafe_allow_html=True)

# Medical Disclaimer
with st.expander("⚠️ Important Medical Disclaimer", expanded=False):
    st.error("""
    **CRITICAL MEDICAL DISCLAIMER**
    
    This chatbot provides general health information only and is **NOT** a substitute for professional medical advice, diagnosis, or treatment. 
    
    **ALWAYS SEEK** the advice of your physician or qualified health provider with any medical questions. 
    
    **NEVER DISREGARD** professional medical advice or delay seeking it because of information from this chatbot.
    
    **IN CASE OF EMERGENCY**: 
    - Call your local emergency number immediately
    - Go to the nearest emergency department
    - Contact your primary care provider
    """)

# Main tabs
tab1, tab2, tab3 = st.tabs(["💬 Chat", "👤 Profile", "📊 Analytics"])

with tab1:
    st.header("Medical Chat Interface")
    
    # User info with auto-profile
    col1, col2 = st.columns([2, 1])
    with col1:
        user_id = st.text_input("User ID:", value=st.session_state.current_user_id, 
                               help="Your unique ID for personalized responses")
    
    with col2:
        auto_fill = st.toggle("Smart Assist", value=True, 
                             help="Automatically enhance your input with medical terminology")
    
    # Auto-fill suggestions row
    if st.session_state.suggestions:
        st.subheader("Suggestions:")
        cols = st.columns(len(st.session_state.suggestions))
        for i, suggestion in enumerate(st.session_state.suggestions):
            with cols[i]:
                if st.button(suggestion, key=f"sug_{i}", use_container_width=True, 
                            help="Click to use this suggestion"):
                    st.session_state.user_input = suggestion
                    st.session_state.suggestions = []
    
    # User input with auto-complete
    user_input = st.text_area(
        "Describe your symptoms:",
        value=st.session_state.get('user_input', ''),
        placeholder="Start typing symptoms (e.g. 'head pain')...",
        height=100,
        key="input_area"
    )
    
    # Real-time auto-fill and suggestions
    if auto_fill and user_input:
        st.session_state.user_input = enhance_input(user_input)
        st.session_state.suggestions = generate_suggestions(user_input)
        st.rerun()
    
    # Buttons with enhanced options
    col1, col2, col3, col4 = st.columns([2,1,1,1])
    with col1:
        send_button = st.button("Send Message", type="primary", use_container_width=True)
    with col2:
        clear_button = st.button("Clear Chat", use_container_width=True)
    with col3:
        examples_button = st.button("Examples", use_container_width=True,
                                  help="Show example questions")
    with col4:
        voice_button = st.button("Voice Input", use_container_width=True,
                               help="Enable voice input (simulated)")
    
    if voice_button:
        st.session_state.show_voice = not st.session_state.show_voice
    
    if st.session_state.show_voice:
        voice_options = st.selectbox("Select voice command:", [
            "I have a severe headache",
            "Chest pain and dizziness",
            "Fever with body aches",
            "Nausea after eating",
            "Shortness of breath when walking"
        ])
        if st.button("Use Voice Command"):
            st.session_state.user_input = voice_options
            st.rerun()
    
    if examples_button:
        st.session_state.suggestions = [
            "I have a throbbing headache",
            "Chest tightness when exercising",
            "Fever of 101°F for two days",
            "Feeling dizzy when standing up",
            "Persistent cough with shortness of breath"
        ]
        st.rerun()
    
    if clear_button:
        st.session_state.chat_history = []
        st.session_state.suggestions = []
        st.session_state.user_input = ""
        st.rerun()
    
    if send_button and user_input:
        # Get user profile if available
        user_profile = st.session_state.user_profiles.get(user_id)
        
        # Get response
        response_data = get_medical_response(user_input, user_profile)
        
        # Add to chat history
        st.session_state.chat_history.append({
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'user_input': user_input,
            'response': response_data['response'],
            'emergency': response_data['emergency'],
            'confidence': response_data['confidence'],
            'condition': response_data.get('condition', 'Unknown')
        })
        
        st.session_state.user_input = ""
        st.session_state.suggestions = []
        st.rerun()
    
    # Enhanced chat display
    st.subheader("Conversation History")
    
    if st.session_state.chat_history:
        for chat in reversed(st.session_state.chat_history[-8:]):  # Show last 8 messages
            # User message
            st.markdown(f"""
            <div class="chat-you">
                <strong>You</strong> ({chat['timestamp']}):<br>
                {chat['user_input']}
            </div>
            """, unsafe_allow_html=True)
            
            # Bot response
            chat_class = "chat-bot"
            if chat['emergency']:
                chat_class += " chat-emergency"
            
            st.markdown(f"""
            <div class="{chat_class}">
                <strong>VitaLife</strong> [{chat['confidence']}]:<br>
                {chat['response']}
            </div>
            """, unsafe_allow_html=True)
            
            st.divider()
    else:
        st.info("💬 Start by describing your symptoms. Try 'I have a headache'")

with tab2:
    st.header("👤 User Profile Management")
    
    # Check if profile exists
    profile_exists = user_id in st.session_state.user_profiles
    profile_data = st.session_state.user_profiles.get(user_id, {})
    
    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name:", value=profile_data.get('name', ''))
            age = st.number_input("Age:", min_value=0, max_value=120, 
                                 value=profile_data.get('age', 30))
            gender = st.selectbox("Gender:", ["Prefer not to say", "Female", "Male", "Non-binary", "Other"],
                                index=0 if 'gender' not in profile_data else 
                                ["Prefer not to say", "Female", "Male", "Non-binary", "Other"].index(profile_data['gender']))
            
        with col2:
            height = st.number_input("Height (cm):", min_value=100, max_value=250, 
                                    value=profile_data.get('height', 170))
            weight = st.number_input("Weight (kg):", min_value=30, max_value=300, 
                                    value=profile_data.get('weight', 70))
            blood_type = st.selectbox("Blood Type:", ["Unknown", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
                                    index=0 if 'blood_type' not in profile_data else 
                                    ["Unknown", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"].index(profile_data['blood_type']))
        
        medical_history = st.text_area("Medical History:", 
                                      value=profile_data.get('medical_history', ''),
                                      placeholder="e.g., Diabetes, Hypertension, Asthma...")
        
        medications = st.text_area("Current Medications:", 
                                  value=profile_data.get('medications', ''),
                                  placeholder="e.g., Metformin 500mg daily, Lisinopril 10mg...")
        
        allergies = st.text_input("Known Allergies:", 
                                 value=profile_data.get('allergies', ''),
                                 placeholder="e.g., Penicillin, Shellfish, Latex...")
        
        # Form actions
        col1, col2, col3 = st.columns(3)
        with col1:
            save_profile = st.form_submit_button("💾 Save Profile", type="primary")
        with col2:
            clear_profile = st.form_submit_button("🧹 Clear Form")
        with col3:
            delete_profile = st.form_submit_button("🗑️ Delete Profile")
        
        if save_profile:
            profile_data = {
                'name': name,
                'age': age,
                'gender': gender,
                'height': height,
                'weight': weight,
                'blood_type': blood_type,
                'medical_history': medical_history,
                'medications': medications,
                'allergies': allergies,
                'last_updated': datetime.now().isoformat()
            }
            st.session_state.user_profiles[user_id] = profile_data
            st.success(f"Profile saved for {name} (ID: {user_id})")
        
        if clear_profile:
            st.session_state.user_profiles[user_id] = {}
            st.rerun()
        
        if delete_profile:
            if user_id in st.session_state.user_profiles:
                del st.session_state.user_profiles[user_id]
                st.success(f"Profile deleted for ID: {user_id}")
            else:
                st.warning("No profile found for this ID")
    
    # Profile summary card
    if profile_exists:
        st.divider()
        st.subheader("Profile Summary")
        
        profile = st.session_state.user_profiles[user_id]
        bmi = profile.get('weight', 0) / ((profile.get('height', 1) / 100) ** 2) if profile.get('height') else 0
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Name", profile.get('name', 'Unknown'))
            st.metric("Age", profile.get('age', 'N/A'))
            st.metric("Blood Type", profile.get('blood_type', 'Unknown'))
            
        with col2:
            st.metric("Height", f"{profile.get('height', 'N/A')} cm")
            st.metric("Weight", f"{profile.get('weight', 'N/A')} kg")
            st.metric("BMI", f"{bmi:.1f} ({'Healthy' if 18.5 <= bmi <= 24.9 else 'Consult doctor'})")
        
        if profile.get('medical_history'):
            with st.expander("Medical History"):
                st.write(profile['medical_history'])
        
        if profile.get('allergies'):
            st.warning(f"⚠️ Allergies: {profile['allergies']}")

with tab3:
    st.header("📊 Health Analytics")
    
    if not st.session_state.chat_history:
        st.info("No chat history available for analytics")
    else:
        # Basic metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Chats", len(st.session_state.chat_history))
        with col2:
            emergencies = sum(1 for c in st.session_state.chat_history if c['emergency'])
            st.metric("Emergency Detections", emergencies)
        with col3:
            st.metric("Registered Users", len(st.session_state.user_profiles))
        with col4:
            avg_confidence = np.mean([0.8 if c['confidence'] == 'HIGH' else 0.5 if c['confidence'] == 'MEDIUM' else 0.2 
                                     for c in st.session_state.chat_history])
            st.metric("Avg. Confidence", f"{avg_confidence*100:.1f}%")
        
        # Condition distribution
        st.subheader("Symptom Analysis")
        condition_count = {}
        for chat in st.session_state.chat_history:
            cond = chat.get('condition', 'Unknown')
            condition_count[cond] = condition_count.get(cond, 0) + 1
        
        if condition_count:
            fig, ax = plt.subplots()
            ax.pie(condition_count.values(), labels=condition_count.keys(), autopct='%1.1f%%',
                  colors=['#3498db', '#2ecc71', '#e74c3c', '#9b59b6', '#f39c12'])
            ax.axis('equal')
            st.pyplot(fig)
        else:
            st.warning("No symptom data available")
        
        # Recent activity
        st.subheader("Recent Conversations")
        for chat in st.session_state.chat_history[-5:]:
            with st.expander(f"{chat['timestamp']} - {chat['user_input'][:50]}..."):
                st.write(f"**Condition:** {chat.get('condition', 'Unknown')}")
                st.write(f"**Confidence:** {chat['confidence']}")
                st.write(f"**Emergency:** {'Yes' if chat['emergency'] else 'No'}")
                st.divider()
                st.write(chat['response'])

# Enhanced sidebar
with st.sidebar:
    st.header("⚡ Quick Actions")
    
    if st.button("🆕 Generate New User ID", use_container_width=True):
        st.session_state.current_user_id = str(uuid.uuid4())[:8]
        st.success(f"New ID: {st.session_state.current_user_id}")
        st.rerun()
    
    st.divider()
    st.write(f"**Current User ID:** `{st.session_state.current_user_id}`")
    
    if st.session_state.user_profiles.get(st.session_state.current_user_id):
        profile = st.session_state.user_profiles[st.session_state.current_user_id]
        st.subheader(f"👤 {profile.get('name', 'User')}")
        st.caption(f"Age: {profile.get('age', 'N/A')} | Blood: {profile.get('blood_type', 'Unknown')}")
    
    st.divider()
    st.header("💡 Symptom Suggestions")
    
    # Quick symptom buttons
    symptoms = ["Headache", "Fever", "Chest Pain", "Nausea", "Dizziness"]
    cols = st.columns(2)
    for i, symptom in enumerate(symptoms):
        with cols[i % 2]:
            if st.button(f"🤒 {symptom}", key=f"qs_{i}", use_container_width=True):
                st.session_state.user_input = f"I have {symptom.lower()}"
                st.rerun()
    
    st.divider()
    st.header("📚 Medical Resources")
    st.markdown("""
    - [CDC Health Topics](https://www.cdc.gov)
    - [Mayo Clinic Symptoms](https://www.mayoclinic.org)
    - [MedlinePlus](https://medlineplus.gov)
    - [WHO Health Advice](https://www.who.int)
    """)
    
    st.divider()
    st.header("ℹ️ About VitaLife")
    st.info("""
    **AI-Powered Medical Assistant v3.0**
    
    Features:
    - Advanced symptom analysis
    - Medical terminology auto-fill
    - Emergency detection
    - Personalized health profiles
    - Conversation analytics
    
    *This application is for educational purposes only*
    """)
