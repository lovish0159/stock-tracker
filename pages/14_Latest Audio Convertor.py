import streamlit as st
import asyncio
import edge_tts
import re
import os
from datetime import datetime

# ==========================================
# 1. ENTERPRISE CONFIGURATION
# ==========================================
st.set_page_config(page_title="Ultra AI Audio Engine", page_icon="⚡", layout="centered")

st.markdown("""
    <style>
        #MainMenu, footer, header {visibility: hidden;}
        .main-header { font-size: 2.5rem; color: #1e293b; text-align: center; font-weight: 800; margin-bottom: 0px;}
        .sub-header { text-align: center; color: #475569; margin-bottom: 2rem; font-size: 16px;}
        .stTextArea textarea { font-size: 16px; border-radius: 12px; border: 1px solid #cbd5e1; padding: 15px;}
        div.stButton > button { border-radius: 8px; font-weight: 600; padding: 0.5rem 1rem; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CORE AI NEURAL ENGINE (Disk Saving)
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
    """Cleans text for uninterrupted speedy TTS."""
    text = re.sub(r'\n+', ' ', text)  
    text = re.sub(r'\s+', ' ', text)  
    return text.strip()

async def synthesize_and_save_audio(text: str, voice_name: str, speed: int, file_path: str):
    """Streams unlimited text and directly writes it to a PHYSICAL file on the server."""
    speed_str = f"{speed:+d}%" 
    communicate = edge_tts.Communicate(text, voice_name, rate=speed_str)
    # 🎯 EXPERT FIX: Save physically to disk instead of memory chunking
    await communicate.save(file_path)

def generate_audio_sync(text: str, voice_name: str, speed: int, file_path: str):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_until_complete(synthesize_and_save_audio(text, voice_name, speed, file_path))

# ==========================================
# 3. USER INTERFACE
# ==========================================
def main():
    # Session State
    if "generated_file_path" not in st.session_state:
        st.session_state.generated_file_path = None
        
    st.markdown("<div class='main-header'>⚡ Ultra AI Audio Engine</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Physical Disk Storage | Zero Timeout Drops</div>", unsafe_allow_html=True)

    text_input = st.text_area("📝 Paste Unlimited Text Here:", height=250, placeholder="Type or paste any amount of text here...")

    col1, col2 = st.columns([1, 1])
    with col1:
        selected_voice_label = st.selectbox("🌐 Select AI Voice:", list(VOICE_MODELS.keys()))
        selected_voice_id = VOICE_MODELS[selected_voice_label]
    with col2:
        speech_speed = st.slider("⏱️ Audio Speed (%)", min_value=-50, max_value=50, value=0, step=5)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🚀 Convert to Audio", use_container_width=True, type="primary"):
        clean_text = sanitize_text(text_input)
        
        if not clean_text:
            st.error("⚠️ Error: Please enter some text first.")
        else:
            st.session_state.generated_file_path = None
            progress_bar = st.progress(0, text="⚡ Establishing AI Connection...")
            
            try:
                progress_bar.progress(50, text="Writing audio directly to server Hard Drive...")
                
                # Create a physical file path
                current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
                temp_file_name = f"Audio_{current_time}.mp3"
                
                # Execute Core Engine to save directly to disk
                generate_audio_sync(clean_text, selected_voice_id, speech_speed, temp_file_name)
                
                # Store the file path in state
                st.session_state.generated_file_path = temp_file_name
                
                progress_bar.progress(100, text="✅ Audio Successfully Written to Disk!")
                st.success("🎉 Conversion Complete! Ready to Play and Download.")
                progress_bar.empty()
                
            except Exception as e:
                progress_bar.empty()
                st.error(f"❌ System Fault: {str(e)}")

    # Secure Player & Download Section
    st.divider()
    if st.session_state.generated_file_path and os.path.exists(st.session_state.generated_file_path):
        st.markdown("### 🎧 Play & Save Audio")
        
        # Open the physical file for reading
        with open(st.session_state.generated_file_path, "rb") as file_handle:
            # Play from physical file
            st.audio(file_handle, format='audio/mp3')
            
            # Download directly from physical file handler (prevents mobile timeouts)
            st.download_button(
                label="📥 Download Secure Audio File (MP3)",
                data=file_handle,
                file_name=st.session_state.generated_file_path,
                mime="audio/mp3",
                use_container_width=True
            )
            
        st.info("💡 **Pro Tip:** Agar upar wala Red Button fail ho, tabhi Black Player ke **3-dots (⋮)** se download karein. File disk par hai, isliye ab connection failed nahi hoga.")

if __name__ == "__main__":
    main()
