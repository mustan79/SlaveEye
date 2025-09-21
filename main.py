import streamlit as st
#from streamlit_camera_input_live import camera_input_live
from PIL import Image
import google.generativeai as genai

st.title("🔊 Akıllı Sesli Asistan")

# API anahtarı Streamlit secrets üzerinden alınır
google_api_key = st.secrets.get("GEMINI_API_KEY")
if not google_api_key:
    st.error("Google API Key bulunamadı. Lütfen Streamlit secrets'a ekleyin.")
    st.stop()

genai.configure(api_key=google_api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

st.markdown("""
<style>
    .big-btn {width:96vw; height:8vh; font-size:3em; margin:1vh 0;}
</style>
""", unsafe_allow_html=True)

info_area = st.empty()

def speak(text):
    info_area.info(text)
    speak_html = f"""
    <script>
    var msg = new SpeechSynthesisUtterance({text!r});
    msg.lang = 'tr-TR'; window.speechSynthesis.speak(msg);
    </script>"""
    st.components.v1.html(speak_html, height=0)

if "step" not in st.session_state:
    st.session_state["step"] = None
if "mic_prompt" not in st.session_state:
    st.session_state["mic_prompt"] = None
if "component_value" not in st.session_state:
    st.session_state["component_value"] = None

col1, col2 = st.columns(2)
with col1:
    foto_btn = st.button("📷 Resim Çek", use_container_width=True)
with col2:
    mic_btn = st.button("🎤 Mikrofonla Sor", use_container_width=True)

# --- Kamera ile tek tık akışı ---
if foto_btn or st.session_state["step"] == "foto":
    st.session_state["step"] = "foto"
    img_bytes = st.camera_input("Kamera ile fotoğraf çek", format="png")
    if img_bytes:
        img = Image.open(img_bytes)
        speak("🟢 Modelden yanıt bekleniyor...")
        yanit = model.generate_content([img, "Bu resimde neler var?"]).text
        speak("✅ Yanıt seslendiriliyor...")
        speak(yanit)
        st.session_state["step"] = None
    st.stop()

# --- Mikrofon akışı ---
if mic_btn:
    st.session_state["step"] = "mic"
    st.session_state["mic_prompt"] = None
    st.session_state["component_value"] = None

if st.session_state["step"] == "mic":
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
        st.session_state["step"] = "mic_photo"
        speak("Şimdi kamera açılıyor ve fotoğraf çekilecek.")
        st.stop()

if st.session_state["step"] == "mic_photo":
    img_bytes = st.camera_input("Kamera ile fotoğraf çek", key="cam_input_mic", format="png")
    if img_bytes and st.session_state["mic_prompt"]:
        img = Image.open(img_bytes)
        prompt = st.session_state["mic_prompt"]
        speak("🟢 Modelden yanıt bekleniyor...")
        yanit = model.generate_content([img, prompt]).text
        speak("✅ Yanıt seslendiriliyor...")
        speak(yanit)
        st.session_state["step"] = None
        st.session_state["mic_prompt"] = None
    st.stop()

st.info("""
- 📷 **Resim Çek:** Butona bir defa bastığında kamera açılır, fotoğraf çekilir, model yanıtı sesli olarak dinlettirilir.
- 🎤 **Mikrofonla Sor:** Konuş, ardından fotoğraf çekmeni ister, ikisini modele yollar ve yanıtı seslendirir.
- Tüm akışlar sade, tek tık ve sesli bildirimlidir.
""")
