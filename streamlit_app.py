import streamlit as st
from groq import Groq
import google.generativeai as genai
from gtts import gTTS
import requests
from bs4 import BeautifulSoup
from googlesearch import search
import PyPDF2
from PIL import Image
import io
import base64
import datetime
import uuid

# ==============================================================================
# 1. CONFIGURATION
# ==============================================================================
st.set_page_config(page_title="VOID by G1", page_icon="🧿", layout="wide")

# ⚠️ SECRETS (We will set these in the Cloud Settings later)
# If running locally, you can paste keys here, but for Cloud, use st.secrets
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("API Keys missing! Please set them in Streamlit Secrets.")
    st.stop()

client_groq = Groq(api_key=GROQ_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)
model_vision = genai.GenerativeModel('gemini-1.5-flash')

CREATOR_NAME = "Jeevan Kumar"
CREATOR_TITLE = "Boss"
PASSCODE = "G15002"

# ==============================================================================
# 2. CORE ENGINES
# ==============================================================================

def google_search_engine(query):
    """Real Google Search + Website Scraping"""
    try:
        # 1. Search Google
        # We try to get 3 good results
        results = list(search(query, num_results=3, advanced=True))
        
        intel = []
        for r in results:
            try:
                # 2. Visit Website (Scraping)
                page = requests.get(r.url, timeout=2, headers={'User-Agent': 'Mozilla/5.0'})
                soup = BeautifulSoup(page.text, 'html.parser')
                # Get first 500 characters of text
                text = soup.get_text()[:500].replace("\n", " ")
                intel.append(f"SOURCE: {r.title}\nLINK: {r.url}\nINFO: {text}")
            except: continue
            
        return "\n\n".join(intel)
    except Exception as e:
        return None

def generate_image(prompt):
    """Image Generation via Pollinations (No Key Needed)"""
    clean_prompt = prompt.replace(" ", "%20")
    return f"https://image.pollinations.ai/prompt/{clean_prompt}"

def analyze_file(uploaded_file):
    """Reads PDFs and Images"""
    if uploaded_file.type == "application/pdf":
        reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages[:5]: # Limit to first 5 pages for speed
            text += page.extract_text()
        return f"PDF CONTENT:\n{text}"
    
    elif "image" in uploaded_file.type:
        img = Image.open(uploaded_file)
        # We return the image object for the logic to handle later
        return img
    return None

def speak(text):
    """Mobile-Compatible Audio Player"""
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        b64 = base64.b64encode(mp3_fp.read()).decode()
        md = f"""
            <audio autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)
    except: pass

# ==============================================================================
# 3. THE BRAIN
# ==============================================================================
def brain_process(user_input, file_data=None):
    # A. IMAGE GENERATION CHECK
    if any(x in user_input.lower() for x in ["generate image", "create image", "draw"]):
        prompt = user_input.lower().replace("generate image", "").replace("create image", "").replace("draw", "").strip()
        img_url = generate_image(prompt)
        return "IMG", img_url

    # B. VISION / FILE CHECK
    file_context = ""
    if file_data:
        if isinstance(file_data, str): # It's a PDF text
            file_context = file_data
        else: # It's an Image object
            response = model_vision.generate_content([user_input, file_data])
            return "TXT", response.text

    # C. GOOGLE SEARCH CHECK
    web_data = ""
    ignore = ["hi", "hello", "void", "thanks"]
    if not any(x == user_input.lower().strip() for x in ignore) and not file_context:
        web_data = google_search_engine(user_input)

    # D. FINAL PROMPT
    current_time = datetime.datetime.now().strftime("%A, %I:%M %p")
    system = f"""
    You are VOID by G1. Owner: {CREATOR_NAME}. Time: {current_time}.
    Directives: Be concise, smart, and loyal.
    """
    
    final_prompt = user_input
    if web_data: final_prompt += f"\n\n[GOOGLE SEARCH DATA]:\n{web_data}"
    if file_context: final_prompt += f"\n\n[FILE DATA]:\n{file_context}"

    try:
        completion = client_groq.chat.completions.create(
            messages=[{"role": "system", "content": system}, {"role": "user", "content": final_prompt}],
            model="llama-3.3-70b-versatile", temperature=0.6, max_tokens=600
        )
        return "TXT", completion.choices[0].message.content
    except Exception as e: return "TXT", f"Error: {e}"

# ==============================================================================
# 4. UI INTERFACE (MOBILE OPTIMIZED)
# ==============================================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;900&family=Rajdhani:wght@400;700&display=swap');
    .stApp { background-color: #000; color: #00E5FF; font-family: 'Rajdhani'; }
    .hero { text-align: center; font-family:'Orbitron'; font-size: 2.5rem; text-shadow: 0 0 15px #00E5FF; }
    .stTextInput input { background: #111; color: #fff; border: 1px solid #333; border-radius: 15px; }
    .stChatMessage { background: #0a0a0a; border: 1px solid #222; border-radius: 10px; }
    .stChatMessage[data-testid="user"] { border-left: 3px solid #FFF; }
    .stChatMessage[data-testid="assistant"] { border-left: 3px solid #00E5FF; }
    </style>
""", unsafe_allow_html=True)

if "auth" not in st.session_state: st.session_state.auth = False
if "messages" not in st.session_state: st.session_state.messages = []

# --- LOCK SCREEN ---
if not st.session_state.auth:
    st.markdown("<br><br><div class='hero'>G1 SECURE</div>", unsafe_allow_html=True)
    pw = st.text_input("ENTER BIO-KEY", type="password")
    if st.button("AUTHENTICATE"):
        if pw == PASSCODE:
            st.session_state.auth = True
            st.rerun()
        else: st.error("ACCESS DENIED")

# --- MAIN APP ---
else:
    st.markdown("<div class='hero'>Void by G1</div>", unsafe_allow_html=True)
    
    # File Uploader (Hidden in sidebar to save space)
    with st.sidebar:
        st.header("📂 UPLOAD DATA")
        uploaded_file = st.file_uploader("Image / PDF", type=['png', 'jpg', 'jpeg', 'pdf'])

    # Chat History
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            if "image" in m: st.image(m["image"])
            else: st.write(m["content"])

    # Input
    txt = st.chat_input("Command Void...")
    
    if txt:
        st.session_state.messages.append({"role": "user", "content": txt})
        
        # Process File if exists
        file_data = None
        if uploaded_file:
            file_data = analyze_file(uploaded_file)
            
        # Brain Logic
        type_resp, content = brain_process(txt, file_data)
        
        if type_resp == "IMG":
            st.session_state.messages.append({"role": "assistant", "image": content, "content": "Generating visual..."})
        else:
            st.session_state.messages.append({"role": "assistant", "content": content})
            speak(content)
            
        st.rerun()
