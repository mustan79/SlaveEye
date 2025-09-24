import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from PIL import Image
import io

# CSS yükle
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("📸 Akıllı Asistan (Tarayıcıda Sesli)")

# Çevresel değişkenleri yükle
load_dotenv()
google_api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
if not google_api_key:
    st.error("Google API Key bulunamadı. Lütfen .env dosyanızı kontrol edin.")
    st.stop()

# Gemini API yapılandırması
genai.configure(api_key=google_api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

# Global değişkenler
son_cekilen_resim = None
info_area = st.empty()

def speak(text):
    info_area.info(text)
    speak_html = f"""
    <script>
    var msg = new SpeechSynthesisUtterance({text!r});
    msg.lang = 'tr-TR'; window.speechSynthesis.speak(msg);
    </script>"""
    st.components.v1.html(speak_html, height=0)

if "mic_prompt" not in st.session_state:
    st.session_state["mic_prompt"] = None
mic_flag = False # Başlangıçta False olmalı

# ======= TARAYICI MİKROFON - SES TO TEXT =======
mic_html = """
<div>
  <button class="big-button" id="start-record">🎤 Mikrofondan Konuş</button>
  <p id="mic-result" style="font-weight:bold; font-size:1.2em"></p>
</div>
<script>
  const btn = document.getElementById('start-record');
  const result = document.getElementById('mic-result');
  let recognition;
  if ('webkitSpeechRecognition' in window) {
    recognition = new webkitSpeechRecognition();
    recognition.lang = "tr-TR";
    recognition.continuous = false;
    recognition.interimResults = false;

    btn.onclick = () => {
      recognition.start();
      btn.innerText = "Dinleniyor...";
    };

    recognition.onresult = (e) => {
      let text = e.results[0][0].transcript;
      result.innerText = text;
      // Streamlit yazılı inputa otomatik aktarım için:
      window.parent.postMessage({isStreamlitMessage: true, type: "streamlit:setComponentValue", data: text}, "*");
      btn.innerText = "🎤 Mikrofondan Konuş";
    };

    recognition.onerror = (e) => {
      result.innerText = "Hata: " + e.error;
      btn.innerText = "🎤 Mikrofondan Konuş";
    };
  } else {
    result.innerText = "Tarayıcı mikrofon desteği yok!";
    btn.disabled = true;
  }
</script>
"""

mic_text = st.components.v1.html(mic_html, height=200)

if mic_data == 'mic_started':
    # Sadece mikrofon başladıysa flag'i ayarla
    mic_flag = True

elif mic_data:
    # Mikrofon verisi geldiyse hem prompt'u ayarla, hem de flag'i true yap
    st.session_state["mic_prompt"] = mic_data
    mic_flag = True


# ======= UI =======
# Kamera seçimi (Mobil için)
kamera_secimi = st.radio("Kamera Seçimi:", ("Arka Kamera", "Ön Kamera"))

# Resim çekme butonu
captured_image = st.camera_input("2. Resim Çek",key="kalici_resim")
if captured_image:
    son_cekilen_resim = Image.open(captured_image)
    st.image(captured_image, caption="Çekilen Resim", use_column_width=True)
#    prompt = "Bu resimde neler görüyorsun anlat."
    speak("Modelden yanıt bekleniyor...")
    prompt = st.session_state["mic_prompt"] if mic_flag else "Bu resimde neler var?"
    yanit = model.generate_content([img, prompt]).text
    speak(yanit)


col1, col2 = st.columns([2,1])
with col1:
    st.markdown("Mikrofondan aldığınız metin otomatik buraya gelir.")

