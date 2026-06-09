import streamlit as st
import asyncio
import edge_tts
from datetime import datetime
import re
import PyPDF2
import io

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
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. MICROSOFT NEURAL ENGINE (Async Framework)
# ==========================================
VOICE_MODELS = {
    "Hindi (Female - Swara HD)": "hi-IN-SwaraNeural",
    "Hindi (Male - Madhur HD)": "hi-IN-MadhurNeural",
    "English (Female - Aria HD)": "en-US-AriaNeural",
    "English (Male - Guy HD)": "en-US-GuyNeural",
    "Punjabi (Female - Rakhi HD)": "pa-IN-RakhiNeural",
    "Punjabi (Male - Ojas HD)": "pa-IN-OjasNeural"
}

def sanitize_text(text: str) -> str:
    """Removes extra spaces, newlines, and unwanted characters for smooth TTS."""
    text = re.sub(r'\n+', ' ', text)  
    text = re.sub(r'\s+', ' ', text)  
    return text.strip()

def extract_text_from_pdf(pdf_file) -> str:
    """Extracts raw text securely from uploaded PDF files."""
    extracted_text = ""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + " "
    except Exception as e:
        st.error(f"Error reading PDF format: {e}")
    return extracted_text

async def synthesize_neural_audio(text: str, voice_name: str, speed: int) -> bytes:
    """Generates HD neural audio with custom speed."""
    speed_str = f"{speed:+d}%" 
    communicate = edge_tts.Communicate(text, voice_name, rate=speed_str)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

def generate_audio_sync(text: str, voice_name: str, speed: int) -> bytes:
    """Synchronous wrapper for async Edge TTS."""
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
    st.markdown("<div class='sub-header'>Powered by Microsoft Edge AI | PDF Integration | HD Voice Quality</div>", unsafe_allow_html=True)

    left_col, right_col = st.columns([2, 1])

    with left_col:
        st.markdown("### 📄 Input Document")
        
        # Extended File Uploader for PDFs
        uploaded_file = st.file_uploader("Upload a .pdf or .txt file (Optional)", type=["txt", "pdf"])
        
        default_text = ""
        if uploaded_file is not None:
            if uploaded_file.name.endswith(".pdf"):
                default_text = extract_text_from_pdf(uploaded_file)
                st.success("✅ PDF processed successfully! Text extracted below for review.")
            else:
                default_text = uploaded_file.getvalue().decode("utf-8")
                st.success("✅ Text file loaded successfully!")

        text_input = st.text_area("Or Paste/Edit Text Here:", value=default_text, height=300, placeholder="Upload a document above, or paste your text directly here...")

    with right_col:
        st.markdown("### ⚙️ Engine Settings")
        
        selected_voice_label = st.selectbox("🌐 Neural Voice Model:", list(VOICE_MODELS.keys()))
        selected_voice_id = VOICE_MODELS[selected_voice_label]
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        speech_speed = st.slider("⏱️ Speech Speed (%)", min_value=-50, max_value=50, value=0, step=5, help="Adjust the talking speed. 0 is default.")
        
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🚀 Execute Neural Synthesis", use_container_width=True, type="primary"):
            clean_text = sanitize_text(text_input)
            
            if not clean_text:
                st.error("⚠️ Input required: Please provide text data or upload a file.")
            else:
                st.session_state.audio_data = None
                st.session_state.processing_complete = False
                
                progress_bar = st.progress(0, text="Initializing Neural Engine...")
                
                try:
                    progress_bar.progress(40, text="Connecting to Microsoft AI servers...")
                    
                    audio_bytes = generate_audio_sync(clean_text, selected_voice_id, speech_speed)
                    
                    st.session_state.audio_data = audio_bytes
                    st.session_state.processing_complete = True
                    
                    progress_bar.progress(100, text="Finalizing Output...")
                    st.success("✅ Synthesis Complete! High-Definition audio generated successfully.")
                    progress_bar.empty()
                    
                except Exception as e:
                    progress_bar.empty()
                    st.error(f"❌ System Fault: {str(e)}")

    st.divider()

    if st.session_state.processing_complete and st.session_state.audio_data:
        st.markdown("### 🎧 Playback & Download")
        st.audio(st.session_state.audio_data, format='audio/mp3')
        
        st.download_button(
            label="📥 Download HD Audio Output (MP3)",
            data=st.session_state.audio_data,
            file_name=f"Neural_Audio_{datetime.now().strftime('%Y%m%d_%H%M')}.mp3",
            mime="audio/mp3",
            use_container_width=True
        )

if __name__ == "__main__":
    main()
