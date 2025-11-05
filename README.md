# 🤖 Akıllı Asistan - Streamlit Uygulaması

Bu uygulama, Google Gemini AI ile entegre edilmiş sesli etkileşimli bir asistan uygulamasıdır.

## ✨ Özellikler

- 📸 **Kamera Entegrasyonu**: Arkaplanda kamera ile fotoğraf çekme
- 🎤 **Sesli Etkileşim**: Mikrofon ile ses girişi ve sesli yanıt
- 🤖 **AI Analizi**: Gemini-2.5-flash ile resim analizi
- 🔊 **Sesli Geri Bildirim**: Tüm yanıtların sesli okunması
- 📱 **Mobil Uyumlu**: Tüm cihazlarda çalışır

## 🚀 Kurulum ve Çalıştırma

### 1. Gerekli Paketleri Yükleyin
```bash
pip install -r requirements.txt
```

### 2. API Anahtarını Ayarlayın
- `.env.example` dosyasını `.env` olarak kopyalayın
- Google AI Studio'dan API anahtarınızı alın: https://aistudio.google.com/
- `.env` dosyasında `GEMINI_API_KEY` değerini güncelleyin

### 3. Uygulamayı Çalıştırın
```bash
streamlit run app.py
```

## 📱 Kullanım

### Resim Çekme Modu:
1. "📸 Resim Çek" butonuna tıklayın
2. Kamera açılacak (arka planda çalışacak)
3. Fotoğraf çekin
4. AI fotoğrafı analiz edecek ve sesli yanıt verecek

### Mikrofon Modu:
1. "🎤 Mikrofon" butonuna tıklayın
2. İsteğinizi sesli olarak söyleyin
3. Sistem otomatik olarak fotoğraf çekecek
4. İsteğinizle birlikte fotoğraf AI'ya gönderilecek
5. AI yanıtını sesli olarak duyabileceksiniz

## 🛠️ Teknik Detaylar

- **Frontend**: Streamlit
- **AI Model**: Google Gemini-2.5-flash
- **Kamera**: Streamlit camera_input
- **Mikrofon**: Web Speech API (webkitSpeechRecognition)
- **Ses**: Speech Synthesis API
- **Resim İşleme**: PIL (Python Imaging Library)

## 🔧 Geliştirici Notları

### Session State Kullanımı:
- `st.session_state["captured_image"]`: Çekilen fotoğraf
- `st.session_state["mic_text"]`: Mikrofondan alınan metin

### Ana Fonksiyonlar:
- `speak(text)`: Metni sesli olarak okuma
- Mikrofon entegrasyonu: JavaScript ile web tarayıcısı mikrofon API'si
- Kamera entegrasyonu: Streamlit'in built-in kamera bileşeni

## 📋 Gereksinimler

- Python 3.8+
- Modern web tarayıcısı (Chrome, Firefox, Safari)
- İnternet bağlantısı
- Google Gemini API anahtarı

## 🐛 Sorun Giderme

### Mikrofon Çalışmıyor:
- Tarayıcının mikrofon izinlerini kontrol edin
- HTTPS kullanıldığından emin olun
- Farklı tarayıcı deneyin

### Kamera Çalışmıyor:
- Tarayıcının kamera izinlerini kontrol edin
- Kamera uygulaması başka bir uygulama tarafından kullanılmıyor olmalı

### API Hatası:
- API anahtarının doğru olduğunu kontrol edin
- API kota limitinizi kontrol edin
- İnternet bağlantınızı kontrol edin

## 📄 Lisans

MIT Lisansı altında dağıtılmaktadır.