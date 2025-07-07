import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from PIL import Image

# CSS yükle
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("📸 Akıllı Sesli Asistan (Görsel Yok, Sadece Sesli Sonuç)")

load_dotenv()
google_api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
if not google_api_key:
    st.error("Google API Key bulunamadı. Lütfen .env dosyanızı kontrol edin.")
    st.stop()

genai.configure(api_key=google_api_key)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

kamera_secimi = st.radio("Kamera Seçimi:", ("Arka Kamera", "Ön Kamera"))

info_area = st.empty()

# Kamera inputunu gizle
hide_camera_css = """
<style>
    [data-testid="stCameraInput"] {display: none !important;}
</style>
"""
st.markdown(hide_camera_css, unsafe_allow_html=True)

# Oturumda resmi saklamak için
if "cekilen_resim" not in st.session_state:
    st.session_state["cekilen_resim"] = None

# Büyük buton ile fotoğraf çekme
st.markdown(
    """
    <div style="text-align:center;">
        <form action="" method="post">
            <button class="big-button" style="width:90%;font-size:2.5em;" type="submit">📷 Resim Çek</button>
        </form>
    </div>
    """, unsafe_allow_html=True
)
capture_btn = st.camera_input("", key="kalici_resim", label_visibility="collapsed")

# 1. RESIM ÇEKİLİNCE İŞLE
if capture_btn:
    try:
        img = Image.open(capture_btn)
        st.session_state["cekilen_resim"] = img
        info_area.info("🟢 Fotoğraf çekildi, modele gönderiliyor...")
        yanit = model.generate_content([img, "Bu resimde neler var?"]).text
        info_area.success("✅ Yanıt alındı ve seslendiriliyor...")
        speak_html = f"""
        <script>
        var msg = new SpeechSynthesisUtterance({yanit!r});
        msg.lang = 'tr-TR';
        window.speechSynthesis.speak(msg);
        </script>
        """
        st.components.v1.html(speak_html, height=0)
    except Exception as e:
        info_area.error(f"❌ Hata: {e}")

# ======= Mikrofon HTML ve JS =======
mic_html = """
<div>
  <button class="big-button" id="start-record" style="width:100%;font-size:2em;">🎤 Yeniden Sor (Mikrofon)</button>
  <p id="mic-result" style="font-weight:bold; font-size:1.3em"></p>
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
      window.parent.postMessage(
        {isStreamlitMessage: true, type: "streamlit:setComponentValue", data: text},
        "*"
      );
      btn.innerText = "🎤 Yeniden Sor (Mikrofon)";
    };

    recognition.onerror = (e) => {
      result.innerText = "Hata: " + e.error;
      btn.innerText = "🎤 Yeniden Sor (Mikrofon)";
    };
  } else {
    result.innerText = "Tarayıcı mikrofon desteği yok!";
    btn.disabled = true;
  }
</script>
"""
mic_text = st.components.v1.html(mic_html, height=220)

# 2. MİKROFONLA YENİ PROMPT GELİRSE AYNI RESİMLE İŞLE
prompt_text = st.session_state.get("component_value")
if prompt_text and st.session_state["cekilen_resim"] is not None:
    info_area.info("🟢 Yeni sesli prompt alındı, aynı resim ile modele gönderiliyor...")
    try:
        yanit = model.generate_content([st.session_state["cekilen_resim"], prompt_text]).text
        info_area.success("✅ Yanıt alındı ve seslendiriliyor...")
        speak_html = f"""
        <script>
        var msg = new SpeechSynthesisUtterance({yanit!r});
        msg.lang = 'tr-TR';
        window.speechSynthesis.speak(msg);
        </script>
        """
        st.components.v1.html(speak_html, height=0)
    except Exception as e:
        info_area.error(f"❌ Hata: {e}")

st.info("Fotoğraf çekince resim ve sabit prompt gönderilir, cevap otomatik seslendirilir. Mikrofonla yeni soru sorarsan, aynı resimle konuşmaya devam edilir. Yazılı cevap ekranda görünmez.")

