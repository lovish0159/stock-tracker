import streamlit as st
from gtts import gTTS
import io
import time
import logging
from datetime import datetime
from typing import List, Optional

# ==========================================
# 1. ENTERPRISE CONFIGURATION & LOGGING
# ==========================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
st.set_page_config(page_title="Pro Audio Synthesizer", page_icon="🎙️", layout="centered")

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
# 2. CORE AUDIO ENGINE (OOP Architecture)
# ==========================================
class TTSEngine:
    """Professional Text-to-Speech Engine with chunking and exponential backoff."""
    
    def __init__(self, chunk_size: int = 1500, max_retries: int = 4, base_delay: float = 2.0):
        self.chunk_size = chunk_size
        self.max_retries = max_retries
        self.base_delay = base_delay

    def _split_text(self, text: str) -> List[str]:
        """Splits text cleanly without cutting words in half."""
        words = text.split()
        chunks, current_chunk = [], []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > self.chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += len(word) + 1
                
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        return chunks

    def synthesize(self, text: str, lang: str, progress_bar) -> Optional[bytes]:
        """Synthesizes text to audio bytes using secure chunking and anti-ban protocol."""
        chunks = self._split_text(text)
        total_chunks = len(chunks)
        master_buffer = io.BytesIO()
        
        logging.info(f"Initiating synthesis for {total_chunks} chunks in language: {lang}")

        for index, chunk in enumerate(chunks):
            delay = self.base_delay
            success = False
            
            for attempt in range(self.max_retries):
                try:
                    tts = gTTS(text=chunk, lang=lang, slow=False)
                    chunk_buffer = io.BytesIO()
                    tts.write_to_fp(chunk_buffer)
                    master_buffer.write(chunk_buffer.getvalue())
                    success = True
                    break # Break retry loop on success
                    
                except Exception as e:
                    if "429" in str(e):
                        logging.warning(f"Rate limited on chunk {index+1}. Attempt {attempt+1}/{self.max_retries}. Retrying in {delay}s...")
                        time.sleep(delay)
                        delay *= 2 # Exponential Backoff (2s -> 4s -> 8s)
                    else:
                        logging.error(f"TTS Error: {e}")
                        raise e
            
            if not success:
                raise Exception(f"Failed to process segment {index+1} after {self.max_retries} attempts.")

            # Polite delay between successful chunks to avoid triggering 429
            if index < total_chunks - 1:
                time.sleep(1.5)
            
            # Update UI Progress
            percent_complete = int(((index + 1) / total_chunks) * 100)
            progress_bar.progress(percent_complete, text=f"⚙️ Synthesizing data matrix: {index + 1}/{total_chunks} segments completed...")

        logging.info("Audio synthesis completed successfully.")
        return master_buffer.getvalue()

# ==========================================
# 3. STATE MANAGEMENT
# ==========================================
def init_session_state():
    """Initializes session variables to persist audio data across reruns."""
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

    st.markdown("<div class='main-header'>🎙️ Pro Audio Synthesizer</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Enterprise-Grade Text-to-Speech with Auto-Chunking & Anti-Ban Security</div>", unsafe_allow_html=True)

    text_input = st.text_area("📄 Document Text:", height=250, placeholder="Paste your comprehensive document, article, or book chapter here...")

    col1, col2 = st.columns([1, 1])
    with col1:
        lang_choice = st.selectbox("🌐 Voice Algorithm:", [
            ("English", "en"), 
            ("Hindi", "hi"),
            ("Punjabi", "pa")
        ], format_func=lambda x: x[0])

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🚀 Execute Neural Synthesis", use_container_width=True, type="primary"):
        clean_text = text_input.strip()
        
        if not clean_text:
            st.error("⚠️ Input required: Please provide text data to process.")
        else:
            # Reset state for new processing
            st.session_state.audio_data = None
            st.session_state.processing_complete = False
            
            progress_bar = st.progress(0, text="Initializing synthesis engine...")
            engine = TTSEngine(chunk_size=1200) # Slightly stricter chunk size for utmost safety
            
            try:
                # Execute Core Engine
                audio_bytes = engine.synthesize(clean_text, lang_choice[1], progress_bar)
                
                # Store in session state
                st.session_state.audio_data = audio_bytes
                st.session_state.processing_complete = True
                
                progress_bar.empty()
                st.success("✅ Synthesis Complete! Master audio file generated successfully.")
                
            except Exception as e:
                progress_bar.empty()
                st.error(f"❌ System Fault: {str(e)}")

    # Display Audio Player and Download Button if data exists in memory
    if st.session_state.processing_complete and st.session_state.audio_data:
        st.audio(st.session_state.audio_data, format='audio/mp3')
        
        st.download_button(
            label="📥 Download Secure Audio Output (MP3)",
            data=st.session_state.audio_data,
            file_name=f"Pro_Synthesis_{datetime.now().strftime('%Y%m%d_%H%M')}.mp3",
            mime="audio/mp3",
            use_container_width=True
        )

    st.divider()
    st.caption("🔒 System Integrity: Stable | Exponential Backoff: Active | Chunking: Optimized")

if __name__ == "__main__":
    main()
    
