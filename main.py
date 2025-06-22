import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import os
from dotenv import load_dotenv
from PIL import Image
import io
import base64  # Resimleri base64'e çevirmek için

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
son_cekilen_resim = None  # Son çekilen resmi saklamak için

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
        st.text_area("Gemini Yanıtı", yanit)
        seslendir(yanit)
        return yanit
    except Exception as e:
        st.error(f"Gemini API hatası: {e}")
        seslendir(f"Gemini API hatası: {e}")
        return None

# 📌 **Streamlit UI**
st.title("📸 Akıllı Asistan")

# Kamera seçimi (Mobil için)
kamera_secimi = st.radio("Kamera Seçimi:", ("Arka Kamera", "Ön Kamera"))

# Resim çekme butonu
captured_image = st.camera_input("2. Resim Çek",key="kalici_resim")
if captured_image:
    son_cekilen_resim = Image.open(captured_image) # PIL Image objesine çevir
#    st.image(captured_image, caption="Çekilen Resim", use_column_width=True)

   # Resmi Gemini'ye gönder
    prompt = "Bu resimde neler görüyorsun anlat."
    gemini_cevapla(prompt, son_cekilen_resim)

# Yazılı giriş
kullanici_girdisi = st.text_input("3. Yazılı Prompt:", placeholder="Buraya yazın...")
if st.button("Gönder ✉️"):
    if kullanici_girdisi:
        # Eğer son çekilen resim varsa, resimle beraber gönder
        if son_cekilen_resim:
            gemini_cevapla(kullanici_girdisi, son_cekilen_resim)
        else:
            gemini_cevapla(kullanici_girdisi)
    else:
        st.warning("Lütfen bir şeyler yazın.")
