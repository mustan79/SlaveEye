import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from PIL import Image
import base64

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="Akıllı Asistan",
    page_icon="🤖",
    layout="centered"
)

# CSS yükle
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("🤖 Akıllı Asistan")

# Çevresel değişkenleri yükle
load_dotenv()
google_api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
if not google_api_key:
    st.error("Google API Key bulunamadı. Lütfen .env dosyanızı kontrol edin.")
    st.stop()

# Gemini API yapılandırması
genai.configure(api_key=google_api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

# Sesli yanıt fonksiyonu
def speak(text):
    """Metni sesli olarak okuma"""
    speak_html = f"""
    <script>
    var msg = new SpeechSynthesisUtterance({text!r});
    msg.lang = 'tr-TR';
    msg.rate = 1.0;
    window.speechSynthesis.speak(msg);
    </script>"""
    st.components.v1.html(speak_html, height=0)

# Session state başlatma
if "captured_image" not in st.session_state:
    st.session_state["captured_image"] = None
if "mic_text" not in st.session_state:
    st.session_state["mic_text"] = ""

# Mikrofon HTML komponenti
mic_html = """
<div style="text-align: center; margin: 20px;">
  <button class="big-button" id="start-record" onclick="startMic()">🎤 Mikrofon</button>
  <div id="mic-result" style="font-weight: bold; font-size: 1.2em; margin-top: 10px; color: #333;"></div>
</div>
<script>
function startMic() {
  const btn = document.getElementById('start-record');
  const result = document.getElementById('mic-result');
  
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    result.innerText = "Tarayıcı mikrofon desteği yok!";
    return;
  }
  
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = new SpeechRecognition();
  
  recognition.lang = "tr-TR";
  recognition.continuous = false;
  recognition.interimResults = false;

  recognition.onstart = function() {
    btn.innerText = "🔊 Dinleniyor...";
    result.innerText = "Mikrofon aktif...";
  };

  recognition.onresult = function(event) {
    const text = event.results[0][0].transcript;
    result.innerText = "Anladığım: " + text;
    
    // Streamlit'e metni gönder
    window.parent.postMessage({
      type: "streamlit:setComponentValue",
      data: text
    }, "*");
    
    btn.innerText = "🎤 Mikrofon";
  };

  recognition.onerror = function(event) {
    result.innerText = "Hata: " + event.error;
    btn.innerText = "🎤 Mikrofon";
  };

  recognition.onend = function() {
    btn.innerText = "🎤 Mikrofon";
  };

  recognition.start();
}
</script>
"""

# Mikrofon bileşeni
mic_result = st.components.v1.html(mic_html, height=150)

# Mikrofon verisini session state'e kaydet
if isinstance(mic_result, str) and mic_result.strip():
    st.session_state["mic_text"] = mic_result

# Butonlar için CSS
st.markdown("""
<style>
.big-button {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
  padding: 20px 40px;
  font-size: 24px;
  border-radius: 15px;
  cursor: pointer;
  transition: all 0.3s ease;
  margin: 10px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}

.big-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0,0,0,0.3);
}

.button-container {
  display: flex;
  justify-content: center;
  gap: 30px;
  margin: 30px 0;
}

.camera-container {
  text-align: center;
  margin: 20px 0;
}
</style>
""", unsafe_allow_html=True)

# Ana butonlar
col1, col2 = st.columns([1, 1])

with col1:
    # Resim çek butonu
    camera_photo = st.camera_input(
        "📸 Resim Çek",
        key="photo_capture",
        help="Bu butona bastığınızda kamera aktif olacak ve arkaplanda çalışacak"
    )
    
    if camera_photo:
        st.session_state["captured_image"] = camera_photo
        if st.session_state["mic_text"]:
            # Mikrofon girişi varsa onu kullan
            prompt = st.session_state["mic_text"]
            speak("Modelden yanıt bekleniyor...")
        else:
            # Sabit prompt
            prompt = "Bu resimde gördüklerini detaylı olarak anlat."
            speak("Modelden yanıt bekleniyor...")
        
        # Resmi AI'ya gönder
        image = Image.open(st.session_state["captured_image"])
        response = model.generate_content([image, prompt])
        response_text = response.text
        
        # Yanıtı seslendir
        speak(response_text)
        
        # Temizle
        st.session_state["mic_text"] = ""

with col2:
    # Mikrofon kullanım talimatları
    st.markdown("### 🎤 Mikrofon Kullanımı:")
    st.markdown("1. Mikrofon butonuna basın")
    st.markdown("2. Ne istediğinizi söyleyin")
    st.markdown("3. Kamera otomatik fotoğraf çekecek")
    st.markdown("4. İsteğinizle ilgili yanıt gelecek")
    
    if st.session_state["mic_text"]:
        st.success(f"Son mikrofon girişi: **{st.session_state['mic_text']}**")

# Bilgi alanı
st.markdown("---")
st.markdown("💡 **İpuçları:**")
st.markdown("- Resim çek butonuna bastığınızda kamera açılacak")
st.markdown("- Mikrofon kullanmak için önce mikrofon butonuna basın")
st.markdown("- Tüm yanıtlar sesli olarak okunacak")