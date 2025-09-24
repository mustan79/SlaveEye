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
mic_flag = 0


resim = st.camera_input("Kamera ile fotoğraf çek")
if resim:
    # Resmi PIL Image objesine çevir
    img = Image.open(resim)
    speak("Modelden yanıt bekleniyor...")
    if mic_flag ==1;
        prompt = st.session_state["mic_prompt"]
        st.session_state["step"] = None
        st.session_state["mic_prompt"] = None
    else;
        prompt = "Bu resimde neler var?"

    yanit = model.generate_content([img, prompt]).text
    speak(yanit)
#    st.stop()



# --- Mikrofon akışı ---
st.session_state["mic_prompt"] = None
st.session_state["component_value"] = None

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
else {
  result.innerText = "Tarayıcı mikrofon desteği yok!";
  btn.disabled = false;
}
</script>
"""
st.components.v1.html(mic_html, height=230)
mic_value = st.session_state.get("component_value")
if mic_value:
    st.session_state["mic_prompt"] = mic_value
    mic_flag = 1


#