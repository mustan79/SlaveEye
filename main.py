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
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# Global değişkenler
son_cekilen_resim = None

# 🤖 Gemini modeline soru sor ve cevap al
def gemini_cevapla(input_text, image=None):
    try:
        contents = []
        if image:
            st.info("Görüntü ve metin Gemini’ye gönderiliyor...")
            contents.append(image)
            contents.append(input_text)
            st.success("Görüntü ve metin başarıyla gönderildi.")
        else:
            st.info("Sadece metin Gemini’ye gönderiliyor...")
            contents.append(input_text)

        response = model.generate_content(contents)
        yanit = response.text
        return yanit
    except Exception as e:
        st.error(f"Gemini API hatası: {e}")
        return None

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

# ======= UI =======
# Kamera seçimi (Mobil için)
kamera_secimi = st.radio("Kamera Seçimi:", ("Arka Kamera", "Ön Kamera"))

# Resim çekme butonu
captured_image = st.camera_input("2. Resim Çek",key="kalici_resim")
if captured_image:
    son_cekilen_resim = Image.open(captured_image)
    st.image(captured_image, caption="Çekilen Resim", use_column_width=True)
    prompt = "Bu resimde neler görüyorsun anlat."
    yanit = gemini_cevapla(prompt, son_cekilen_resim)
    if yanit:
        st.text_area("Gemini Yanıtı", yanit, key="yanit_1", height=150, help="Aşağıdan yanıtı sesli dinleyebilirsiniz.")
        # Yanıtı sesli okutma butonu
        speak_html = f"""
        <button class="big-button" onclick="window.speechSynthesis.speak(new SpeechSynthesisUtterance('{yanit.replace("'", "").replace("\\n", " ")}'));">
        🔊 Yanıtı Sesli Oku
        </button>
        """
        st.components.v1.html(speak_html, height=80)

# Yazılı giriş
st.markdown("### 3. Yazılı Prompt:")
col1, col2 = st.columns([2,1])
with col1:
    kullanici_girdisi = st.text_input(
        "Prompt:",
        placeholder="Buraya yazın ya da yukarıdan mikrofonla konuşun...",
        key="kullanici_girdisi"
    )
with col2:
    st.markdown("Mikrofondan aldığınız metin otomatik buraya gelir.")

gonder = st.button("Gönder ✉️", key="gonder_btn")
if gonder and kullanici_girdisi:
    if son_cekilen_resim:
        yanit = gemini_cevapla(kullanici_girdisi, son_cekilen_resim)
    else:
        yanit = gemini_cevapla(kullanici_girdisi)
    if yanit:
        st.text_area("Gemini Yanıtı", yanit, key="yanit_2", height=150)
        # Yanıtı sesli okutma butonu
        speak_html = f"""
        <button class="big-button" onclick="window.speechSynthesis.speak(new SpeechSynthesisUtterance('{yanit.replace("'", "").replace("\\n", " ")}'));">
        🔊 Yanıtı Sesli Oku
        </button>
        """
        st.components.v1.html(speak_html, height=80)
elif gonder:
    st.warning("Lütfen bir şeyler yazın.")

# Kullanıcıya bilgi notu
st.info(
    "🗣️ Mikrofondan konuşmak için yukarıdaki butonu kullan. "
    "Cevabı sesli dinlemek için 'Yanıtı Sesli Oku'ya tıkla. "
    "Sunucu tarafında değil, tamamen tarayıcıda çalışır."
)
