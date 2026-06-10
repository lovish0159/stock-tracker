import streamlit as st
import asyncio
import edge_tts
import re
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
# 2. CORE AI NEURAL ENGINE
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

async def synthesize_neural_audio(text: str, voice_name: str, speed: int) -> bytes:
    """Streams unlimited text directly to audio buffer."""
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
# 3. USER INTERFACE
# ==========================================
def main():
    # Memory Setup
    if "audio_data" not in st.session_state:
        st.session_state.audio_data = None
        
    st.markdown("<div class='main-header'>⚡ Ultra AI Audio Engine</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Unlimited Text | High-Speed AI | Zero Errors</div>", unsafe_allow_html=True)

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
            st.session_state.audio_data = None
            progress_bar = st.progress(0, text="⚡ Establishing AI Connection...")
            
            try:
                progress_bar.progress(50, text="Processing Unlimited Text at High Speed...")
                
                # Execute Core Engine
                audio_bytes = generate_audio_sync(clean_text, selected_voice_id, speech_speed)
                st.session_state.audio_data = audio_bytes
                
                progress_bar.progress(100, text="✅ Audio Successfully Generated!")
                st.success("🎉 Conversion Complete! Ready to Play and Download.")
                progress_bar.empty()
                
            except Exception as e:
                progress_bar.empty()
                st.error(f"❌ System Fault: {str(e)}")

            # Secure Player & Download Section
    st.divider()
    if st.session_state.audio_data:
        st.markdown("### 🎧 Play & Save Audio")
        st.audio(st.session_state.audio_data, format='audio/mp3')
        
        # ==========================================
        # 🔍 EXPERT DIAGNOSTIC TOOL
        # ==========================================
        st.markdown("### 🛠️ System Diagnostic Info")
        
        # Calculate precise file size in Megabytes (MB)
        file_size_bytes = len(st.session_state.audio_data)
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        st.info(f"📊 **Actual Audio File Size:** {file_size_mb:.2f} MB")
        
        if file_size_mb > 1.5:
            st.error("🚨 **Root Cause Found:** Aapki file 1.5 MB se badi hai! Mobile browsers itni badi file ko 'Force Download' (Base64) ya Streamlit ke default button se direct download hone se block kar dete hain.")
            st.success("💡 **The ONLY Solution for Large Files on Mobile:** Upar diye gaye Black Audio Player ke right side mein **3-dots (⋮)** par click karein aur wahan se **'Download'** select karein. Yeh browser ka direct system hai, jo kabhi fail nahi hota!")
        else:
            st.warning("⚠️ File size safe limit mein hai. Agar phir bhi download nahi ho raha, toh iska matlab aap kisi App (WhatsApp/Telegram) ke internal browser mein hain. Kripya is link ko Chrome mein open karein.")
        
        # Standard Streamlit Button
        st.download_button(
            label="📥 Save Audio File (Streamlit Native)",
            data=st.session_state.audio_data,
            file_name=f"AI_Audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3",
            mime="audio/mp3",
            use_container_width=True
        )
        
        # Force Download HTML Link
        import base64
        b64 = base64.b64encode(st.session_state.audio_data).decode()
        file_name = f"AI_Audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        href = f'''
        <div style="text-align: center; margin-top: 15px;">
            <a href="data:audio/mp3;base64,{b64}" download="{file_name}" 
               style="display: inline-block; padding: 12px 24px; background-color: #16a34a; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; width: 100%; box-sizing: border-box;">
               🚀 Force Download (Alternative)
            </a>
        </div>
        '''
        st.markdown(href, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
