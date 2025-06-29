import streamlit as st
import uuid
import json
import os
from datetime import datetime
import re

# Page configuration
st.set_page_config(
    page_title="VitaLife Medical Chatbot",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'user_profiles' not in st.session_state:
    st.session_state.user_profiles = {}
if 'current_user_id' not in st.session_state:
    st.session_state.current_user_id = str(uuid.uuid4())[:8]

# Medical knowledge base (simplified)
MEDICAL_KNOWLEDGE = {
    "headache": {
        "symptoms": ["head pain", "migraine", "tension headache"],
        "advice": "Rest in a quiet, dark room. Stay hydrated. Consider over-the-counter pain relievers if appropriate.",
        "emergency": False
    },
    "chest_pain": {
        "symptoms": ["chest pain", "heart pain", "chest pressure"],
        "advice": "Seek immediate medical attention for chest pain.",
        "emergency": True
    },
    "fever": {
        "symptoms": ["high temperature", "fever", "hot", "chills"],
        "advice": "Rest, stay hydrated, monitor temperature. Seek medical care if fever persists or is very high.",
        "emergency": False
    },
    "nausea": {
        "symptoms": ["nausea", "vomiting", "sick stomach", "queasy"],
        "advice": "Rest, sip clear fluids, try bland foods. Avoid solid foods until feeling better.",
        "emergency": False
    }
}

AUTO_FILL_PATTERNS = {
    r'\b(head\s*hurt|head\s*pain)\b': 'headache',
    r'\b(chest\s*hurt|heart\s*pain)\b': 'chest pain',
    r'\b(feel\s*hot|high\s*temp)\b': 'fever',
    r'\b(feel\s*sick|want\s*to\s*vomit)\b': 'nausea'
}

def enhance_input(text):
    """Auto-fill and enhance user input with medical terminology"""
    enhanced = text.lower()
    for pattern, replacement in AUTO_FILL_PATTERNS.items():
        enhanced = re.sub(pattern, replacement, enhanced, flags=re.IGNORECASE)
    return enhanced

def detect_emergency(text):
    """Detect emergency situations"""
    emergency_keywords = [
        'chest pain', 'heart attack', 'can\'t breathe', 'severe pain',
        'unconscious', 'bleeding heavily', 'overdose', 'suicide'
    ]
    return any(keyword in text.lower() for keyword in emergency_keywords)

def get_medical_response(query, user_profile=None):
    """Generate medical response based on query and user profile"""
    enhanced_query = enhance_input(query)
    
    # Check for emergency
    if detect_emergency(enhanced_query):
        return {
            'response': "🚨 **EMERGENCY DETECTED** 🚨\n\nThis appears to be a medical emergency. Please:\n• Call emergency services immediately (911/999/local emergency number)\n• Seek immediate medical attention\n• Do not delay professional medical care\n\nThis chatbot cannot provide emergency medical treatment.",
            'emergency': True,
            'confidence': 'HIGH'
        }
    
    # Search knowledge base
    best_match = None
    best_score = 0
    
    for condition, info in MEDICAL_KNOWLEDGE.items():
        for symptom in info['symptoms']:
            if symptom in enhanced_query:
                score = len(symptom)
                if score > best_score:
                    best_score = score
                    best_match = info
    
    if best_match:
        response = f"Based on your symptoms, here's some general information:\n\n"
        response += f"**Advice:** {best_match['advice']}\n\n"
        
        if user_profile:
            response += f"**Personalized Note:** Given your profile (Age: {user_profile.get('age', 'N/A')}), "
            if user_profile.get('medical_history'):
                response += f"and medical history of {user_profile['medical_history']}, "
            response += "please consider consulting with your healthcare provider.\n\n"
        
        response += "**Disclaimer:** This is general information only. Always consult a healthcare professional for proper diagnosis and treatment."
        
        return {
            'response': response,
            'emergency': best_match.get('emergency', False),
            'confidence': 'MEDIUM'
        }
    else:
        return {
            'response': "I understand you have a health concern. While I can provide general health information, I recommend consulting with a healthcare professional for proper evaluation and advice specific to your situation.",
            'emergency': False,
            'confidence': 'LOW'
        }

# Header
st.markdown("""
<div style="text-align: center; padding: 20px; background-color: #f0f8ff; border-radius: 10px; margin-bottom: 20px;">
    <h1 style="color: #2c3e50; margin: 0;">🏥 VitaLife Medical Chatbot</h1>
    <p style="color: #7f8c8d; margin: 5px 0;">AI-Powered Health Assistant with Auto-Fill & Profile Management</p>
    <p style="color: #e74c3c; font-weight: bold; margin: 5px 0;">⚠️ For informational purposes only - Not a substitute for professional medical advice</p>
</div>
""", unsafe_allow_html=True)

# Medical Disclaimer
with st.expander("⚠️ Important Medical Disclaimer", expanded=False):
    st.warning("""
    **IMPORTANT MEDICAL DISCLAIMER**
    
    This chatbot provides general health information only and is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition. Never disregard professional medical advice or delay in seeking it because of something you have read here.
    
    **IN CASE OF EMERGENCY**: Call your local emergency number immediately.
    """)

# Main tabs
tab1, tab2, tab3 = st.tabs(["💬 Chat", "👤 Profile", "📊 Analytics"])

with tab1:
    st.header("🏥 Medical Chatbot Interface")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        user_id = st.text_input("User ID (Optional):", value=st.session_state.current_user_id, help="Enter your user ID for personalized responses")
        auto_fill = st.checkbox("Enable Auto-fill & Enhancement", value=True, help="Automatically enhances your input with medical terminology")
    
    # User input
    user_input = st.text_area(
        "Your Input:",
        placeholder="Describe your symptoms or ask a medical question...\nExample: 'I have a headache and feel nauseous'",
        height=100
    )
    
    # Buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        send_button = st.button("Send", type="primary")
    with col2:
        clear_button = st.button("Clear Chat")
    with col3:
        suggestions_button = st.button("Get Suggestions")
    
    # Handle button clicks
    if clear_button:
        st.session_state.chat_history = []
        st.rerun()
    
    if suggestions_button:
        st.info("""
        **Example Questions:**
        - "I have a severe headache and feel nauseous"
        - "Chest pain and shortness of breath"
        - "What is normal blood pressure?"
        - "How to prevent common cold?"
        - "Tired and no energy for days"
        - "Sharp pain in abdomen"
        """)
    
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
            'confidence': response_data['confidence']
        })
        
        st.rerun()
    
    # Display chat history
    st.subheader("Chat History")
    chat_container = st.container()
    
    with chat_container:
        if st.session_state.chat_history:
            for i, chat in enumerate(reversed(st.session_state.chat_history[-10:])):  # Show last 10 messages
                with st.expander(f"[{chat['timestamp']}] {chat['user_input'][:50]}...", expanded=(i==0)):
                    st.write(f"**You:** {chat['user_input']}")
                    
                    if chat['emergency']:
                        st.error(chat['response'])
                    else:
                        st.write(f"**VitaLife:** {chat['response']}")
                    
                    st.caption(f"Confidence: {chat['confidence']}")
        else:
            st.info("No chat history yet. Start by asking a medical question!")

