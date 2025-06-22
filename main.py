import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import os
from dotenv import load_dotenv
from PIL import Image
import io

# Çevresel değişkenleri yükle
load_dotenv()
google_api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
if not google_api_key:
    st.error("Google API Key bulunamadı. Lütfen .env dosyanızı kontrol edin.")
    st.stop()

# Gemini API yapılandırması
genai.configure(api_key=google_api_key)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

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

st.markdown("""
- Kameradan fotoğraf çekmek için aşağıdaki butonu kullan.
- Dilersen ses dosyası da yükleyebilirsin (opsiyonel).
""")

# Kamera inputu
captured_image = st.camera_input("Kameradan Fotoğraf Çek (tarayıcınızdan izin vermelisiniz)")

# Ses dosyası yükleme (isteğe bağlı)
uploaded_audio = st.file_uploader("Bir ses dosyası yükleyin (opsiyonel, .wav/.mp3)", type=["wav", "mp3"])

# Yazılı giriş kutusu
kullanici_girdisi = st.text_input("Sorunuzu yazın:", placeholder="Buraya yazabilirsiniz...")

# Butonlar ve UI
col1, col2 = st.columns(2)

with col1:
    if st.button("✉️ Gönder"):
        if kullanici_girdisi.strip():
            img = None
            if captured_image is not None:
                # Streamlit image objesini PIL Image objesine çevir
                img = Image.open(captured_image)
            yanit = gemini_cevapla(kullanici_girdisi, img)
        else:
            st.warning("Lütfen bir soru/metin girin.")

with col2:
    if uploaded_audio is not None:
        st.audio(uploaded_audio, format="audio/wav")
        st.info("Ses dosyası başarıyla yüklendi. (Otomatik çözümleme için ek kod eklenebilir.)")

# Yakalanan fotoğrafı göster
if captured_image is not None:
    st.image(captured_image, caption="Yakalanan Görüntü")

