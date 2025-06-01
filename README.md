# 🧠 DATA SAGE  
### AI Destekli Metin Tabanlı SQL Sorgulama ve Anlık Veri Analizi Platformu

---

## 🎯 Proje Amacı

Data Sage, SQL bilgisi olmayan kullanıcıların bile veritabanı sorguları yapabilmesini sağlamak amacıyla geliştirilmiş bir yapay zekâ destekli analiz platformudur. Doğal dilde yazılan ifadeler OpenAI GPT-3.5/4 API ile anlamlı SQL sorgularına dönüştürülür ve sonuçlar grafiklerle görselleştirilerek kullanıcıya sunulur.

---

## 📌 Proje Hedefleri

- Doğal dil ifadelerini anlamlı SQL sorgularına çevirmek  
- Kullanıcıya tablo ve grafik formatında anlaşılır sonuçlar sunmak  
- SQL bilmeyen kullanıcıları da veri analiz süreçlerine dahil etmek  
- RESTful API yapısı sayesinde diğer sistemlerle entegre çalışmak  
- Açık kaynak topluluğu ile global katkıya açık bir sistem geliştirmek  

---

## 👥 Takım Üyeleri ve Yetkinlikleri

| İsim                   | Rol                         | Yetkinlikler                                              |
|------------------------|------------------------------|------------------------------------------------------------|
| **Aleks Dulda**        | Proje Yöneticisi             | İletişim, ekip koordinasyonu, dökümantasyon                |
| **Murat Demirbaş**     | Backend / Frontend Geliştirici| Flask, Python, OpenAI API, SQL, HTML/CSS                  |
| **Muhammet Emin Alantepe** | Veritabanı Uzmanı         | SQL, Veri Modelleme, Veritabanı Yönetimi                  |
| **Enes Malik Altınpınar**| Test & Kalite Uzmanı       | Unit Test, Senaryo Testleri, Versiyon Takibi              |
| **Kaan Çardak**        | Topluluk ve Yatırım İlişkileri | Açık kaynak iletişimi, tanıtım, sponsorluk                |

---

## 💻 Kullanılan Teknolojiler

### Yazılım

- **Python 3.x** – Backend geliştirme  
- **Flask** – Web uygulama çatısı  
- **OpenAI GPT-3.5/4 API** – Doğal dil işleme  
- **SQLite** – Hafif veritabanı yönetimi  
- **HTML/CSS + Jinja2** – Dinamik web arayüzü  
- **Tabulate** – Tablo formatlı veri sunumu  
- **Chart.js / D3.js** – Görselleştirme desteği

---

### Donanım / Altyapı

- Lokal çalıştırma desteği (offline geliştirme)  
- Docker / Cloud deploy opsiyonları (Heroku, Render, vs.)

---
## Kurulum Talimatları

1. Projeyi klonlayın veya zip dosyasını indirin:  
   ```bash
   git clone https://github.com/kullanici/datasage.git
   ```  
2. Proje dizinine gidin:  
   ```bash
   cd datasage
   ```  
3. Bir Python sanal ortamı oluşturun ve etkinleştirin:  
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```  
4. Gerekli Python paketlerini yükleyin:  
   ```bash
   pip install -r requirements.txt
   ```  
5. `sakila.db` veritabanı dosyasını proje kök dizinine kopyalayın.  
6. OpenAI API anahtarınızı ortam değişkeni olarak ayarlayın:  
   ```bash
   export OPENAI_API_KEY="sizin_api_anahtarınız"
   ```  
7. Uygulamayı başlatın:  
   ```bash
   flask run
   ```  
   veya  
   ```bash
   python app.py
   ```  

## Kullanım

- Tarayıcınızda `http://localhost:5000` adresine gidin.  
- Sorgunuzu doğal dilde yazın ve Gönder butonuna basın.  
- SQL sorgusu oluşturulacak ve sonuçlar gösterilecektir.

## Örnek Çıktı

**Sorgu:** "Ücreti 0.99 olan filmleri göster."  
**SQL Çıktısı:**
```sql
SELECT title FROM film WHERE rental_rate = 0.99;
```

**Örnek Sonuç:**

| title             |
|-------------------|
| Academy Dinosaur  |
| Ace Goldfinger    |
| Adaptation Holes  |
| ...               |

## Güvenlik Notu

API anahtarınızı asla kod içinde açık olarak bırakmayın. Ortam değişkeni olarak kullanmanız önerilir.

## Katkıda Bulunma

- Issue açarak katkıda bulunabilirsiniz.  
- Pull request göndererek kod katkısı sağlayabilirsiniz.

---

## 🔧 Yazılım Geliştirme Süreci

Proje, **iteratif ve artımlı Agile yazılım geliştirme yaklaşımı** benimsenerek aşağıdaki aşamalarla geliştirilmiştir:

1. **İhtiyaç Analizi** – Hedef kullanıcı profili ve veri ihtiyaçları belirlendi.  
2. **Tasarım** – Arayüz ve sistem mimarisi (API, veritabanı) tasarlandı.  
3. **Geliştirme** – OpenAI API entegrasyonu ve sorgu işleyici yazıldı.  
4. **Test & Debug** – Fonksiyonel testler ve hata düzeltmeleri yapıldı.  
5. **Dokümantasyon & Yayınlama** – Kullanım kılavuzu hazırlandı, dağıtıma uygun hale getirildi.

---

## 🌍 Global Geliştiricilere Açık Çağrı

> **Data Sage, açık kaynak bir projedir!**  
Projeye katkı sunmak isteyen dünya çapındaki geliştiricileri bekliyoruz.

Siz de katkıda bulunabilirsiniz:

- 🧩 Kod katkısı
- 🐞 Hata bildirimi
- 🌐 Çok dilli çeviri desteği
- 📖 Belgeleri iyileştirme
- 💡 Yeni özellik önerileri

👉 PR gönderin veya `issues` sekmesinden bizimle iletişime geçin.

---

## 💰 Yatırımcılara ve Destekçilere Davet

Veri analizini demokratikleştirme yolculuğunda sizinle büyümek istiyoruz.

**Destekleriniz ile:**

- Daha büyük dil modelleri (GPT-4, Claude, vs.) entegre edilebilir  
- Mobil uygulamalar geliştirilebilir  
- Sesli komut, çoklu dil desteği gibi yenilikler eklenebilir  

**Destekçiler için ayrıcalıklar:**

- Sponsor logonuz GitHub'da ve platformda yer alır  
- Etki analiz raporları paylaşılır  
- Açık kaynak destekçi rozetleri verilir  

---

## 📬 İletişim

- ✉️ Email: aleksdulda@gmail.com
- 🔗 GitHub: [github.com/aleksdulda](https://github.com/aleksdulda)  

---

> Projeye yıldız bırakmayı ve katkı sağlamayı unutmayın! ⭐  