with tab2:
    st.header("👤 User Profile Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        profile_user_id = st.text_input("User ID:", value=st.session_state.current_user_id)
        name = st.text_input("Name:", placeholder="Your name")
        age = st.number_input("Age:", min_value=0, max_value=120, value=30)
        gender = st.selectbox("Gender:", ["Prefer not to say", "Female", "Male", "Other"])
    
    with col2:
        medical_history = st.text_area("Medical History:", placeholder="e.g., diabetes, hypertension, asthma (separate by commas)", height=100)
        medications = st.text_area("Current Medications:", placeholder="Current medications (separate by commas)", height=80)
        allergies = st.text_input("Known Allergies:", placeholder="Known allergies (separate by commas)")
    
    col1, col2 = st.columns(2)
    with col1:
        save_profile = st.button("Save Profile", type="primary")
    with col2:
        load_profile = st.button("Load Profile")
    
    if save_profile:
        profile_data = {
            'name': name,
            'age': age,
            'gender': gender,
            'medical_history': medical_history,
            'medications': medications,
            'allergies': allergies,
            'created_at': datetime.now().isoformat()
        }
        st.session_state.user_profiles[profile_user_id] = profile_data
        st.success(f"Profile saved successfully for User ID: {profile_user_id}")
    
    if load_profile:
        if profile_user_id in st.session_state.user_profiles:
            profile = st.session_state.user_profiles[profile_user_id]
            st.success("Profile loaded successfully!")
            st.json(profile)
        else:
            st.error("Profile not found for this User ID")
    
    # Display all profiles
    if st.session_state.user_profiles:
        st.subheader("Saved Profiles")
        for uid, profile in st.session_state.user_profiles.items():
            with st.expander(f"User: {profile.get('name', 'Unknown')} (ID: {uid})"):
                st.json(profile)

with tab3:
    st.header("📊 Analytics Dashboard")
    
    if st.button("Generate Analytics"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Conversations", len(st.session_state.chat_history))
        
        with col2:
            emergency_count = sum(1 for chat in st.session_state.chat_history if chat.get('emergency', False))
            st.metric("Emergency Detections", emergency_count)
        
        with col3:
            st.metric("Registered Users", len(st.session_state.user_profiles))
        
        if st.session_state.chat_history:
            st.subheader("Recent Activity")
            recent_chats = st.session_state.chat_history[-5:]
            for chat in recent_chats:
                st.write(f"**{chat['timestamp']}** - {chat['user_input'][:100]}...")
        
        st.subheader("System Information")
        st.info("""
        **VitaLife Medical Chatbot v2.0**
        - Diseases covered: 4 (Headache, Chest Pain, Fever, Nausea)
        - Auto-fill patterns: 4
        - Features: Profile management, Emergency detection, Analytics
        - Emergency detection: Active
        - Auto-fill enhancement: Active
        """)

# Sidebar
with st.sidebar:
    st.header("🔧 Quick Actions")
    
    if st.button("🆕 New User ID"):
        st.session_state.current_user_id = str(uuid.uuid4())[:8]
        st.rerun()
    
    st.write(f"**Current User ID:** `{st.session_state.current_user_id}`")
    
    st.header("📋 Quick Examples")
    examples = [
        "I have a severe headache and feel nauseous",
        "Chest pain and shortness of breath",
        "What is normal blood pressure?",
        "How to prevent common cold?",
        "Tired and no energy for days"
    ]
    
    for example in examples:
        if st.button(f"💬 {example[:30]}...", key=f"example_{hash(example)}"):
            st.session_state.example_input = example
    
    st.header("ℹ️ About")
    st.info("""
    VitaLife is an AI-powered medical chatbot designed to provide general health information and assist with symptom assessment.
    
    **Features:**
    - Auto-fill medical terminology
    - Emergency situation detection
    - User profile management
    - Chat history tracking
    - Analytics dashboard
    
    **Remember:** Always consult healthcare professionals for medical advice.
    """)