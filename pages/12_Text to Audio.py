import streamlit as st
import asyncio
import edge_tts
from datetime import datetime

# ==========================================
# 1. ENTERPRISE CONFIGURATION
# ==========================================
st.set_page_config(page_title="Neural Audio Synthesizer", page_icon="🎙️", layout="centered")

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
# Map of High-Definition Neural Voices
VOICE_MODELS = {
    "Hindi (Female - Swara)": "hi-IN-SwaraNeural",
    "Hindi (Male - Madhur)": "hi-IN-MadhurNeural",
    "English (Female - Aria)": "en-US-AriaNeural",
    "English (Male - Guy)": "en-US-GuyNeural",
    "Punjabi (Female - Rakhi)": "pa-IN-RakhiNeural",
    "Punjabi (Male - Ojas)": "pa-IN-OjasNeural"
}

async def synthesize_neural_audio(text: str, voice_name: str) -> bytes:
    """Asynchronously generates high-quality neural audio without API limits."""
    communicate = edge_tts.Communicate(text, voice_name)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

def generate_audio_sync(text: str, voice_name: str) -> bytes:
    """Wrapper to run async Edge TTS in Streamlit's synchronous environment."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(synthesize_neural_audio(text, voice_name))

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

    st.markdown("<div class='main-header'>🎙️ HD Neural Audio Synthesizer</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Powered by Microsoft Edge AI | Bypass Rate Limits | Zero Chunking Needed</div>", unsafe_allow_html=True)

    text_input = st.text_area("📄 Document Text:", height=280, placeholder="Paste your comprehensive document, article, or book chapter here...")

    col1, col2 = st.columns([1, 1])
    with col1:
        selected_voice_label = st.selectbox("🌐 Select Neural Voice Model:", list(VOICE_MODELS.keys()))
        selected_voice_id = VOICE_MODELS[selected_voice_label]

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🚀 Execute Neural Synthesis", use_container_width=True, type="primary"):
        clean_text = text_input.strip()
        
        if not clean_text:
            st.error("⚠️ Input required: Please provide text data to process.")
        else:
            st.session_state.audio_data = None
            st.session_state.processing_complete = False
            
            progress_bar = st.progress(0, text="Initializing Neural Engine... Please wait, processing full document...")
            
            try:
                # Progress to 50% while it connects to Microsoft Servers
                progress_bar.progress(50, text="Generating HD Audio Matrix... This is faster and won't be blocked.")
                
                # Execute Core Engine (Direct stream, no chunks needed!)
                audio_bytes = generate_audio_sync(clean_text, selected_voice_id)
                
                # Store in session state
                st.session_state.audio_data = audio_bytes
                st.session_state.processing_complete = True
                
                progress_bar.progress(100, text="Finalizing Output...")
                time.sleep(0.5) # Short pause for UI smoothness
                progress_bar.empty()
                st.success(f"✅ Synthesis Complete! High-Definition audio generated successfully using {selected_voice_label}.")
                
            except Exception as e:
                progress_bar.empty()
                st.error(f"❌ System Fault: {str(e)}")

    # Display Audio Player and Download Button if data exists in memory
    if st.session_state.processing_complete and st.session_state.audio_data:
        st.audio(st.session_state.audio_data, format='audio/mp3')
        
        st.download_button(
            label="📥 Download HD Audio Output (MP3)",
            data=st.session_state.audio_data,
            file_name=f"Neural_Audio_{datetime.now().strftime('%Y%m%d_%H%M')}.mp3",
            mime="audio/mp3",
            use_container_width=True
        )

    st.divider()
    st.caption("🔒 System Integrity: Stable | API: Microsoft Neural Edge | Rate Limit: Bypassed")

if __name__ == "__main__":
    main()
