import streamlit as st
import asyncio
import edge_tts
from datetime import datetime
import re
import PyPDF2

# ==========================================
# 1. ENTERPRISE CONFIGURATION
# ==========================================
st.set_page_config(page_title="Pro Neural Audio Synthesizer", page_icon="🎙️", layout="wide")

def apply_pro_css():
    st.markdown("""
        <style>
            #MainMenu, footer, header {visibility: hidden;}
            .main-header { font-size: 2.5rem; color: #0f172a; text-align: center; font-weight: 800; margin-bottom: 0px; letter-spacing: -1px;}
            .sub-header { text-align: center; color: #64748b; margin-bottom: 2rem; font-size: 16px; font-weight: 500;}
            .stTextArea textarea { font-size: 16px; border-radius: 12px; border: 1px solid #cbd5e1; padding: 15px;}
            div.stButton > button { border-radius: 8px; font-weight: 600; padding: 0.5rem 1rem; }
            /* Styling to make the upload area look like a solid button instead of drag-drop */
            [data-testid="stFileUploadDropzone"] { border: 2px solid #3b82f6; border-radius: 10px; padding: 20px; background-color: #f8fafc; }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. MICROSOFT NEURAL ENGINE & TEXT PROCESSING
# ==========================================
VOICE_MODELS = {
    "Hindi (Female - Swara HD)": "hi-IN-SwaraNeural",
    "Hindi (Male - Madhur HD)": "hi-IN-MadhurNeural",
    "English (Female - Aria HD)": "en-US-AriaNeural",
    "English (Male - Guy HD)": "en-US-GuyNeural",
    "Punjabi (Female - Rakhi HD)": "pa-IN-RakhiNeural",
    "Punjabi (Male - Ojas HD)": "pa-IN-OjasNeural"
}

@st.cache_data(show_spinner=False)
def sanitize_text(text: str) -> str:
    """Ultra-fast regex to clean text formatting."""
    text = re.sub(r'\n+', ' ', text)  
    text = re.sub(r'\s+', ' ', text)  
    return text.strip()

def extract_text_from_pdf(pdf_file) -> str:
    """Fast extraction of PDF text."""
    extracted_text = []
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                extracted_text.append(text)
        return " ".join(extracted_text)
    except Exception as e:
        st.error(f"❌ Error reading PDF format: {e}")
        return ""

async def synthesize_neural_audio(text: str, voice_name: str, speed: int) -> bytes:
    """Generates HD neural audio via async stream."""
    speed_str = f"{speed:+d}%" 
    communicate = edge_tts.Communicate(text, voice_name, rate=speed_str)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

def generate_audio_sync(text: str, voice_name: str, speed: int) -> bytes:
    """Synchronous wrapper for async Edge TTS execution."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(synthesize_neural_audio(text, voice_name, speed))

# ==========================================
# 3. STATE MANAGEMENT
# ==========================================
def init_session_state():
    if 'audio_data' not in st.session_state:
        st.session_state.audio_data = None
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False

# ==========================================
# 4. USER INTERFACE RENDERING
# ==========================================
def main():
    apply_pro_css()
    init_session_state()

    st.markdown("<div class='main-header'>🎙️ Pro Neural Audio Synthesizer</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Upload File ➔ Click Synthesize ➔ Download HD Audio</div>", unsafe_allow_html=True)

    left_col, right_col = st.columns([2, 1])

    with left_col:
        st.markdown("### 📂 Input Source")
        
        # Explicit Upload Mechanism
        uploaded_file = st.file_uploader("Click 'Browse files' to select a PDF or TXT", type=["txt", "pdf"], accept_multiple_files=False)
        
        default_text = ""
        if uploaded_file is not None:
            with st.spinner("⚡ Extracting text..."):
                if uploaded_file.name.endswith(".pdf"):
                    default_text = extract_text_from_pdf(uploaded_file)
                    st.success(f"✅ PDF '{uploaded_file.name}' loaded instantly!")
                else:
                    default_text = uploaded_file.getvalue().decode("utf-8")
                    st.success(f"✅ Text file '{uploaded_file.name}' loaded instantly!")

        text_input = st.text_area("Review or Edit Text Here:", value=default_text, height=300, placeholder="Your extracted file text will appear here. You can also type or paste directly...")

    with right_col:
        st.markdown("### ⚙️ Engine Settings")
        
        selected_voice_label = st.selectbox("🌐 Neural Voice Model:", list(VOICE_MODELS.keys()))
        selected_voice_id = VOICE_MODELS[selected_voice_label]
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        speech_speed = st.slider("⏱️ Speech Speed (%)", min_value=-50, max_value=50, value=0, step=5)
        
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🚀 Synthesize Audio Now", use_container_width=True, type="primary"):
            clean_text = sanitize_text(text_input)
            
            if not clean_text:
                st.error("⚠️ Please provide text or upload a file first.")
            else:
                st.session_state.audio_data = None
                st.session_state.processing_complete = False
                
                progress_bar = st.progress(0, text="⚡ Establishing secure connection to Neural Engine...")
                
                try:
                    progress_bar.progress(30, text="Generating high-speed audio matrix...")
                    
                    # Core Processing
                    audio_bytes = generate_audio_sync(clean_text, selected_voice_id, speech_speed)
                    
                    st.session_state.audio_data = audio_bytes
                    st.session_state.processing_complete = True
                    
                    progress_bar.progress(100, text="✅ Audio compiled successfully!")
                    st.success("🎉 Synthesis Complete! Ready for playback.")
                    progress_bar.empty()
                    
                except Exception as e:
                    progress_bar.empty()
                    st.error(f"❌ Processing Interrupted: {str(e)}")

    st.divider()

    if st.session_state.processing_complete and st.session_state.audio_data:
        st.markdown("### 🎧 Playback & Download")
        st.audio(st.session_state.audio_data, format='audio/mp3')
        
        st.download_button(
            label="📥 Download Audio File (MP3)",
            data=st.session_state.audio_data,
            file_name=f"Audio_{datetime.now().strftime('%d%m%Y_%H%M')}.mp3",
            mime="audio/mp3",
            use_container_width=True
        )

if __name__ == "__main__":
    main()
