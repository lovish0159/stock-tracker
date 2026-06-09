import streamlit as st
import asyncio
import edge_tts
from datetime import datetime
import re
import PyPDF2

# ==========================================
# 1. ENTERPRISE CONFIGURATION & SYSTEM STATE
# ==========================================
st.set_page_config(page_title="Pro Neural Audio Synthesizer", page_icon="🎙️", layout="wide")

# Session State Initializer (Prevents UI Freezing)
if "extracted_text" not in st.session_state:
    st.session_state.extracted_text = ""
if "audio_data" not in st.session_state:
    st.session_state.audio_data = None
if "processing_complete" not in st.session_state:
    st.session_state.processing_complete = False
if "last_uploaded_file" not in st.session_state:
    st.session_state.last_uploaded_file = None

def apply_pro_css():
    st.markdown("""
        <style>
            #MainMenu, footer, header {visibility: hidden;}
            .main-header { font-size: 2.5rem; color: #0f172a; text-align: center; font-weight: 800; margin-bottom: 0px; letter-spacing: -1px;}
            .sub-header { text-align: center; color: #64748b; margin-bottom: 2rem; font-size: 16px; font-weight: 500;}
            .stTextArea textarea { font-size: 16px; border-radius: 12px; border: 1px solid #cbd5e1; padding: 15px;}
            div.stButton > button { border-radius: 8px; font-weight: 600; padding: 0.5rem 1rem; }
            [data-testid="stFileUploadDropzone"] { border: 2px solid #3b82f6; border-radius: 10px; background-color: #f8fafc; }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. DATA EXTRACTION ENGINE
# ==========================================
def extract_text_from_pdf(pdf_file) -> str:
    """Fast extraction of PDF text into memory segments."""
    extracted_text = []
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                extracted_text.append(text)
        return " ".join(extracted_text)
    except Exception as e:
        st.error(f"❌ PDF Extraction Fault: {e}")
        return ""

def sanitize_text(text: str) -> str:
    """Ultra-fast regex to clean text formatting."""
    text = re.sub(r'\n+', ' ', text)  
    text = re.sub(r'\s+', ' ', text)  
    return text.strip()

# ==========================================
# 3. MICROSOFT NEURAL ENGINE (Async Control)
# ==========================================
VOICE_MODELS = {
    "Hindi (Female - Swara HD)": "hi-IN-SwaraNeural",
    "Hindi (Male - Madhur HD)": "hi-IN-MadhurNeural",
    "English (Female - Aria HD)": "en-US-AriaNeural",
    "English (Male - Guy HD)": "en-US-GuyNeural",
    "Punjabi (Female - Rakhi HD)": "pa-IN-RakhiNeural",
    "Punjabi (Male - Ojas HD)": "pa-IN-OjasNeural"
}

async def synthesize_neural_audio(text: str, voice_name: str, speed: int) -> bytes:
    speed_str = f"{speed:+d}%" 
    communicate = edge_tts.Communicate(text, voice_name, rate=speed_str)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

def generate_audio_sync(text: str, voice_name: str, speed: int) -> bytes:
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(synthesize_neural_audio(text, voice_name, speed))

# ==========================================
# 4. USER INTERFACE RENDERING
# ==========================================
def main():
    apply_pro_css()

    st.markdown("<div class='main-header'>🎙️ Pro Neural Audio Synthesizer</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>State-Managed Architecture for Instant Processing</div>", unsafe_allow_html=True)

    left_col, right_col = st.columns([2, 1])

    with left_col:
        st.markdown("### 📂 Input Source")
        
        # File Uploader with State Trigger
        uploaded_file = st.file_uploader("Click 'Browse files' to select a PDF or TXT", type=["txt", "pdf"])
        
        if uploaded_file is not None:
            current_file_key = f"{uploaded_file.name}_{uploaded_file.size}"
            
            # Agar naya file upload hua hai toh process karein, varna skip karein
            if st.session_state.last_uploaded_file != current_file_key:
                with st.spinner("⚡ Extracting text instantly..."):
                    if uploaded_file.name.endswith(".pdf"):
                        text_extracted = extract_text_from_pdf(uploaded_file)
                    else:
                        text_extracted = uploaded_file.getvalue().decode("utf-8")
                    
                    # Store in session state and trigger clean rerun
                    st.session_state.extracted_text = text_extracted
                    st.session_state.last_uploaded_file = current_file_key
                    st.session_state.audio_data = None
                    st.session_state.processing_complete = False
                    st.rerun()

        # Text area reads directly from State Memory
        text_input = st.text_area(
            "Review or Edit Text Here:", 
            value=st.session_state.extracted_text, 
            height=300, 
            placeholder="Your file text will load here automatically after selection..."
        )
        
        # Manual edit handling to sync state
        if text_input != st.session_state.extracted_text:
            st.session_state.extracted_text = text_input

    with right_col:
        st.markdown("### ⚙️ Engine Settings")
        
        selected_voice_label = st.selectbox("🌐 Neural Voice Model:", list(VOICE_MODELS.keys()))
        selected_voice_id = VOICE_MODELS[selected_voice_label]
        
        st.markdown("<br>", unsafe_allow_html=True)
        speech_speed = st.slider("⏱️ Speech Speed (%)", min_value=-50, max_value=50, value=0, step=5)
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🚀 Synthesize Audio Now", use_container_width=True, type="primary"):
            clean_text = sanitize_text(st.session_state.extracted_text)
            
            if not clean_text:
                st.error("⚠️ Please provide text or upload a file first.")
            else:
                st.session_state.audio_data = None
                st.session_state.processing_complete = False
                
                progress_bar = st.progress(0, text="⚡ Activating Neural Engine...")
                
                try:
                    progress_bar.progress(40, text="Compiling voice matrix...")
                    audio_bytes = generate_audio_sync(clean_text, selected_voice_id, speech_speed)
                    
                    st.session_state.audio_data = audio_bytes
                    st.session_state.processing_complete = True
                    
                    progress_bar.progress(100, text="✅ Done!")
                    st.success("🎉 Synthesis Complete!")
                    progress_bar.empty()
                    
                except Exception as e:
                    progress_bar.empty()
                    st.error(f"❌ Processing Interrupted: {str(e)}")

    st.divider()

    # Display components seamlessly from state memory
    if st.session_state.processing_complete and st.session_state.audio_data:
        st.markdown("### 🎧 Playback & Download")
        st.audio(st.session_state.audio_data, format='audio/mp3')
        
        st.download_button(
            label="📥 Download Audio File (MP3)",
            data=st.session_state.audio_data,
            file_name=f"Neural_Audio_{datetime.now().strftime('%d%m%Y_%H%M')}.mp3",
            mime="audio/mp3",
            use_container_width=True
        )

if __name__ == "__main__":
    main()
