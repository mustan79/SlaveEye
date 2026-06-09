import streamlit as st
from ollama import Client
import os
from dotenv import load_dotenv
from PIL import Image
import io
import base64

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="Sesli Asistan",
    page_icon="🤖",
    layout="centered"
)

# Çevresel değişkenleri yükle
load_dotenv()
ollama_api_key = st.secrets.get("OLLAMA_API_KEY") or os.getenv("OLLAMA_API_KEY")
if not ollama_api_key:
    st.error("Ollama API Key bulunamadı.")
    st.stop()

client = Client(
    host="https://ollama.com",
    headers={"Authorization": f"Bearer {ollama_api_key}"}
)

def speak(text):
    """Metni sesli okuma tetikleyicisi"""
    speak_html = f"""
    <script>
    var msg = new SpeechSynthesisUtterance({text!r});
    msg.lang = 'tr-TR';
    msg.rate = 1.0;
    window.speechSynthesis.speak(msg);
    </script>"""
    st.components.v1.html(speak_html, height=0)

# Değişkenleri session state üzerinde tutuyoruz
if "mic_text" not in st.session_state:
    st.session_state["mic_text"] = ""
if "auto_trigger" not in st.session_state:
    st.session_state["auto_trigger"] = False

# --- ERİŞİLEBİLİRLİK VE TASARIM CSS AYARLARI ---
st.markdown("""
<style>
/* Arka planı koyulaştırıp butonları öne çıkarma */
.main {
    background-color: #f5f7fb;
}

/* Devasa, erişilebilir buton tasarımları */
.custom-btn {
    border: none;
    color: white;
    padding: 30px 20px;
    font-size: 24px;
    font-weight: bold;
    border-radius: 20px;
    cursor: pointer;
    width: 100%;
    margin-bottom: 20px;
    text-align: center;
    display: block;
    box-shadow: 0 8px 20px rgba(0,0,0,0.15);
    transition: all 0.2s ease;
}

.btn-camera {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
}

.btn-mic {
    background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%);
}

.custom-btn:active {
    transform: scale(0.96);
}

/* KAMERAYI EN ALTTA KÜÇÜCÜK TUTMA VE ERİŞİLMEZ YAPMA HİLESİ */
/* Görsel olarak alt köşede çok az yer kaplayacak ama JS tarafından tıklanabilecek */
div[data-testid="stCameraInput"] {
    position: fixed;
    bottom: 5px;
    right: 5px;
    width: 140px !important;
    height: 100px !important;
    z-index: 9999;
    opacity: 0.4;
    transform: scale(0.7);
}
div[data-testid="stCameraInput"] label {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🤖 Gözsüz Akıllı Asistan")

# --- JAVASCRIPT KÖPRÜSÜ (MİKROFON VE OTOMASYON) ---
# Hem mikrofonu yönetir hem de ses bitince aşağıdaki gizli kameranın deklanşörüne basar.
master_js_html = """
<div style="width: 100%;">
  <button class="custom-btn btn-mic" id="mic-btn" onclick="runMicWorkflow()">🎤 MİKROFONU AÇ (KONUŞ)</button>
  <button class="custom-btn btn-camera" id="cam-btn" onclick="clickHiddenCamera()">📸 SADECE RESİM ÇEK</button>
  <p id="status-text" style="text-align: center; color: #555; font-size: 16px; font-weight: bold; margin-top: 10px;">Durum: Hazır</p>
</div>

<script>
function clickHiddenCamera() {
    const status = document.getElementById('status-text');
    status.innerText = "Kamera Tetikleniyor...";
    
    // Streamlit'in kamera butonunu bulup tıklatıyoruz
    setTimeout(() => {
        const camBtn = window.parent.document.querySelector('div[data-testid="stCameraInput"] button');
        if (camBtn) {
            camBtn.click();
        } else {
            status.innerText = "Hata: Kamera butonu bulunamadı!";
        }
    }, 500);
}

function runMicWorkflow() {
  const micBtn = document.getElementById('mic-btn');
  const status = document.getElementById('status-text');
  
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
    status.innerText = "Tarayıcıda mikrofon desteği yok!";
    return;
  }
  
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = new SpeechRecognition();
  
  recognition.lang = "tr-TR";
  recognition.continuous = false;
  recognition.interimResults = false;

  recognition.onstart = function() {
    micBtn.style.background = "linear-gradient(135deg, #f857a6 0%, #ff5858 100%)";
    micBtn.innerText = "🔊 DİNLENİYOR...";
    status.innerText = "Konuşun, bitince otomatik fotoğraf çekilecek...";
  };

  recognition.onresult = function(event) {
    const text = event.results[0][0].transcript;
    status.innerText = "Söylenen: " + text;
    
    // 1. Adım: Metni Streamlit text_input alanına yaz ve eşitle
    const inputs = window.parent.document.querySelectorAll('input[type="text"]');
    if(inputs.length > 0) {
        inputs[0].value = text;
        inputs[0].dispatchEvent(new Event('input', { bubbles: true }));
    }
    
    // 2. Adım: Zincirleme Reaksiyon - Otomatik olarak kamerayı tetikle
    status.innerText = "Ses alındı! Resim otomatik çekiliyor...";
    setTimeout(() => {
        clickHiddenCamera();
    }, 800);
  };

  recognition.onerror = function(event) {
    status.innerText = "Hata: " + event.error;
    resetUi();
  };

  recognition.onend = function() {
    resetUi();
  };

  function resetUi() {
    micBtn.style.background = "linear-gradient(135deg, #00c6ff 0%, #0072ff 100%)";
    micBtn.innerText = "🎤 MİKROFONU AÇ (KONUŞ)";
  }

  recognition.start();
}
</script>
"""

# HTML Buton bloğunu en üste gömüyoruz
st.components.v1.html(master_js_html, height=240)

# Mikrofondan gelen veriyi yakalayan ara görünmez kutu (Sadece veri aktarımı için)
text_input_val = st.text_input("Gelen Komut:", key="hidden_voice_input", label_visibility="collapsed")

if text_input_val:
    st.session_state["mic_text"] = text_input_val

# Mikrofon senaryosunda ekrana söylenen cümleyi yazdırma kuralı
if st.session_state["mic_text"]:
    st.info(f"🎤 Algılanan Sorunuz: **{st.session_state['mic_text']}**")

# Arka planda duran (küçültülmüş) Streamlit kamera bileşeni
camera_photo = st.camera_input("Kamera", key="hidden_camera")

# --- LLM VE ANALİZ SÜRECİ ---
if camera_photo:
    # 1. mi yoksa 2. senaryo mu aktif kontrol et
    if st.session_state["mic_text"].strip() != "":
        # 2. Senaryo: Kullanıcının kendi cümlesi
        prompt = st.session_state["mic_text"]
    else:
        # 1. Senaryo: Sadece resim çekildi, sabit prompt devrede
        prompt = "Bu resimde ne görüyorsun? Detaylıca Türkçe açıkla."
        
    with st.spinner("Asistan düşünüyor..."):
        try:
            # Resmi base64 formatına çevir
            image = Image.open(camera_photo)
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
            # Ollama Cloud API Çağrısı
            response = client.generate(
                model="gemma4:31b-cloud",
                prompt=prompt,
                images=[img_base64]
            )
            
            response_text = response.response
            
            # SADECE SESLİ YANIT (İstediğin gibi metin çıktısı vermiyor, direkt konuşuyor)
            speak(response_text)
            
        except Exception as e:
            speak("Özür dilerim, bağlantı sırasında bir hata oluştu.")
            
    # Zincirleme akış bittiği için hafızayı temizle (Arayüzü sıfırla)
    st.session_state["mic_text"] = ""


