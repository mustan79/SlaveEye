import streamlit as st
from ollama import Client  # Ollama SDK import edildi
import os
from dotenv import load_dotenv
from PIL import Image
import base64
import io

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="Akıllı Asistan (Ollama Cloud)",
    page_icon="🤖",
    layout="centered"
)

# CSS yükle
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("🤖 Akıllı Asistan (Ollama)")

# Çevresel değişkenleri yükle
load_dotenv()
ollama_api_key = st.secrets.get("OLLAMA_API_KEY") or os.getenv("OLLAMA_API_KEY")
if not ollama_api_key:
    st.error("Ollama API Key bulunamadı. Lütfen .env veya Streamlit Secrets kontrol edin.")
    st.stop()

# Ollama Bulut İstemci (Client) Yapılandırması
client = Client(
    host="https://ollama.com",  # Sizin belirttiğiniz bulut adresi
    headers={"Authorization": f"Bearer {ollama_api_key}"}
)

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
<div style="text-align: center; margin: 30px;">
  <button class="big-button" id="start-record" onclick="startMic()">🎤 Mikrofon</button>
  <div id="mic-result" style="font-weight: bold; font-size: 4em; margin-top: 30px; color: #333;"></div>
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
mic_result = st.components.v1.html(mic_html, height=250)

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
  padding: 30px 50px;
  font-size: 24px;
  border-radius: 15px;
  cursor: pointer;
  transition: all 0.3s ease;
  margin: 10px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}

.big-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(0,0,0,0.3);
}

.button-container {
  display: flex;
  justify-content: center;
  gap: 30px;
  margin: 30px 0;
}

.camera-container {
  text-align: center;
  margin: 30px 0;
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
            prompt = st.session_state["mic_text"]
            speak("Modelden yanıt bekleniyor...")
        else:
            prompt = "Bu resimde gördüklerini detaylı olarak anlat."
            speak("Modelden yanıt bekleniyor...")
        
        # Resmi aç ve Ollama için hazırla
        image = Image.open(st.session_state["captured_image"])
        
        # PIL Image nesnesini Base64 stringine dönüştürme işlemi
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        try:
            # Ollama API çağrısı
            response = client.generate(
                model="gemma4:31b-cloud",
                prompt=prompt,
                images=[img_base64]  # Resim base64 listesi olarak gönderildi
            )
            response_text = response['response']
            
            # Yanıtı ekrana yazdır ve seslendir
            st.write(response_text)
            speak(response_text)
            
        except Exception as e:
            st.error(f"Ollama API hatası oluştu: {e}")
        
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


