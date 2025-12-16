import streamlit as st
import google.generativeai as genai
import re
import datetime
import random
import os
import PyPDF2
from dotenv import load_dotenv

# --- 0. SETUP & CONFIGURATION ---
load_dotenv() # Loads the API key from the .env file

st.set_page_config(
    page_title="The Dauthority",
    page_icon="🦁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS: Dark Mode Friendly + Big Mobile Buttons
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3em;
        font-weight: bold;
        transition: transform 0.1s;
    }
    .stButton>button:active {
        transform: scale(0.98);
    }
    .report-box {
        padding: 15px;
        border-radius: 10px;
        background-color: #262730; /* Dark mode safe gray */
        border-left: 5px solid #ff4b4b;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. THE BRAIN (LOGIC LAYER) ---

def get_funny_spinner():
    """Returns a random loading message to keep spirits high."""
    phrases = [
        "Consulting the Oracle of 7th Ave...",
        "Translating 'Floor Scream' to 'Corporate Speak'...",
        "Checking if this is legal... one sec...",
        "Summoning the patience you don't have...",
        "Herding the digital cats...",
        "Polishing your brilliance...",
        "Lawyering up...",
        "Asking the ghost in the machine..."
    ]
    return random.choice(phrases)

def scrub_pii(text):
    """
    Privacy Air Gap: Removes Phone Numbers and Names before sending to AI.
    """
    if not text: return ""
    # Redact Phone Numbers
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE_REDACTED]', text)
    # Redact Names (Pattern: Capitalized words not at start of sentence)
    text = re.sub(r'(?<!^)(?<!\.\s)\b[A-Z][a-z]+\s[A-Z][a-z]+\b', '[CLIENT_NAME]', text)
    return text

def extract_text_from_pdf(uploaded_file):
    """Parses text from uploaded PDF manuals."""
    try:
        reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        return f"Error reading PDF: {e}"

# THE HARD SCAFFOLDING (Alberta Law Injection)
REGULATORY_CONTEXT = """
SYSTEM MANDATE: You are 'The Dauthority', a Shift Supervisor Assistant for the Calgary Drop-In Center.
Your goal is to protect the user from liability, ensure staff safety, and maintain professional standards.

CRITICAL LEGAL FRAMEWORK (ALBERTA/CALGARY):
1. MENTAL HEALTH ACT (Form 10): 
   - Staff CANNOT detain a client against their will unless there is an immediate threat to life (Good Samaritan Act). 
   - Only Police/Peace Officers can execute a Form 10 apprehension.
   - If a client wants to leave against advice, you can only document it, not physically stop them (unless imminent danger).

2. PROTECTION FOR PERSONS IN CARE ACT (PPCA): 
   - Any allegation of abuse (financial, emotional, physical) involving a client is a MANDATORY REPORT.
   - You must flag this immediately.

3. OHS ACT (Right to Refuse): 
   - If a staff member claims work is "unsafe" (e.g., biohazard without PPE), you must trigger the formal investigation process.
   - Do not discipline for refusal of unsafe work.

4. PRIVACY (FOIP): 
   - Do not advise sharing client info with landlords/family without signed consent.
"""

def query_dauthority(prompt, api_key, system_instruction, context_files=""):
    """Sends the package to Gemini."""
    if not api_key:
        return "🦁 ROAR! (System Error: I need an API Key in the .env file or Sidebar.)"
    
    genai.configure(api_key=api_key)
    
    # The Mega-Prompt
    full_prompt = f"""
    {REGULATORY_CONTEXT}
    
    USER'S UPLOADED DOCUMENTS (Policy/SOPs):
    {context_files}
    
    SPECIFIC INSTRUCTION:
    {system_instruction}
    
    USER INPUT:
    {prompt}
    """
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"🔥 Connection Error: {e}"

# --- 2. THE INTERFACE (SIDEBAR) ---

# Initialize Session State
if "bolo_list" not in st.session_state: st.session_state.bolo_list = []
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "internal_docs" not in st.session_state: st.session_state.internal_docs = ""
if "last_file" not in st.session_state: st.session_state.last_file = None

with st.sidebar:
    st.title("🦁 The Dauthority")
    st.caption("*Shift Command & Control*")
    
    # API Key Logic (Env first, Input second)
    env_key = os.getenv("GOOGLE_API_KEY")
    if env_key:
        api_key = env_key
        st.success("🔑 System Online")
    else:
        api_key = st.text_input("🔑 Google API Key", type="password")
    
    st.divider()
    
    # FEATURE: THE HYPE BUTTON
    if st.button("😤 I Need Hype"):
        hypes = [
            "You are a glorious golden god of de-escalation.",
            "They are lucky to have you.",
            "Deep breath. You run this floor.",
            "Chaos is a ladder, and you're climbing it.",
            "Not today, Satan. Not today.",
            "You are the eye of the storm."
        ]
        st.toast(random.choice(hypes), icon="🔥")

    st.divider()

    # FEATURE: BOLO BOARD (Persistent Watchlist)
    st.subheader("🚨 BOLO (Watchlist)")
    new_bolo = st.text_input("Add Risk:", placeholder="Client Name / Threat")
    if st.button("Add to Board"):
        if new_bolo: st.session_state.bolo_list.append(new_bolo)
    
    if st.session_state.bolo_list:
        st.error("⚠️ ACTIVE:")
        for item in st.session_state.bolo_list:
            st.markdown(f"**• {item}**")
        if st.button("Clear Board"):
            st.session_state.bolo_list = []

    st.divider()
    
    # FEATURE: DATA PERSISTENCE (Download Log)
    log_content = f"""DAUTHORITY SESSION LOG - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
    -----------------------------------
    ACTIVE BOLO LIST:
    {', '.join(st.session_state.bolo_list)}
    
    LAST CHAT RESPONSE:
    {(st.session_state.chat_history[-1]['content']) if st.session_state.chat_history else 'None'}
    """
    st.download_button("💾 Save Session Log", data=log_content, file_name="Shift_Log.txt")

    # HELP GUIDE
    with st.expander("❓ Quick Guide"):
        st.markdown("""
        - **Scribe:** Messy notes -> Legal report.
        - **Diplomat:** Angry vent -> Nice email.
        - **Gavel:** Policy questions (Upload PDF first).
        - **Tip:** Use the 🎤 on your phone keyboard!
        """)

