import streamlit as st
from gtts import gTTS
import io

# ==========================================
# 1. APP CONFIGURATION
# ==========================================
st.set_page_config(page_title="Unlimited Text to Audio", page_icon="🔊", layout="centered")

# Custom CSS for better UI styling
st.markdown("""
    <style>
        .main-header { font-size: 2.5rem; color: #1d4ed8; text-align: center; font-weight: bold; }
        .sub-header { text-align: center; color: #475569; margin-bottom: 2rem; }
        .stTextArea textarea { font-size: 16px; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. UI LAYOUT & LOGIC
# ==========================================
st.markdown("<div class='main-header'>🔊 Text to Audio Converter</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>Jinna marji wadda text likho, eh app usnu MP3 vich convert kar devegi!</div>", unsafe_allow_html=True)

# User input for text
text_input = st.text_area("📝 Apna text ethe paste karo:", height=250, placeholder="Ethe apna text likho ya paste karo...")

# Language Selection (Optional but useful)
col1, col2 = st.columns([1, 1])
with col1:
    lang_choice = st.selectbox("🌐 Audio di Bhasha (Language) chuno:", [
        ("English", "en"), 
        ("Punjabi", "pa"), 
        ("Hindi", "hi")
    ], format_func=lambda x: x[0])

# ==========================================
# 3. AUDIO GENERATION ENGINE
# ==========================================
st.markdown("<br>", unsafe_allow_html=True)

if st.button("🎧 Convert to Audio", use_container_width=True, type="primary"):
    if text_input.strip() == "":
        st.warning("⚠️ Kirpa karke pehlan koi text likho!")
    else:
        with st.spinner("⏳ Audio generate ho rahi hai... kirpa karke udeek karo (wadda text thoda time lai sakda hai)..."):
            try:
                # Text nu speech vich convert karna
                tts = gTTS(text=text_input, lang=lang_choice[1], slow=False)
                
                # Audio nu memory vich save karna (Hard disk te save karan di lorh nahi)
                audio_bytes = io.BytesIO()
                tts.write_to_fp(audio_bytes)
                audio_bytes.seek(0)
                
                st.success("✅ Audio bilkul tyar hai!")
                
                # App de andar audio player show karna
                st.audio(audio_bytes, format='audio/mp3')
                
                # Download button
                st.download_button(
                    label="⬇️ Audio file Download Karo (MP3)",
                    data=audio_bytes,
                    file_name="converted_audio.mp3",
                    mime="audio/mp3",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"❌ Koi technical error aagya: {e}")

# Footer
st.markdown("---")
st.caption("Developed securely for Streamlit Cloud")
