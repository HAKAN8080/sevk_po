# Retail Analytics Platform

Perakende mağaza zinciri için geliştirilmiş stok yönetimi ve transfer optimizasyon platformu.

## Özellikler

### 📤 Veri Yükleme
- Ürün Master verisi
- Mağaza Master verisi
- Depo Stok bilgileri
- Anlık Stok/Satış verileri
- KPI (Forward Cover) verileri

### 🔄 Otomatik Transfer
Mağazalar arası akıllı stok transfer sistemi:
- **İki Aşamalı Filtreleme**: Önce mağaza seviyesinde ALAN/VEREN sınıflandırması, sonra ürün bazında eşleştirme
- **Cover Bazlı Optimizasyon**: Stok/Satış oranına göre transfer kararları
- **İhtiyaç Hesaplama**: RPT (Forward Cover), Min Limit ve Initial Stok bazlı üç farklı yaklaşım
- **Veren Optimizasyonu**: Her veren mağaza, brut kar potansiyeline göre minimum sayıda alana transfer yapar
- **Parametrik Kontrol**: Transfer limitleri (min 50 adet/çift), cover eşikleri (alan < 8, veren ≥ 15 hafta), geniş dağıtım (10'a kadar mağaza)

**Parametreler:**
- Depo stok limiti
- Alan/Veren Cover eşikleri
- Min/Max transfer miktarları
- Mağaza başına maksimum transfer sayısı

**Transfer Kapsamı:**
- Bölge içi
- İl bazlı (çoklu seçim)
- Türkiye geneli

**Filtreleme:**
- Ürün Müdürlüğü (UMG)
- Müdürlük (MG)
- Marka
- Kategori
- Klasman

### 📦 Sevkiyat
Merkez depodan mağazalara sevkiyat planlama modülü.

### 🛒 PO (Purchase Order)
Satın alma sipariş yönetim modülü.

## Kurulum

### Gereksinimler
- Python 3.8+
- pip

### Adımlar

1. Repoyu klonlayın:
```bash
git clone https://github.com/kullaniciadi/retail-analytics.git
cd retail-analytics
```

2. Virtual environment oluşturun:
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows
```

3. Bağımlılıkları yükleyin:
```bash
pip install -r requirements.txt
```

## Kullanım

Uygulamayı başlatın:
```bash
streamlit run app.py
```

Tarayıcınızda `http://localhost:8501` adresine gidin.

### İlk Kullanım
1. **Veri Yükleme** sayfasından gerekli CSV dosyalarını yükleyin
2. İlgili modülü (Otomatik Transfer, Sevkiyat, PO) seçin
3. Parametreleri ayarlayın
4. Hesapla butonuna basın
5. Sonuçları Excel olarak indirin

## Teknik Detaylar

### Veri Yapısı
- **Ürün Master**: Ürün hiyerarşisi, min/max stok limitleri
- **Mağaza Master**: Mağaza bilgileri, bölge/il bilgileri
- **Depo Stok**: Merkez depo stok seviyeleri
- **Anlık Stok/Satış**: Mağaza bazlı güncel stok ve satış verileri
- **KPI**: Forward cover değerleri

### Transfer Algoritması
1. **Mağaza Sınıflandırma**: Toplam mağaza cover hesabı (tüm ürünler)
2. **ALAN/VEREN Belirleme**: Cover eşiklerine göre ayrıştırma (exclusive)
3. **Ürün İhtiyaç Hesaplama**: MAX(RPT, Min, Initial)
4. **Veren Döngüsü**: Her veren için brut kar potansiyeline göre alan seçimi
5. **Stok Tüketme**: Veren stoku dağıtılırken azaltılır
6. **Limit Kontrolleri**: Min/max transfer, mağaza çifti limitleri

## Lisans

Bu proje özel kullanım içindir.
