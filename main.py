import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from PIL import Image

st.set_page_config(page_title="Akıllı Sesli Asistan", layout="wide")

# --- CSS: Butonları büyüt, kamera inputunu gizle ---
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
if "mic_waiting_photo" not in st.session_state:
    st.session_state["mic_waiting_photo"] = False
if "mic_listen" not in st.session_state:
    st.session_state["mic_listen"] = False

# --- SADE EKRAN: 2 BUTON ---
col1, col2 = st.columns(2)
with col1:
    foto_btn = st.button("📷 Resim Çek", key="btn_foto", use_container_width=True)
with col2:
    mic_btn = st.button("🎤 Mikrofon", key="btn_mic", use_container_width=True)

# --- KAMERA INPUTU (gizli) ---
camera_file = st.camera_input("", key="cam_input", label_visibility="collapsed")

# --- 1. MOD: SADECE RESİM ÇEK ---
if foto_btn:
    info_area.info("Kamera açılıyor... Bir fotoğraf çekin.")
    # Bilgilendirmeyi seslendir
    st.components.v1.html("""
    <script>
    var msg = new SpeechSynthesisUtterance("Kamera açılıyor, lütfen bir fotoğraf çekin.");
    msg.lang = 'tr-TR'; window.speechSynthesis.speak(msg);
    </script>
    """, height=0)
    st.stop()  # Yeniden yüklemede camera_input açılır

if camera_file and not st.session_state.get("mic_waiting_photo"):
    try:
        img = Image.open(camera_file)
        prompt = "Bu resimde neler görüyorsun?"
        info_area.info("🟢 Modelden yanıt bekleniyor...")
        yanit = model.generate_content([img, prompt]).text
        info_area.success("✅ Yanıt seslendiriliyor...")
        st.components.v1.html(f"""
        <script>
        var msg = new SpeechSynthesisUtterance({yanit!r});
        msg.lang = 'tr-TR'; window.speechSynthesis.speak(msg);
        </script>
        """, height=0)
    except Exception as e:
        info_area.error(f"Hata: {e}")
        st.components.v1.html(f"""
        <script>
        var msg = new SpeechSynthesisUtterance("Hata oluştu: {str(e)}");
        msg.lang = 'tr-TR'; window.speechSynthesis.speak(msg);
        </script>
        """, height=0)

# --- 2. MOD: MİKROFON İLE PROMPT AL, SONRA FOTOĞRAF ÇEK ---
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
        info_area.info("Şimdi fotoğraf çekin lütfen!")
        st.components.v1.html("""
        <script>
        var msg = new SpeechSynthesisUtterance("Şimdi fotoğraf çekin lütfen!");
        msg.lang = 'tr-TR'; window.speechSynthesis.speak(msg);
        </script>
        """, height=0)
        st.stop()

if camera_file and st.session_state.get("mic_waiting_photo"):
    try:
        img = Image.open(camera_file)
        prompt = st.session_state["mic_prompt"] or "Bu resimde neler var?"
        yanit = model.generate_content([img, prompt]).text
        info_area.success("✅ Yanıt seslendiriliyor...")
        st.components.v1.html(f"""
        <script>
        var msg = new SpeechSynthesisUtterance({yanit!r});
        msg.lang = 'tr-TR'; window.speechSynthesis.speak(msg);
        </script>
        """, height=0)
        st.session_state["mic_prompt"] = None
        st.session_state["mic_waiting_photo"] = False
    except Exception as e:
        info_area.error(f"Hata: {e}")
        st.components.v1.html(f"""
        <script>
        var msg = new SpeechSynthesisUtterance("Hata oluştu: {str(e)}");
        msg.lang = 'tr-TR'; window.speechSynthesis.speak(msg);
        </script>
        """, height=0)
        st.session_state["mic_prompt"] = None
        st.session_state["mic_waiting_photo"] = False

st.info("""
**Kullanım:**
- 📷 Resim Çek: Sadece fotoğraf çekip, modelden yanıtı sesli alırsınız.
- 🎤 Mikrofon: Önce konuşarak prompt girersiniz, hemen ardından fotoğraf çekersiniz. İkisi birlikte modele gider, yanıt sesli döner.
- Kamera ve fotoğraf hiçbir zaman ekranda gösterilmez.
""")

