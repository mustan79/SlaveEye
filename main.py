import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import os
import speech_recognition as sr
from dotenv import load_dotenv
import time
import cv2
from PIL import Image

# Çevresel değişkenleri yükle
load_dotenv()
google_api_key = os.getenv("GEMINI_API_KEY")
if not google_api_key:
    st.error("Google API Key bulunamadı. Lütfen .env dosyanızı kontrol edin.")
    st.stop()

# Gemini API yapılandırması
genai.configure(api_key=google_api_key)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# 🎤 **Mikrofondan ses al ve metne çevir**
def ses_kayit(device_index=0):
    r = sr.Recognizer()
    with sr.Microphone(device_index=device_index) as source:
        st.info("Konuşabilirsiniz...")
        r.adjust_for_ambient_noise(source)  # Ortam gürültüsünü ayarlar
        audio = r.listen(source, timeout=5)  # Maksimum 5 saniye dinler

    try:
        text = r.recognize_google(audio, language='tr-TR')
        st.success(f"Algılanan metin: {text}")
        return text
    except sr.UnknownValueError:
        st.error("Ses anlaşılamadı, lütfen tekrar deneyin.")
        return None
    except sr.RequestError:
        st.error("Ses tanıma hizmetine ulaşılamadı.")
        return None

# 🔊 **Metni seslendir**
def seslendir(text):
    try:
        tts = gTTS(text=text, lang="tr", slow=False)
        file_path = "yanit.mp3"
        tts.save(file_path)

        # Streamlit ile mp3 dosyasını oynat
        with open(file_path, "rb") as audio_file:
            st.audio(audio_file.read(), format="audio/mp3")

        os.remove(file_path)

    except Exception as e:
        st.error(f"Seslendirme hatası: {e}")

# 📷 **Kameradan görüntü yakala ve uyarı ver**
def capture_image(camera_index=0):
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        st.error(f"Kamera {camera_index} açılamadı.")
        seslendir(f"Kamera {camera_index} açılamadı.")
        cap.release()
        return None
    
    ret, frame = cap.read()
    if ret:
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        cap.release()
        st.success("Resim yakalandı!")
        seslendir("Resim yakalandı!")
        return image
    cap.release()
    st.error("Görüntü yakalanamadı.")
    seslendir("Görüntü yakalanamadı.")
    return None

# 🤖 **Gemini modeline soru sor ve cevap al**
def gemini_cevapla(input_text, image=None):
    try:
        if image:
            st.info("Görüntü ve metin Gemini’ye gönderiliyor...")
            response = model.generate_content([input_text, image])
            st.success("Görüntü ve metin başarıyla gönderildi.")
        else:
            st.info("Sadece metin Gemini’ye gönderiliyor...")
            response = model.generate_content(input_text)
        yanit = response.text
        st.text_area("Gemini Yanıtı", yanit)
        seslendir(yanit)
        return yanit
    except Exception as e:
        st.error(f"Gemini API hatası: {e}")
        seslendir(f"Gemini API hatası: {e}")
        return None

# 📌 **Streamlit UI**
st.title("🎙️ Sesli ve Görüntülü Chatbot")

# Sidebar ile cihaz seçimi
with st.sidebar:
    camera_options = [f"Kamera {i}" for i in range(3)]  # Basit bir liste
    selected_camera = st.selectbox("Kamera Seç", camera_options, index=0)
    camera_index = int(selected_camera.split()[1])

    mic_options = [f"Mikrofon {i}" for i in range(3)]  # Basit bir liste
    selected_mic = st.selectbox("Mikrofon Seç", mic_options, index=0)
    mic_index = int(selected_mic.split()[1])

# Butonlar ve UI
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("📷 Görüntü Yakala"):
        image = capture_image(camera_index)
        if image:
            st.session_state['captured_image'] = image
            st.image(image, caption="Yakalanan Görüntü")

with col2:
    if st.button("🎙️ Mikrofonla Konuş"):
        ses_metni = ses_kayit(mic_index)
        if ses_metni:
            st.session_state['prompt'] = ses_metni
            if 'captured_image' in st.session_state:
                gemini_cevapla(ses_metni, st.session_state['captured_image'])
            else:
                gemini_cevapla(ses_metni)

with col3:
    if st.button("✉️ Gönder"):
        if 'prompt' in st.session_state and st.session_state['prompt'].strip():
            if 'captured_image' in st.session_state:
                gemini_cevapla(st.session_state['prompt'], st.session_state['captured_image'])
            else:
                gemini_cevapla(st.session_state['prompt'])

# Yazılı giriş kutusu
kullanici_girdisi = st.text_input("Sorunuzu yazın:", placeholder="Buraya yazabilirsiniz...")
if kullanici_girdisi.strip():
    st.session_state['prompt'] = kullanici_girdisi

if 'captured_image' in st.session_state:
    st.image(st.session_state['captured_image'], caption="Yakalanan Görüntü")
