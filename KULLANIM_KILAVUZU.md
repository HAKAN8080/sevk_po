# Otomatik Transfer Modülü - Kullanım Kılavuzu

## İçindekiler
1. [Genel Bakış](#genel-bakış)
2. [Başlangıç](#başlangıç)
3. [Adım Adım Kullanım](#adım-adım-kullanım)
4. [Parametreler Detaylı Açıklama](#parametreler-detaylı-açıklama)
5. [Transfer Mantığı](#transfer-mantığı)
6. [Örnek Senaryolar](#örnek-senaryolar)
7. [İpuçları ve Öneriler](#ipuçları-ve-öneriler)
8. [Sorun Giderme](#sorun-giderme)

---

## Genel Bakış

**Otomatik Transfer Modülü**, mağazalar arası akıllı stok transferi yaparak:
- 🎯 Hızlı dönen mağazalara (düşük cover) öncelik verir
- 📦 Yavaş dönen mağazalardan (yüksek cover) stok aktarır
- 💰 Brut kar potansiyeline göre optimize eder
- 🔄 İki aşamalı filtreleme ile hassas eşleştirme yapar

### Temel Kavramlar

**Cover Nedir?**
- Cover = (Stok + Yoldaki) / Haftalık Satış
- Mevcut stoğun kaç hafta dayanacağını gösterir
- Düşük cover (< 4 hafta) → Hızlı dönen, stok ihtiyacı var
- Yüksek cover (≥ 12 hafta) → Yavaş dönen, fazla stok var

**İki Aşamalı Filtreleme:**
1. **Mağaza Sınıflandırma**: Toplam mağaza cover'a göre ALAN/VEREN belirlenir
2. **Ürün Eşleştirme**: Belirlenen mağazalar içinde ürün bazlı transfer yapılır

---

## Başlangıç

### 1. Veri Yükleme
Öncelikle gerekli veri dosyalarını yükleyin:

**Gerekli Dosyalar:**
- ✅ **Ürün Master**: Ürün hiyerarşisi (UMG, MG, Marka, Kategori, Klasman) ve min/max stok limitleri
- ✅ **Mağaza Master**: Mağaza bilgileri (bölge, il, tip)
- ✅ **Depo Stok**: Merkez depo stok seviyeleri
- ✅ **Anlık Stok/Satış**: Mağaza bazlı güncel stok ve satış verileri
- ✅ **KPI**: Forward cover değerleri (MG bazlı)

**Adımlar:**
1. Ana sayfadan "📤 Veri Yükleme'ye Git" butonuna tıklayın
2. Her dosya için "Browse files" ile CSV dosyasını seçin
3. Tüm dosyalar yüklendiğinde ✅ işareti görünecek

---

## Adım Adım Kullanım

### Adım 1: Bölge/İl Seçimi 🗺️

Transfer kapsamını belirleyin:

| Seçenek | Açıklama | Ne Zaman Kullanılır |
|---------|----------|---------------------|
| **Bölge İçi** | Sadece bir bölge içinde transfer | Lojistik maliyeti minimuma indirmek için |
| **İl İçi** | Seçilen il(ler) içinde transfer | Belirli şehirlerde stok dengeleme |
| **TR Geneli** | Tüm Türkiye genelinde transfer | Maksimum optimizasyon için |

### Adım 2: Transfer Parametrelerini Ayarlama ⚙️

Parametreler expander içinde gizlenebilir. Oka tıklayarak açın/kapatın.

#### 📦 Depo Stok Limiti
- **Amaç**: Sadece depoda az olan ürünleri transfer etmek
- **Kullanım**:
  - Checkbox'ı işaretleyin
  - Limit değerini girin (örn: 100)
  - Bu değerin **ALTINDA** stoku olan ürünler değerlendirilir
- **Örnek**: Limit = 100 → Depoda 0-99 adet olan ürünler transfer için uygun

#### 📏 Transfer Kuralları

**1. Min transfer/çift (Default: 50)**
- Bir veren-alan mağaza çifti için minimum toplam transfer
- **Örnek**: M1 → M2 toplam transfer < 50 ise bu çift iptal edilir
- **Ne zaman artırılır?** Daha büyük transferler isteniyorsa (örn: 100'e çıkarın)

**2. Max transfer/çift (Default: 1000)**
- Bir veren-alan mağaza çifti için maksimum toplam transfer
- Aşırı yüklenmeyi önler
- **Ne zaman artırılır?** Büyük transferler gerekiyorsa

**3. Min ürün transferi (Default: 2)**
- Her ürün için minimum transfer adedi
- **Amaç**: 1 adetlik gereksiz transferleri engeller
- Transfer < 2 ise o ürün transfer edilmez

**4. Verende min kalan (Default: 2)**
- Transfer sonrası veren mağazada kalacak minimum adet
- **Önemli Mantık**: Eğer kalan < 2 olacaksa, tamamını gönderir
- **Örnek**: Stok 5, transfer 4 → Kalan 1 < 2 → Tamamı (5) gönderilir

**5. Veren→Max alan (Default: 10)**
- Bir veren mağaza maksimum kaç farklı alan mağazaya mal verebilir
- **Amaç**: Veren mağaza geniş dağıtım yapabilir
- **Ne zaman azaltılır?** Daha az dağıtım isteniyorsa (örn: 3'e düşürün)

**6. Alan→Max veren (Default: 10)**
- Bir alan mağaza maksimum kaç farklı veren mağazadan mal alabilir
- **Amaç**: Alan mağaza geniş kaynaklardan transfer alabilir
- **Ne zaman azaltılır?** Daha az kaynak isteniyorsa (örn: 3'e düşürün)

#### 📊 Cover Kuralları

**Alan Cover < (hafta) (Default: 8.0)**
- Alan mağazalar için maksimum cover
- Cover < 8 hafta olanlar ALAN olabilir
- **Ne zaman azaltılır?** Daha agresif transfer için (örn: 4.0)
- **Ne zaman artırılır?** Daha seçici olmak için (örn: 12.0)

**Veren Cover ≥ (hafta) (Default: 15.0)**
- Veren mağazalar için minimum cover
- Cover ≥ 15 hafta olanlar VEREN olabilir
- **Ne zaman azaltılır?** Daha fazla veren bulmak için (örn: 10.0)
- **Ne zaman artırılır?** Sadece çok yavaş dönenleri transfer etmek için (örn: 20.0)

### Adım 3: Ürün Hiyerarşisi Filtreleme 🎯

İsteğe bağlı - Sadece belirli ürün gruplarını transfer etmek için:

- **UMG**: Ürün Müdür Grubu
- **MG**: Müdür Grubu
- **Marka**: Marka kodu
- **Kategori**: Kategori kodu
- **Klasman**: Klasman kodu

**İpucu**: Çoklu seçim yapabilirsiniz. Boş bırakırsanız tüm ürünler değerlendirilir.

### Adım 4: Transfer Hesaplama 🚀

"🚀 Transfer Önerilerini Hesapla" butonuna tıklayın.

**İşlem Süreci:**
1. ✅ Veri birleştirme ve filtreleme
2. 🏪 Mağaza sınıflandırma (ALAN/VEREN)
3. 📊 İhtiyaç hesaplama (RPT, Min, Initial)
4. 🔄 Veren optimizasyonu ile eşleştirme
5. 📏 Limit kontrolleri
6. 📈 Sonuçların gösterimi

### Adım 5: Sonuçları İnceleme ve İndirme 📥

**Özet İstatistikler:**
- Toplam transfer adedi
- Brüt kar potansiyeli
- Veren/Alan mağaza sayıları
- Ortalama veren başına alan sayısı

**Grafikler:**
- Veren başına transfer dağılımı
- Alan başına transfer dağılımı
- Bölge/İl bazlı dağılım

**Excel İndirme:**
- "📥 Excel İndir" butonu
- Tüm detaylar dahil
- Pivot tablolar için hazır

---

## Parametreler Detaylı Açıklama

### Transfer Kuralları Kombinasyonları

**Senaryo 1: Muhafazakar Transfer**
```
Min transfer/çift: 200
Max transfer/çift: 500
Min ürün transferi: 3
Verende min kalan: 5
Alan Cover: 3.0
Veren Cover: 16.0
```
→ Az ama kesin transferler

**Senaryo 2: Agresif Transfer**
```
Min transfer/çift: 50
Max transfer/çift: 2000
Min ürün transferi: 1
Verende min kalan: 0
Alan Cover: 6.0
Veren Cover: 8.0
```
→ Çok sayıda transfer

**Senaryo 3: Dengeli (Default)**
```
Min transfer/çift: 50
Max transfer/çift: 1000
Min ürün transferi: 2
Verende min kalan: 2
Veren→Max alan: 10
Alan→Max veren: 10
Alan Cover: 8.0
Veren Cover: 15.0
```
→ Optimal denge - Geniş kapsamlı çift yönlü transfer

---

## Transfer Mantığı

### 1. Mağaza Sınıflandırma

```
Mağaza Cover = Toplam (Stok + Yol) / Toplam Satış

ALAN Mağazalar: Mağaza Cover < 8.0
VEREN Mağazalar: Mağaza Cover ≥ 15.0

Önemli: Bir mağaza hem ALAN hem VEREN olamaz (exclusive)
```

### 2. İhtiyaç Hesaplama (ALAN için)

Her ürün için 3 farklı ihtiyaç hesaplanır, maksimumu alınır:

**RPT (Replenishment) İhtiyacı:**
```
Hedef Stok = Forward Cover × Satış
Hedef Stok = MIN(Hedef Stok, Max Deger)
RPT = Hedef Stok - Net Stok
RPT = MAX(RPT, 0)
```

**Min İhtiyacı:**
```
Min İhtiyaç = Min Deger - Net Stok
Min İhtiyaç = MAX(Min İhtiyaç, 0)
```

**Initial İhtiyacı:**
```
Eğer Net Stok = 0 ise:
    Initial = Min Deger
Değilse:
    Initial = 0
```

**Final İhtiyaç:**
```
İhtiyaç = MAX(RPT, Min, Initial)
```

### 3. Transfer Eşleştirme (VEREN Döngüsü)

Her VEREN mağaza için:

1. **Stok Hazırlama**: Net Stok hesapla
2. **ALAN Bulma**: Aynı ürünü ihtiyaç duyan ALAN'ları bul
3. **Bölge/İl Filtresi**: Transfer kapsamına göre filtrele
4. **Brüt Kar Sıralaması**: En yüksek brüt kar potansiyeline göre sırala
   ```
   Brüt Kar Potansiyel = (Ciro / Satış) × İhtiyaç
   ```
5. **Transfer Yapma**:
   - Her ALAN için transfer miktarı hesapla
   - Min ürün transferi kontrolü (< 2 ise skip)
   - Veren min kalan kontrolü (kalan < 2 ise tamamını gönder)
   - Veren stokunu azalt
6. **Limit Kontrolleri**:
   - Veren → Max alan sayısı (default: 3)
   - Alan → Max veren sayısı (default: 3)

### 4. Mağaza Çifti Kontrolleri

Transfer listesi oluştuktan sonra:

1. **Min Transfer/Çift Kontrolü**:
   ```
   Veren-Alan çiftinin toplam transferi ≥ 50 adet olmalı
   Değilse tüm çift iptal edilir
   ```

2. **Max Transfer/Çift Kontrolü**:
   ```
   Veren-Alan çiftinin toplam transferi ≤ 1000 adet olmalı
   Aşarsa en yüksek brüt kara göre önceliklendirilir
   ```

---

## Örnek Senaryolar

### Senaryo 1: Bölge İçi Hızlı Transfer

**Durum**: Marmara bölgesinde acil stok dengeleme gerekiyor.

**Parametreler:**
- Transfer Kapsamı: Bölge İçi → Marmara
- Depo Limit: Kapalı (tüm ürünler)
- Alan Cover: 6.0 (acil olanlar)
- Veren Cover: 15.0
- Min transfer/çift: 30 (küçük transferlere de izin ver)

**Sonuç**: Sadece Marmara bölgesindeki mağazalar arası hızlı transfer.

---

### Senaryo 2: Belirli Markalar için TR Geneli

**Durum**: Nike ve Adidas markalarında ülke genelinde optimizasyon.

**Parametreler:**
- Transfer Kapsamı: TR Geneli
- Ürün Filtresi: Marka → Nike, Adidas
- Depo Limit: 200 (depoda az olanlar)
- Alan Cover: 8.0
- Veren Cover: 18.0 (çok yavaş dönenler)
- Max transfer/çift: 2000 (büyük transferlere izin ver)

**Sonuç**: Sadece seçilen markalar için ülke çapında dengeleme.

---

### Senaryo 3: İstanbul + Ankara Arası

**Durum**: Sadece İstanbul ve Ankara mağazaları arası transfer.

**Parametreler:**
- Transfer Kapsamı: İl İçi → İstanbul, Ankara
- Alan Cover: 8.0
- Veren Cover: 15.0
- Veren→Max alan: 10 (geniş dağıtım)

**Sonuç**: İki büyük şehir arasında optimize transfer.

---

## İpuçları ve Öneriler

### ✅ En İyi Uygulamalar

1. **İlk Çalıştırmada**:
   - Tüm parametreleri default'ta bırakın
   - TR Geneli seçin
   - Sonuçları inceleyin
   - İhtiyaca göre parametreleri ayarlayın

2. **Transfer Çok Az Çıkıyorsa**:
   - Alan Cover'ı artırın (örn: 12.0)
   - Veren Cover'ı azaltın (örn: 10.0)
   - Min transfer/çift'i azaltın (örn: 30)
   - Depo limitini kaldırın

3. **Transfer Çok Fazla Çıkıyorsa**:
   - Alan Cover'ı azaltın (örn: 4.0)
   - Veren Cover'ı artırın (örn: 20.0)
   - Min transfer/çift'i artırın (örn: 100)
   - Depo limiti ekleyin

4. **Lojistik Optimizasyonu**:
   - Bölge İçi veya İl İçi seçin
   - Veren→Max alan'ı düşük tutun (3-5)
   - Min transfer/çift'i artırın (örn: 100)

5. **Brüt Kar Odaklı**:
   - TR Geneli seçin
   - Max transfer/çift'i artırın
   - Alan Cover'ı yüksek tutun (yüksek cirolu mağazalar)

### ⚠️ Dikkat Edilmesi Gerekenler

- **Sezonluk Ürünler**: Forward cover değerleri güncel olmalı
- **Yoldaki Ürünler**: Anlık stok verisinde "yol" kolonunu mutlaka doldurun
- **Min/Max Değerler**: Ürün master'da eksik olmamalı
- **Bölge/İl Bilgileri**: Mağaza master'da doğru olmalı

### 🚀 Performans İpuçları

- **Büyük veri setleri** için önce bölge/il filtresi uygulayın
- **Ürün hiyerarşisi** ile filtreleyerek hızlı test yapın
- **Depo limiti** kullanarak ürün sayısını azaltın

---

## Sorun Giderme

### ❌ "Eksik Veri" Hatası

**Çözüm**:
1. Veri Yükleme sayfasına gidin
2. Tüm 5 dosyanın yüklendiğinden emin olun
3. CSV dosyalarının doğru formatta olduğunu kontrol edin

---

### ⚠️ "Transfer kalmadı" Uyarısı

**Sebepler**:
1. Min transfer/çift çok yüksek
2. Cover kriterleri çok sıkı
3. Bölge/İl filtresi çok dar

**Çözüm**:
- Min transfer/çift'i azaltın (örn: 30)
- Alan Cover'ı artırın (örn: 10.0)
- Veren Cover'ı azaltın (örn: 12.0)
- Transfer kapsamını genişletin

---

### 📊 "ALAN/VEREN mağaza bulunamadı"

**Sebepler**:
1. Cover kriterleri çok katı
2. Seçilen bölge/ilde uygun mağaza yok

**Çözüm**:
- Cover eşiklerini gevşetin
- TR Geneli'ne geçin
- Farklı bölge/il deneyin

---

### 🔢 "Depo stok limiti sonrası ürün kalmadı"

**Sebepler**:
1. Depo limiti çok düşük
2. Depoda az ürün var

**Çözüm**:
- Depo limitini artırın veya kaldırın
- Depo stok verilerini kontrol edin

---

## Teknik Destek

Sorun yaşıyorsanız:

1. **Hata Mesajını Kaydedin**: Ekran görüntüsü alın
2. **Parametreleri Notlayın**: Hangi ayarlarla çalıştırdığınızı not edin
3. **Veri Kontrolü**: CSV dosyalarının formatını kontrol edin
4. **GitHub Issues**: https://github.com/kullaniciadi/retail-analytics/issues

---

## Versiyon Geçmişi

**v2.0** (2026-01-07)
- ✨ Otomatik Transfer modülü eklendi
- ✨ İki aşamalı filtreleme sistemi
- ✨ Veren optimizasyonu (brüt kar bazlı)
- ✨ Parametrik kontroller (6 yeni parametre)
- 🎨 Kompakt UI tasarımı
- 📊 Gelişmiş raporlama

---

**Son Güncelleme**: 7 Ocak 2026
**Hazırlayan**: Retail Analytics Ekibi
