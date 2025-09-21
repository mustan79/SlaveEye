import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from PIL import Image

# --- CSS: Butonları büyük yap, kamera inputunu gizle ---
st.markdown("""
<style>
    .big-btn {width:96vw; height:8vh; font-size:3em; margin:1vh 0;}
    [data-testid="stCameraInput"] {display: none !important;}
</style>
""", unsafe_allow_html=True)

st.title("🔊 Akıllı Sesli Asistan")

# --- API Key Yükle ---
load_dotenv()
google_api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
if not google_api_key:
    st.error("Google API Key bulunamadı. Lütfen .env dosyanızı kontrol edin.")
    st.stop()

genai.configure(api_key=google_api_key)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

info_area = st.empty()

# --- Session State Başlat ---
for k, v in [
    ("cekilen_resim", None),
    ("mic_prompt", None),
    ("step", None),
    ("mic_listen", False),
    ("mic_value", None)
]:
    if k not in st.session_state:
        st.session_state[k] = v

# --- Ana Butonlar ---
col1, col2 = st.columns(2)
with col1:
    foto_btn = st.button("📷 Resim Çek", key="btn_foto", use_container_width=True)
with col2:
    mic_btn = st.button("🎤 Mikrofonla Sor", key="btn_mic", use_container_width=True)

# --- Kamera Inputu (her zaman hazır, gizli) ---
camera_file = st.camera_input("", key="cam_input", label_visibility="collapsed")

def speak(text):
    # Ekranda göster + sesli okut
    info_area.info(text)
    speak_html = f"""
    <script>
    var msg = new SpeechSynthesisUtterance({text!r});
    msg.lang = 'tr-TR'; window.speechSynthesis.speak(msg);
    </script>"""
    st.components.v1.html(speak_html, height=0)

# --- FOTOĞRAF ÇEKME AKIŞI ---
if foto_btn:
    st.session_state["step"] = "foto"
    speak("Kamera açılıyor, lütfen fotoğraf çekin ve yükleyin.")
    st.stop()

if st.session_state["step"] == "foto" and camera_file:
    try:
        img = Image.open(camera_file)
        st.session_state["cekilen_resim"] = img
        speak("🟢 Modelden yanıt bekleniyor...")
        yanit = model.generate_content([img, "Bu resimde neler var?"]).text
        speak("✅ Yanıt seslendiriliyor...")
        speak(yanit)
        st.session_state["step"] = None
    except Exception as e:
        speak(f"Hata: {e}")
        st.session_state["step"] = None

# --- MİKROFON AKIŞI ---
if mic_btn:
    st.session_state["step"] = "mic"
    st.session_state["mic_listen"] = True

if st.session_state.get("mic_listen"):
    mic_html = """
    <div>
      <button class="big-btn" id="start-record">🎤 Konuşmaya Başla</button>
      <p id="mic-result" style="font-weight:bold; font-size:1.5em"></p>
    </div>
    <script>
    const btn = document.getElementById('start-record');
    const result = document.getElementById('mic-result');
    if ('webkitSpeechRecognition' in window) {
      let recognition = new webkitSpeechRecognition();
      recognition.lang = "tr-TR"; recognition.continuous = false; recognition.interimResults = false;
      btn.onclick = () => { recognition.start(); btn.innerText = "Dinleniyor..."; };
      recognition.onresult = (e) => {
        let text = e.results[0][0].transcript;
        result.innerText = text;
        window.parent.postMessage({isStreamlitMessage: true, type: "streamlit:setComponentValue", data: text}, "*");
        btn.innerText = "🎤 Konuşmaya Başla";
      };
      recognition.onerror = (e) => { result.innerText = "Hata: " + e.error; btn.innerText = "🎤 Konuşmaya Başla"; };
    } else {
      result.innerText = "Tarayıcı mikrofon desteği yok!";
      btn.disabled = true;
    }
    </script>
    """
    st.components.v1.html(mic_html, height=230)
    mic_value = st.session_state.get("component_value")
    if mic_value:
        st.session_state["mic_prompt"] = mic_value
        st.session_state["mic_listen"] = False
        st.session_state["step"] = "mic_photo"
        speak("Şimdi fotoğraf çekmeniz gerekiyor. Kamera açılıyor.")
        st.stop()

# --- MİKROFON SONRASI FOTOĞRAF AKIŞI ---
if st.session_state["step"] == "mic_photo" and camera_file:
    try:
        img = Image.open(camera_file)
        st.session_state["cekilen_resim"] = img
        prompt = st.session_state["mic_prompt"] or "Bu resimde neler var?"
        speak("🟢 Modelden yanıt bekleniyor...")
        yanit = model.generate_content([img, prompt]).text
        speak("✅ Yanıt seslendiriliyor...")
        speak(yanit)
        st.session_state["mic_prompt"] = None
        st.session_state["step"] = None
    except Exception as e:
        speak(f"Hata: {e}")
        st.session_state["step"] = None

st.info("""
- 📷 **Resim Çek:** Kameradan fotoğraf çek, model yanıtını otomatik seslendirir.
- 🎤 **Mikrofonla Sor:** Konuş, ardından fotoğraf çekmeni ister, ikisini birlikte modele yollar ve yanıtı seslendirir.
""")

