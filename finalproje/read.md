# 📌 Kütüphane Takip Sistemi

## 🧾 Proje Tanıtımı
Bu uygulama, kullanıcıların kitap ödünç alma işlemlerini ve üye yönetimini kolayca gerçekleştirebileceği bir kütüphane yönetim sistemidir. Flask framework’ü ile geliştirilmiştir. Kullanıcı girişi, kitap ekleme/silme, üye ekleme, ödünç işlemleri ve geçmiş kayıtları görüntüleme gibi işlemler yapılabilir.

## 🚀 Proje Özellikleri
- 🔐 Kullanıcı kayıt ve giriş işlemleri
- 📚 Kitap ekleme, düzenleme ve silme
- 👤 Üye ekleme, düzenleme ve silme
- 📖 Kitap ödünç alma ve iade işlemleri
- 🔎 Kitap ve üye arama / filtreleme özellikleri
- 📦 SQLite veritabanı ile kalıcı veri saklama
- 📊 Raporlama ve geçmiş görüntüleme

## ⚙️ Kurulum ve Çalıştırma

### ✅ Gereksinimler
Bu projeyi çalıştırmak için bilgisayarınızda aşağıdaki yazılımlar kurulu olmalıdır:
- Python 3.x

Ayrıca aşağıdaki kütüphaneler kullanılmaktadır:
- flask
- (Diğer gerekli kütüphaneler requirements.txt dosyasında listelenmiştir.)

Not: Gerekli kütüphaneleri otomatik olarak yüklemek için terminalde aşağıdaki komutu çalıştırabilirsiniz:
```
pip install -r requirements.txt
```

### 🚀 Uygulamayı Başlatma
Terminalde proje klasörüne gidip aşağıdaki komutu çalıştırın:
```
python app.py
```
Uygulama tarayıcınızda http://127.0.0.1:5000/ adresinde çalışacaktır.

## 📂 Proje Dosya Yapısı

```
proje-h1 - Kopya (2) - Kopya/
├── app.py                  # Ana Python uygulama dosyası
├── books.json              # Kitap verilerinin saklandığı dosya
├── users.json              # Kullanıcı verilerinin saklandığı dosya
├── requirements.txt        # Gerekli Python paketlerini içeren dosya
├── routes.py               # Uygulama rotalarını içeren dosya
├── instance/
│   └── site.db             # SQLite veritabanı dosyası
├── migrations/             # Veritabanı migrasyon dosyaları
├── static/
│   └── style.css           # Uygulamaya ait stil dosyası
├── templates/              # HTML şablonlarının bulunduğu klasör
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── kitaplar.html
│   ├── kitap_ekle.html
│   ├── kitap_duzenle.html
│   ├── uyeler.html
│   ├── uye_ekle.html
│   ├── profil.html
│   ├── ayarlar.html
│   ├── odunc.html
│   └── raporlar.html
└── README.md               # Proje açıklama dosyası
```
