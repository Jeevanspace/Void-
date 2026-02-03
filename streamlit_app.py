import streamlit as st
from groq import Groq
import google.generativeai as genai
from gtts import gTTS
import speech_recognition as sr
from streamlit_mic_recorder import mic_recorder
from duckduckgo_search import DDGS
import PyPDF2
from PIL import Image
from pydub import AudioSegment
import io
import base64
import datetime
import uuid
import random

# ==============================================================================
# 1. CONFIGURATION
# ==============================================================================
st.set_page_config(page_title="VOID OMNI", page_icon="🧿", layout="wide", initial_sidebar_state="collapsed")

# Load Secrets
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("⚠️ API KEYS MISSING! Check Streamlit Secrets.")
    st.stop()

client_groq = Groq(api_key=GROQ_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)
model_vision = genai.GenerativeModel('gemini-1.5-flash')

CREATOR_NAME = "Jeevan Kumar"
CREATOR_TITLE = "Boss"

# ==============================================================================
# 2. UI THEME (SPACEX / IRON MAN STYLE)
# ==============================================================================
def inject_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;900&family=Rajdhani:wght@400;600&display=swap');
        
        /* DEEP SPACE BACKGROUND */
        .stApp {
            background-color: #000000;
            background-image: 
                radial-gradient(circle at 50% 50%, #1a1a2e 0%, #000000 100%),
                url("https://www.transparenttextures.com/patterns/stardust.png");
            color: #E0E0E0;
            font-family: 'Rajdhani', sans-serif;
        }

        /* NEON HEADER */
        .hero-text {
            font-family: 'Orbitron', sans-serif;
            text-align: center;
            font-size: 3rem;
            background: linear-gradient(90deg, #00E5FF, #0072FF);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 20px rgba(0, 229, 255, 0.5);
            margin-bottom: 0px;
        }
        
        /* CHAT BUBBLES (GLASSMORPHISM) */
        .stChatMessage {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(0, 229, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
        }
        .stChatMessage[data-testid="user"] {
            border-right: 3px solid #FFFFFF;
            background: rgba(255, 255, 255, 0.05);
        }
        .stChatMessage[data-testid="assistant"] {
            border-left: 3px solid #00E5FF;
            background: rgba(0, 229, 255, 0.02);
        }

        /* INPUT FIELD */
        .stTextInput input {
            background-color: #050505 !important;
            color: #00E5FF !important;
            border: 1px solid #00E5FF !important;
            border-radius: 25px;
            font-family: 'Orbitron';
            text-align: center;
        }

        /* AUDIO PLAYER */
        audio { width: 100%; height: 30px; filter: invert(1) hue-rotate(180deg); }
        </style>
    """, unsafe_allow_html=True)

inject_css()

# ==============================================================================
# 3. CORE ENGINES (VOICE, SEARCH, VISION)
# ==============================================================================

def audio_to_text(audio_bytes):
    """Converts Browser Audio (WebM) to Text"""
    try:
        # Convert WebM to WAV in memory
        audio_io = io.BytesIO(audio_bytes)
        sound = AudioSegment.from_file(audio_io)
        wav_io = io.BytesIO()
        sound.export(wav_io, format="wav")
        wav_io.seek(0)
        
        # Recognize
        r = sr.Recognizer()
        with sr.AudioFile(wav_io) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data)
            return text
    except: return None

def speak(text):
    """Generates Voice Response"""
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        b64 = base64.b64encode(mp3_fp.read()).decode()
        
        # Visible Player for Mobile Compatibility
        md = f"""
            <audio controls autoplay>
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)
    except: pass

def search_web(query):
    """Real-Time Internet Search"""
    try:
        results = DDGS().text(query, max_results=3)
        if results:
            return "\n".join([f"• {r['body']}" for r in results])
    except: return None

def generate_image(prompt):
    """AI Image Generator"""
    clean = prompt.replace(" ", "%20")
    # Using Pollinations AI
    return f"https://image.pollinations.ai/prompt/{clean}?nologo=true"

# ==============================================================================
# 4. THE BRAIN
# ==============================================================================
def brain_engine(user_input, file_context=None):
    # A. IMAGE GENERATION CHECK
    if any(x in user_input.lower() for x in ["generate image", "create image", "draw a", "make a picture"]):
        prompt = user_input.lower().replace("generate image", "").replace("draw a", "").strip()
        return "IMG", generate_image(prompt)

    # B. SEARCH CHECK (Live Data)
    web_data = ""
    ignore = ["hi", "hello", "void", "thanks"]
    if not any(x == user_input.lower().strip() for x in ignore) and not file_context:
        web_data = search_web(user_input)

    # C. PROMPT CONSTRUCTION
    current_time = datetime.datetime.now().strftime("%A, %I:%M %p")
    system = f"""
    You are VOID, the Advanced AI of {CREATOR_NAME}.
    Time: {current_time}.
    Directives:
    1. Be highly intelligent, concise, and loyal (Jarvis Personality).
    2. If [WEB DATA] is present, use it for 2025/2026 facts.
    3. If [FILE DATA] is present, analyze it.
    """
    
    final_prompt = user_input
    if web_data: final_prompt += f"\n\n[LIVE SEARCH DATA]:\n{web_data}"
    if file_context: final_prompt += f"\n\n[FILE CONTENT]:\n{file_context}"

    try:
        res = client_groq.chat.completions.create(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": final_prompt}],
            model="llama-3.3-70b-versatile", temperature=0.6, max_tokens=600
        )
        return "TXT", res.choices[0].message.content
    except Exception as e: return "TXT", f"Error: {e}"

# ==============================================================================
# 5. UI FLOW
# ==============================================================================

# Header
st.markdown("<div class='hero-text'>VOID OMNI</div>", unsafe_allow_html=True)
st.markdown(f"<div style='text-align:center; color:#555;'>SYSTEM ONLINE // {CREATOR_NAME}</div>", unsafe_allow_html=True)

# File Uploader (Expandable)
with st.expander("📂 UPLOAD FILES / VISION"):
    uploaded_file = st.file_uploader("Analyze Image or PDF", type=['png', 'jpg', 'jpeg', 'pdf'])

# Chat History
if "messages" not in st.session_state: st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        if "image" in m: st.image(m["image"])
        else: st.write(m["content"])

# INPUT AREA
c1, c2 = st.columns([1, 6])

with c1:
    # VOICE INPUT BUTTON
    audio_data = mic_recorder(start_prompt="🎤", stop_prompt="🛑", key='mic')

with c2:
    # TEXT INPUT
    text_input = st.chat_input("Command Void...")

# LOGIC HANDLER
final_input = None
file_data = None

# 1. Handle Voice
if audio_data:
    transcription = audio_to_text(audio_data['bytes'])
    if transcription:
        final_input = transcription

# 2. Handle Text
if text_input:
    final_input = text_input

# 3. Handle File
if uploaded_file:
    if "image" in uploaded_file.type:
        img = Image.open(uploaded_file)
        # Use Gemini for Vision
        if final_input: # If user asked a question about image
            try:
                vision_res = model_vision.generate_content([final_input, img])
                st.session_state.messages.append({"role": "user", "content": f"Image Analysis: {final_input}"})
                st.session_state.messages.append({"role": "assistant", "content": vision_res.text})
                speak(vision_res.text)
                st.rerun()
            except: st.error("Vision Error")
    elif "pdf" in uploaded_file.type:
        reader = PyPDF2.PdfReader(uploaded_file)
        file_data = ""
        for page in reader.pages[:3]: file_data += page.extract_text()

# 4. EXECUTE
if final_input and not uploaded_file: # Normal Chat / Image Gen
    st.session_state.messages.append({"role": "user", "content": final_input})
    
    # Brain Processing
    type_resp, content = brain_engine(final_input, file_data)
    
    if type_resp == "IMG":
        st.session_state.messages.append({"role": "assistant", "content": "Visualizing...", "image": content})
    else:
        st.session_state.messages.append({"role": "assistant", "content": content})
        speak(content)
    
    st.rerun()
