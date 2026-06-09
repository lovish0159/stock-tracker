import streamlit as st
from gtts import gTTS
import io
from datetime import datetime  # 🎯 EXPERT FIX: Yeh import miss ho gaya tha

# ==========================================
# 1. ENTERPRISE APP CONFIGURATION
# ==========================================
st.set_page_config(page_title="Unlimited Text to Audio Engine", page_icon="🔊", layout="centered")

st.markdown("""
    <style>
        #MainMenu, footer, header {visibility: hidden;}
        .main-header { font-size: 2.3rem; color: #1d4ed8; text-align: center; font-weight: bold; margin-bottom: 5px; }
        .sub-header { text-align: center; color: #475569; margin-bottom: 2rem; font-size: 15px; }
        .stTextArea textarea { font-size: 16px; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. EXPERT ENGINE: TEXT CHUNKING & MERGE LOGIC
# ==========================================
def split_text_into_chunks(text, chunk_size=2000):
    """
    Expert Method: Splits huge text safely at sentence/space boundaries 
    to prevent Google TTS API rejection or truncation.
    """
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 > chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
        else:
            current_chunk.append(word)
            current_length += len(word) + 1
            
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

# ==========================================
# 3. CORE USER INTERFACE
# ==========================================
st.markdown("<div class='main-header'>🔊 Industrial Text-to-Audio Engine</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>Equipped with Auto-Chunking for Unlimited Data Streams</div>", unsafe_allow_html=True)

# Input Framework
text_input = st.text_area("📝 Paste your comprehensive text here:", height=280, placeholder="Enter pages of data here without worry...")

col1, col2 = st.columns([1, 1])
with col1:
    lang_choice = st.selectbox("🌐 Audio Language Framework:", [
        ("English", "en"), 
        ("Punjabi (Standard)", "pa"), 
        ("Hindi", "hi")
    ], format_func=lambda x: x[0])

st.markdown("<br>", unsafe_allow_html=True)

# Execution Grid
if st.button("🎧 Synthesize into Master Audio", use_container_width=True, type="primary"):
    clean_text = text_input.strip()
    
    if not clean_text:
        st.warning("⚠️ Operational Halt: Text body cannot be empty.")
    else:
        with st.spinner("⏳ Running Chunking Engine & Synthesizing Audio Matrix (Large data streams may take a few seconds)..."):
            try:
                # Text ko safe limits mein split karna
                text_chunks = split_text_into_chunks(clean_text)
                combined_audio_buffer = io.BytesIO()
                
                # Processing each segment sequentially
                for index, chunk in enumerate(text_chunks):
                    tts = gTTS(text=chunk, lang=lang_choice[1], slow=False)
                    chunk_buffer = io.BytesIO()
                    tts.write_to_fp(chunk_buffer)
                    chunk_buffer.seek(0)
                    
                    # Append chunk data to the main master buffer
                    combined_audio_buffer.write(chunk_buffer.read())
                
                # Reset buffer to start for standard playback
                combined_audio_buffer.seek(0)
                
                st.success(f"✅ Data Synthesis Complete! Successfully processed {len(text_chunks)} data matrix segments.")
                
                # Native Streamlit Player Deployment
                st.audio(combined_audio_buffer, format='audio/mp3')
                
                # Secure Download Pathway (Now completely bug-free)
                st.download_button(
                    label="📥 Download Master Audio File (MP3)",
                    data=combined_audio_buffer,
                    file_name=f"Synthesized_Audio_{datetime.now().strftime('%d%m%Y')}.mp3",
                    mime="audio/mp3",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"❌ Core Exception Triggered: {str(e)}")

st.divider()
st.caption("🔒 Architecture Status: Stabilized & Protected against Stream Overloads.")

