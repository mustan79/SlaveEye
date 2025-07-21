import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from PIL import Image

# CSS: Butonları büyüt ve kamera inputunu gizle
st.markdown("""
<style>
    .big-btn {width:96vw; height:8vh; font-size:3em; margin:1vh 0;}
    [data-testid="stCameraInput"] {display: none !important;}
</style>
""", unsafe_allow_html=True)

st.title("🔊 Akıllı Sesli Asistan")

load_dotenv()
google_api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
if not google_api_key:
    st.error("Google API Key bulunamadı. Lütfen .env dosyanızı kontrol edin.")
    st.stop()

genai.configure(api_key=google_api_key)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

info_area = st.empty()

if "cekilen_resim" not in st.session_state:
    st.session_state["cekilen_resim"] = None
if "mic_prompt" not in st.session_state:
    st.session_state["mic_prompt"] = None

# --- FOTOĞRAF ÇEKME MEKANİĞİ ---
col1, col2 = st.columns(2)
with col1:
    foto_btn = st.button("📷 Resim Çek", key="btn_foto", use_container_width=True)
with col2:
    mic_btn = st.button("🎤 Mikrofonla Sor", key="btn_mic", use_container_width=True)

# --- KAMERA INPUTU (her zaman hazır) ---
camera_file = st.camera_input("", key="cam_input", label_visibility="collapsed")

# FOTOĞRAF ÇEK BUTONUNA BASILINCA: Kamera inputunu tetikle (el ile veya JS ile)
if foto_btn:
    info_area.info("Kamera açılıyor, fotoğraf çek ve yükle...")
    st.stop()  # Tekrar yüklemede kamera_input açılır

if camera_file and (foto_btn or st.session_state.get("mic_waiting_photo")):
    try:
        img = Image.open(camera_file)
        st.session_state["cekilen_resim"] = img
        prompt = st.session_state["mic_prompt"] or "Bu resimde neler var?"
        info_area.info("🟢 Modelden yanıt bekleniyor...")
        yanit = model.generate_content([img, prompt]).text
        info_area.success("✅ Yanıt seslendiriliyor...")
        speak_html = f"""
        <script>
        var msg = new SpeechSynthesisUtterance({yanit!r});
        msg.lang = 'tr-TR'; window.speechSynthesis.speak(msg);
        </script>"""
        st.components.v1.html(speak_html, height=0)
        st.session_state["mic_prompt"] = None
        st.session_state["mic_waiting_photo"] = False
    except Exception as e:
        info_area.error(f"Hata: {e}")

# --- MİKROFON İLE PROMPT ALMA ---
if mic_btn:
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
    mic_text = st.components.v1.html(mic_html, height=230)
    val = st.session_state.get("component_value")
    if val:
        st.session_state["mic_prompt"] = val
        st.session_state["mic_listen"] = False
        st.session_state["mic_waiting_photo"] = True
        info_area.info("Şimdi otomatik kamera ile fotoğraf çekip yükleyin!")
        st.stop()

st.info("""
- 📷 **Resim Çek:** Kameradan fotoğraf çek, model yanıtını otomatik seslendirir.
- 🎤 **Mikrofonla Sor:** Konuş, ardından fotoğraf çekmeni ister, ikisini birlikte modele yollar ve yanıtı seslendirir.
- Görsel veya kamera önizlemesi gösterilmez.
""")