# --- 3. THE INTERFACE (MAIN TABS) ---
tab1, tab2, tab3, tab4 = st.tabs(["📝 The Scribe", "👔 The Diplomat", "⚖️ The Gavel", "⚓ The Captain"])

# --- TAB 1: THE SCRIBE (Reporting) ---
with tab1:
    st.header("Shift Report Synthesizer")
    
    # One-Click Templates
    col_t1, col_t2, col_t3 = st.columns(3)
    note_placeholder = "Type or dictate your messy notes here..."
    if col_t1.button("💥 Conflict Template"):
        note_placeholder = "Time: \nLocation: \nStaff Involved: \nClient(s): \nNarrative: \nPolice Called?: No"
    if col_t2.button("🚑 Medical Template"):
        note_placeholder = "Time: \nLocation: \nNature of Distress: \nNaloxone Used?: \nEMS File #: "
    
    col1, col2 = st.columns(2)
    with col1:
        raw_notes = st.text_area("Your Notes:", value=note_placeholder if "Template" in note_placeholder else "", height=300)
    
    with col2:
        st.markdown("### Official Output")
        if st.button("🦁 Synthesize Report"):
            with st.spinner(get_funny_spinner()):
                scrubbed = scrub_pii(raw_notes)
                instruction = """
                Convert these notes into a Formal Shift Report.
                Categorize into: 1. Critical Incidents (Bold Liability risks), 2. Staffing, 3. Operations.
                Use professional, objective language. Remove slang.
                """
                result = query_dauthority(scrubbed, api_key, instruction)
                st.markdown('<div class="report-box">', unsafe_allow_html=True)
                st.markdown(result)
                st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 2: THE DIPLOMAT (Communication) ---
with tab2:
    st.header("Corporate Translator")
    draft = st.text_area("Vent your frustration here (Don't hold back):", height=150)
    
    sass_mode = st.checkbox("🌶️ Add 'Executive Sass' (Passive Aggressive)")
    
    if st.button("👔 Professionalize Me"):
        with st.spinner(get_funny_spinner()):
            tone = "Professional, HR-safe, firm, objective."
            if sass_mode:
                tone += " Add a layer of polite, undeniable authority. Use phrases like 'Per my previous email'."
            
            clean_text = scrub_pii(draft)
            instruction = f"Rewrite this text. TONE: {tone}"
            result = query_dauthority(clean_text, api_key, instruction)
            st.info(result)

# --- TAB 3: THE GAVEL (Policy/RAG) ---
with tab3:
    st.header("Policy Oracle")
    
    # File Uploader
    uploaded_file = st.file_uploader("Upload Policy PDF or Text", type=['pdf', 'txt'])
    if uploaded_file:
        if uploaded_file.name != st.session_state.last_file:
            with st.spinner("Memorizing the rules..."):
                if uploaded_file.type == "application/pdf":
                    st.session_state.internal_docs = extract_text_from_pdf(uploaded_file)
                else:
                    st.session_state.internal_docs = str(uploaded_file.read(), "utf-8")
                st.session_state.last_file = uploaded_file.name
                st.toast("Policy Loaded!", icon="✅")

    # Chat
    user_query = st.chat_input("Ask: 'Can I ban him for X?' or 'What is the protocol for Y?'")
    
    if user_query:
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        instruction = """
        You are a Risk Management Engine.
        1. FIRST check the uploaded Policy Context.
        2. SECOND check Alberta Law (Hardcoded Context).
        3. ANSWER with a step-by-step checklist.
        """
        with st.spinner(get_funny_spinner()):
            response = query_dauthority(user_query, api_key, instruction, st.session_state.internal_docs)
            st.session_state.chat_history.append({"role": "assistant", "content": response})

    # Render Chat with Clear Button
    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()
        
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# --- TAB 4: THE CAPTAIN (Logistics) ---
with tab4:
    st.header("Team Logistics")
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("☕ Break Captain")
        staff_names = st.text_input("Staff (Comma Separated):", "Sarah, Mike, Jess, Dave")
        start_time = st.time_input("Shift Start", datetime.time(7, 0))
        if st.button("Generate Schedule"):
            s_list = [s.strip() for s in staff_names.split(",")]
            base = datetime.datetime.combine(datetime.date.today(), start_time)
            # Logic: First break 2 hours in, staggered by 30 mins
            break_start = base + datetime.timedelta(hours=2)
            st.markdown("#### 📋 Proposed Schedule")
            for i, staff in enumerate(s_list):
                b_time = break_start + datetime.timedelta(minutes=30 * i)
                st.write(f"**{staff}**: {b_time.strftime('%H:%M')}")

    with col_b:
        st.subheader("🚑 The Hot Wash (Debrief)")
        st.caption("Ask these 4 questions immediately after a crisis.")
        if st.button("Start Debrief"):
             st.markdown("1. **The Facts:** What actually happened? (Timeline)")
             st.markdown("2. **The Actions:** What did we do? (Narcan? CPR? De-escalation?)")
             st.markdown("3. **The Gaps:** What was missing? (Radio dead? Bag empty? Staff froze?)")
             st.markdown("4. **The People:** Is everyone okay to continue working?")