import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from PIL import Image
import io
import base64

# CSS yükle
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("📸 Akıllı Sesli Asistan")

# Çevresel değişkenleri yükle
load_dotenv()
google_api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
if not google_api_key:
    st.error("Google API Key bulunamadı. Lütfen .env dosyanızı kontrol edin.")
    st.stop()

# Gemini API yapılandırması
genai.configure(api_key=google_api_key)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# ======= Kamera seçimi =======
kamera_secimi = st.radio("Kamera Seçimi:", ("Arka Kamera", "Ön Kamera"))

# ======= Bilgilendirme mesajı =======
info_area = st.empty()

# ======= Mikrofon HTML ve JS (yalnızca sesli giriş, erişilebilir) =======
mic_html = """
<div>
  <button class="big-button" id="start-record" style="width:100%;font-size:2em;">🎤 Konuşmak için tıkla</button>
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
      // Streamlit'e aktar
      window.parent.postMessage(
        {isStreamlitMessage: true, type: "streamlit:setComponentValue", data: text},
        "*"
      );
      btn.innerText = "🎤 Konuşmak için tıkla";
    };

    recognition.onerror = (e) => {
      result.innerText = "Hata: " + e.error;
      btn.innerText = "🎤 Konuşmak için tıkla";
    };
  } else {
    result.innerText = "Tarayıcı mikrofon desteği yok!";
    btn.disabled = true;
  }
</script>
"""

mic_text = st.components.v1.html(mic_html, height=220)

# ======= Arka planda fotoğraf çekme =======
# Kamera inputu ekranda görünmeden, sadece dosya olarak alınacak

st.markdown(
    '<div style="display:flex;justify-content:center;margin:1em 0;">'
    '<span style="font-size:1.2em;font-weight:bold;">'
    '📷 Fotoğraf çekmek için aşağıdaki büyük butona tıkla'
    '</span></div>',
    unsafe_allow_html=True
)

# Büyük, erişilebilir resim çekme butonu
capture_col = st.columns([1, 8, 1])
with capture_col[1]:
    # Kamera inputu sadece dosya olarak alınıyor, ekranda görüntü yok
    capture_btn = st.camera_input(
        "", key="kalici_resim", label_visibility="collapsed"
    )

# ======= Sadece sesli prompt =======
# Yazılı giriş KAPALI, sadece mikrofondan alınacak
if 'mic_text' in locals() and mic_text:
    prompt = mic_text
else:
    prompt = None

# ======= Resim ve prompt alınırsa modele gönder =======
yanit = None
if capture_btn:
    try:
        img = Image.open(capture_btn)
        # Bilgilendirme: fotoğraf çekildi
        info_area.info("🟢 Fotoğraf alındı, modele gönderiliyor...")
        # Mikrofondan prompt yoksa varsayılan
        prompt_text = st.session_state.get("component_value") or "Bu resimde neler var?"
        yanit = model.generate_content([img, prompt_text]).text
        info_area.success("✅ Yanıt alındı, seslendiriliyor...")
        # Gemini yanıtını ekrana yaz
        st.markdown(
            f"<div style='font-size:1.2em;line-height:1.5;' aria-live='polite'>{yanit}</div>",
            unsafe_allow_html=True
        )
        # Gemini yanıtını otomatik seslendir (JS)
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

# ======= Sonrası için bilgi mesajı =======
st.info("🔵 Mikrofondan konuş, büyük butonla fotoğraf çek, yanıtı otomatik dinle. "
        "Yazılı giriş yok. En iyi deneyim için ekran okuyucu ile kullanabilirsin.")

# Ek erişilebilirlik için: tuşlarla gezilebilir büyük butonlar
st.markdown("""
<style>
.big-button:focus {
    outline: 3px solid #FFD700;
}
</style>
""", unsafe_allow_html=True)
