import streamlit as st
import pandas as pd
import time
import io
import zipfile
import numpy as np
from datetime import datetime, timedelta

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="Veri Yükleme",
    page_icon="📤",
    layout="wide"
)

# ============================================
# CSS - YAZI TİPLERİNİ %30 KÜÇÜLT
# ============================================
st.markdown("""
<style>
    html, body, [class*="css"] {
        font-size: 70% !important;
    }
    h1 { font-size: 1.8rem !important; }
    h2 { font-size: 1.4rem !important; }
    h3 { font-size: 1.2rem !important; }
    .stButton>button { font-size: 0.7rem !important; }
    .stSelectbox, .stMultiSelect, .stTextInput { font-size: 0.7rem !important; }
</style>
""", unsafe_allow_html=True)

# Session state başlatma
if 'urun_master' not in st.session_state:
    st.session_state.urun_master = None
if 'magaza_master' not in st.session_state:
    st.session_state.magaza_master = None
if 'yasak_master' not in st.session_state:
    st.session_state.yasak_master = None
if 'depo_stok' not in st.session_state:
    st.session_state.depo_stok = None
if 'anlik_stok_satis' not in st.session_state:
    st.session_state.anlik_stok_satis = None
if 'haftalik_trend' not in st.session_state:
    st.session_state.haftalik_trend = None
if 'kpi' not in st.session_state:
    st.session_state.kpi = None
if 'po_yasak' not in st.session_state:
    st.session_state.po_yasak = None
if 'po_detay_kpi' not in st.session_state:
    st.session_state.po_detay_kpi = None

# ============================================
# ANA SAYFA
# ============================================
st.title("📤 Ortak Veri Yükleme Merkezi")
st.markdown("---")

# CSV okuma fonksiyonu
def read_csv_safe(file):
    try:
        df = pd.read_csv(file, sep=';', encoding='utf-8-sig', quoting=1, on_bad_lines='warn')
        return df, ';'
    except:
        try:
            file.seek(0)
            df = pd.read_csv(file, sep=',', encoding='utf-8-sig', quoting=1, on_bad_lines='warn')
            return df, ','
        except Exception as e:
            raise Exception(f"CSV okuma hatası: {str(e)}")

# CSV yazma fonksiyonu
def write_csv_safe(df):
    return df.to_csv(index=False, sep=';', encoding='utf-8-sig', quoting=1)

# Örnek CSV'ler
example_csvs = {
    'urun_master.csv': {
        'data': pd.DataFrame({
            'urun_kod': ['U001', 'U002', 'U003'],
            'satici_kod': ['S001', 'S002', 'S001'],
            'kategori_kod': ['K001', 'K002', 'K001'],
            'umg': ['UMG1', 'UMG2', 'UMG1'],
            'mg': ['MG1', 'MG2', 'MG1'],
            'marka_kod': ['M001', 'M002', 'M001'],
            'klasman_kod': ['K1', 'K2', 'K1'],
            'nitelik': ['Nitelik 1, özellik A', 'Nitelik 2, özellik B', 'Nitelik 1, özellik C'],
            'durum': ['Aktif', 'Aktif', 'Pasif'],
            'ithal': [1, 0, 1],
            'olcu_birimi': ['Adet', 'Adet', 'Kg'],
            'koli_ici': [12, 24, 6],
            'paket_ici': [6, 12, 3]
        }),
        'icon': '📦'
    },
    'magaza_master.csv': {
        'data': pd.DataFrame({
            'magaza_kod': ['M001', 'M002', 'M003'],
            'il': ['İstanbul', 'Ankara', 'İzmir'],
            'bolge': ['Marmara', 'İç Anadolu', 'Ege'],
            'tip': ['Hipermarket', 'Süpermarket', 'Hipermarket'],
            'adres_kod': ['ADR001', 'ADR002', 'ADR003'],
            'sm': [5000, 3000, 4500],
            'bs': ['BS1', 'BS2', 'BS1'],
            'depo_kod': ['D001', 'D001', 'D002']
        }),
        'icon': '🏪'
    },
    'yasak.csv': {
        'data': pd.DataFrame({
            'urun_kod': ['U001', 'U002'],
            'magaza_kod': ['M002', 'M001'],
            'yasak_durum': [1, 1]
        }),
        'icon': '🚫'
    },
    'depo_stok.csv': {
        'data': pd.DataFrame({
            'depo_kod': ['D001', 'D001', 'D002'],
            'urun_kod': ['U001', 'U002', 'U001'],
            'stok': [1000, 1500, 800]
        }),
        'icon': '📦'
    },
    'anlik_stok_satis.csv': {
        'data': pd.DataFrame({
            'magaza_kod': ['M001', 'M001', 'M002'],
            'urun_kod': ['U001', 'U002', 'U001'],
            'stok': [100, 150, 120],
            'yol': [20, 30, 25],
            'satis': [50, 40, 45],
            'ciro': [5000, 6000, 5500],
            'smm': [2.0, 3.75, 2.67]
        }),
        'icon': '📊'
    },
    'haftalik_trend.csv': {
        'data': pd.DataFrame({
            'klasman_kod': ['K1', 'K1', 'K2'],
            'marka_kod': ['M001', 'M001', 'M002'],
            'yil': [2025, 2025, 2025],
            'hafta': [40, 41, 40],
            'stok': [10000, 9500, 15000],
            'satis': [2000, 2100, 1800],
            'ciro': [200000, 210000, 270000],
            'smm': [5.0, 4.52, 8.33],
            'iftutar': [1000000, 950000, 1500000]
        }),
        'icon': '📈'
    },
    'kpi.csv': {
        'data': pd.DataFrame({
            'mg_id': ['MG1', 'MG2', 'MG3'],
            'min_deger': [0, 100, 500],
            'max_deger': [99, 499, 999],
            'forward_cover': [1.5, 2.0, 2.5]
        }),
        'icon': '🎯'
    },
    'po_yasak.csv': {
        'data': pd.DataFrame({
            'urun_kodu': ['U001', 'U002', 'U003'],
            'yasak_durum': [1, 0, 1],
            'acik_siparis': [100, 0, 250]
        }),
        'icon': '🚫'
    },
    'po_detay_kpi.csv': {
        'data': pd.DataFrame({
            'marka_kod': ['M001', 'M002', 'M003'],
            'mg_kod': ['MG1', 'MG2', 'MG1'],
            'cover_hedef': [12.0, 15.0, 10.0],
            'bkar_hedef': [25.0, 30.0, 20.0]
        }),
        'icon': '🎯'
    }
}

# Veri tanımları
data_definitions = {
    'urun_master': {
        'name': 'Ürün Master',
        'required': True,
        'columns': ['urun_kod', 'satici_kod', 'kategori_kod', 'umg', 'mg', 'marka_kod', 
                   'klasman_kod', 'nitelik', 'durum', 'ithal', 'olcu_birimi', 'koli_ici', 'paket_ici'],
        'state_key': 'urun_master',
        'icon': '📦',
        'modules': ['Sevkiyat', 'PO', 'Prepack']
    },
    'magaza_master': {
        'name': 'Mağaza Master',
        'required': True,
        'columns': ['magaza_kod', 'il', 'bolge', 'tip', 'adres_kod', 'sm', 'bs', 'depo_kod'],
        'state_key': 'magaza_master',
        'icon': '🏪',
        'modules': ['Sevkiyat', 'PO']
    },
    'depo_stok': {
        'name': 'Depo Stok',
        'required': True,
        'columns': ['depo_kod', 'urun_kod', 'stok'],
        'state_key': 'depo_stok',
        'icon': '📦',
        'modules': ['Sevkiyat', 'PO']
    },
    'anlik_stok_satis': {
        'name': 'Anlık Stok/Satış',
        'required': True,
        'columns': ['magaza_kod', 'urun_kod', 'stok', 'yol', 'satis', 'ciro', 'smm'],
        'state_key': 'anlik_stok_satis',
        'icon': '📊',
        'modules': ['Sevkiyat', 'PO']
    },
    'kpi': {
        'name': 'KPI',
        'required': True,
        'columns': ['mg_id', 'min_deger', 'max_deger', 'forward_cover'],
        'state_key': 'kpi',
        'icon': '🎯',
        'modules': ['Sevkiyat', 'PO']
    },
    'yasak_master': {
        'name': 'Yasak',
        'required': False,
        'columns': ['urun_kod', 'magaza_kod', 'yasak_durum'],
        'state_key': 'yasak_master',
        'icon': '🚫',
        'modules': ['Sevkiyat']
    },
    'haftalik_trend': {
        'name': 'Haftalık Trend',
        'required': False,
        'columns': ['klasman_kod', 'marka_kod', 'yil', 'hafta', 'stok', 'satis', 'ciro', 'smm', 'iftutar'],
        'state_key': 'haftalik_trend',
        'icon': '📈',
        'modules': ['Sevkiyat']
    },
    'po_yasak': {
        'name': 'PO Yasak',
        'required': False,
        'columns': ['urun_kodu', 'yasak_durum', 'acik_siparis'],
        'state_key': 'po_yasak',
        'icon': '🚫',
        'modules': ['PO']
    },
    'po_detay_kpi': {
        'name': 'PO Detay KPI',
        'required': False,
        'columns': ['marka_kod', 'mg_kod', 'cover_hedef', 'bkar_hedef'],
        'state_key': 'po_detay_kpi',
        'icon': '🎯',
        'modules': ['PO']
    }
}

# ============================================
# 📖 KULLANICI KILAVUZU - İNDİRİLEBİLİR DOKÜMAN
# ============================================
st.markdown("---")
st.subheader("📖 Kullanıcı Kılavuzu")

# Kılavuz içeriğini hazırla
kilavuz_metni = """
═══════════════════════════════════════════════════════════════
                    📖 VERİ YÜKLEME KILAVUZU
                        Thorius Sistemi
═══════════════════════════════════════════════════════════════

İçindekiler:
1. Hızlı Başlangıç
2. Dosya Formatı Gereksinimleri
3. Zorunlu Dosyalar ve Açıklamaları
4. Kolon Açıklamaları (Detaylı)
5. Yaygın Hatalar ve Çözümleri

═══════════════════════════════════════════════════════════════
1. HIZLI BAŞLANGIÇ
═══════════════════════════════════════════════════════════════

ADIM 1: Örnek Dosyaları İndirin
   → Sayfadaki "📥 Örnek CSV Dosyalarını İndir" butonuna tıklayın
   → İndirilen ZIP dosyasını açın
   → İçindeki CSV dosyalarını Excel ile açın ve inceleyin

ADIM 2: Kendi Verilerinizi Hazırlayın
   → Excel'de örnek dosyaları açın
   → Kendi verilerinizi AYNI FORMATTA girin
   → Kolon adlarını DEĞİŞTİRMEYİN!
   → "Farklı Kaydet" → "CSV UTF-8 (Virgülle ayrılmış)" seçin

ADIM 3: Dosyaları Yükleyin
   → "CSV dosyalarını seçin" alanına tıklayın
   → Hazırladığınız CSV dosyalarını seçin (birden fazla seçebilirsiniz)
   → "🚀 Tüm Dosyaları Yükle" butonuna basın
   → Durum tablosundan başarılı yüklemeyi kontrol edin

═══════════════════════════════════════════════════════════════
2. DOSYA FORMATI GEREKSİNİMLERİ
═══════════════════════════════════════════════════════════════

✅ DOĞRU FORMAT:
   • Dosya türü: CSV (Comma Separated Values)
   • Kodlama: UTF-8 (Türkçe karakterler için ZORUNLU)
   • Ayraç: Noktalı virgül (;) veya virgül (,)
   • İlk satır: Kolon başlıkları (küçük harf, alt çizgi ile)
   • Örnek: urun_kod, magaza_kod, stok

❌ YANLIŞ FORMAT:
   • Excel dosyaları (.xlsx, .xls) → Mutlaka CSV'ye çevirin!
   • PDF, Word dosyaları → CSV'ye çevirin!
   • Türkçe karakterli kolon adları → İngilizce kullanın
   • Boşluklu kolon adları → Alt çizgi (_) kullanın

Excel'de CSV Kaydetme:
   1. "Dosya" → "Farklı Kaydet"
   2. "Dosya türü" → "CSV UTF-8 (Virgülle ayrılmış) (*.csv)"
   3. Kaydet

═══════════════════════════════════════════════════════════════
3. ZORUNLU DOSYALAR VE AÇIKLAMALARI
═══════════════════════════════════════════════════════════════

Bu 5 dosya MUTLAKA yüklenmelidir:

┌─────────────────────────────────────────────────────────────┐
│ 📦 ÜRÜN MASTER (urun_master.csv)                            │
├─────────────────────────────────────────────────────────────┤
│ • Tüm ürünlerin temel bilgileri                             │
│ • Neden gerekli: Ürün kodlarını tanımak ve kategorize etmek│
│ • Minimum satır sayısı: En az 1 ürün                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 🏪 MAĞAZA MASTER (magaza_master.csv)                        │
├─────────────────────────────────────────────────────────────┤
│ • Tüm mağazaların temel bilgileri                           │
│ • Neden gerekli: Mağaza kodlarını tanımak ve lokasyon bilgi│
│ • Minimum satır sayısı: En az 1 mağaza                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 📦 DEPO STOK (depo_stok.csv)                                │
├─────────────────────────────────────────────────────────────┤
│ • Depolardaki mevcut stok miktarları                        │
│ • Neden gerekli: Sevkiyat için uygun stok kontrolü         │
│ • Format: Her depo-ürün kombinasyonu için stok miktarı     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 📊 ANLIK STOK/SATIŞ (anlik_stok_satis.csv)                 │
├─────────────────────────────────────────────────────────────┤
│ • Mağazalardaki güncel stok ve satış bilgileri              │
│ • Neden gerekli: İhtiyaç hesaplamak için temel veri        │
│ • Format: Her mağaza-ürün kombinasyonu için bilgiler       │
│ • ÖNEMLİ: Büyük dosyalarda parçalı yükleme kullanın!       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 🎯 KPI (kpi.csv)                                            │
├─────────────────────────────────────────────────────────────┤
│ • Hedef ve limitler (min/max değerler)                     │
│ • Neden gerekli: Minimum/maksimum stok hedefleri için      │
│ • Format: Mal grubu bazında hedef değerler                 │
└─────────────────────────────────────────────────────────────┘

OPSİYONEL DOSYALAR (İsteğe Bağlı):
   • 🚫 Yasak: Bazı ürünlerin bazı mağazalara gitmemesi
   • 📈 Haftalık Trend: Geçmiş haftalık satış verileri
   • 🚫 PO Yasak: Alım siparişi yasak ürünler
   • 🎯 PO Detay KPI: Alım siparişi detaylı hedefler

═══════════════════════════════════════════════════════════════
Son Güncelleme: 2025
Versiyon: 1.0
"""

# İndirme butonları
col1, col2, col3 = st.columns(3)

with col1:
    st.download_button(
        label="📥 Kılavuzu İndir (.txt)",
        data=kilavuz_metni,
        file_name="veri_yukleme_kilavuzu.txt",
        mime="text/plain",
        use_container_width=True,
        help="Metin formatında indir - Not Defteri ile açılabilir"
    )

with col2:
    st.download_button(
        label="📥 Kılavuzu İndir (.md)",
        data=kilavuz_metni,
        file_name="veri_yukleme_kilavuzu.md",
        mime="text/markdown",
        use_container_width=True,
        help="Markdown formatında indir - GitHub'da güzel görünür"
    )

with col3:
    # HTML formatı için
    html_content = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Veri Yükleme Kılavuzu</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
            h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; }}
            h2 {{ color: #34495e; margin-top: 30px; }}
            pre {{ background: #f4f4f4; padding: 15px; border-left: 4px solid #3498db; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #3498db; color: white; }}
            .success {{ color: #27ae60; }}
            .error {{ color: #e74c3c; }}
            .warning {{ color: #f39c12; }}
        </style>
    </head>
    <body>
        <pre>{kilavuz_metni}</pre>
    </body>
    </html>
    """
    
    st.download_button(
        label="📥 Kılavuzu İndir (.html)",
        data=html_content,
        file_name="veri_yukleme_kilavuzu.html",
        mime="text/html",
        use_container_width=True,
        help="HTML formatında indir - Tarayıcıda açılabilir"
    )

st.info("💡 **İpucu:** Kılavuzu indirip kaydedin, ihtiyaç duyduğunuzda açın!")

st.markdown("---")

# ============================================
# ÖZEL: ANLIK STOK/SATIŞ PARÇALI YÜKLEME
# ============================================
st.subheader("📊 Anlık Stok/Satış - Parçalı Yükleme")
st.info("💡 **İpucu:** Büyük dosyaları parça parça yükleyebilirsiniz. Sistem otomatik birleştirecek.")

anlik_parts = st.file_uploader(
    "Anlık Stok/Satış CSV parçalarını seçin (birden fazla)",
    type=['csv'],
    accept_multiple_files=True,
    key="anlik_parts_upload"
)

if anlik_parts:
    st.write(f"**{len(anlik_parts)} parça seçildi**")
    
    if st.button("🔗 Parçaları Birleştir ve Yükle", type="primary", use_container_width=True):
        try:
            combined_df = None
            total_rows = 0
            part_info = []
            
            for idx, part_file in enumerate(anlik_parts, 1):
                # CSV oku
                df_part, used_sep = read_csv_safe(part_file)
                
                # Kolon kontrolü
                expected_cols = set(data_definitions['anlik_stok_satis']['columns'])
                if not expected_cols.issubset(set(df_part.columns)):
                    st.error(f"❌ {part_file.name}: Eksik kolonlar var!")
                    continue
                
                # Sadece gerekli kolonları al
                df_part = df_part[data_definitions['anlik_stok_satis']['columns']].copy()
                
                # String kolonları temizle
                string_cols = df_part.select_dtypes(include=['object']).columns
                for col in string_cols:
                    df_part[col] = df_part[col].str.strip()
                
                # 🆕 Sayısal kolonları zorla
                numeric_cols = ['stok', 'yol', 'satis', 'ciro', 'smm']
                for col in numeric_cols:
                    if col in df_part.columns:
                        df_part[col] = pd.to_numeric(df_part[col], errors='coerce').fillna(0)
                
                # Birleştir
                if combined_df is None:
                    combined_df = df_part
                else:
                    combined_df = pd.concat([combined_df, df_part], ignore_index=True)
                
                part_info.append(f"✅ Parça {idx}: {len(df_part):,} satır")
                total_rows += len(df_part)
            
            if combined_df is not None:
                # Duplicate kontrolü (opsiyonel)
                before_dedup = len(combined_df)
                combined_df = combined_df.drop_duplicates(subset=['magaza_kod', 'urun_kod'], keep='last')
                after_dedup = len(combined_df)
                
                # Kaydet
                st.session_state.anlik_stok_satis = combined_df
                
                # Sonuçları göster
                st.success(f"🎉 **Başarıyla birleştirildi!**")
                for info in part_info:
                    st.write(info)
                
                st.info(f"""
                **Özet:**
                - Toplam yüklenen: {total_rows:,} satır
                - Duplicate temizlendi: {before_dedup - after_dedup:,} satır
                - Final: {after_dedup:,} satır
                """)
                
                time.sleep(1)
                st.rerun()
        
        except Exception as e:
            st.error(f"❌ Birleştirme hatası: {str(e)}")

st.markdown("---")

# ============================================
# ÇOKLU DOSYA YÜKLEME + ÖRNEK İNDİRME
# ============================================
st.subheader("📤 Çoklu Dosya Yükleme")

col1, col2 = st.columns([2, 1])

with col1:
    uploaded_files = st.file_uploader(
        "CSV dosyalarını seçin (birden fazla seçebilirsiniz)",
        type=['csv'],
        accept_multiple_files=True,
        key="multi_upload"
    )

with col2:
    separator_option = st.selectbox(
        "CSV Ayracı:",
        options=['Otomatik Algıla', 'Noktalı Virgül (;)', 'Virgül (,)', 'Tab (\\t)'],
        help="CSV dosyanızdaki alan ayracını seçin"
    )
    
    separator_map = {
        'Otomatik Algıla': 'auto',
        'Noktalı Virgül (;)': ';',
        'Virgül (,)': ',',
        'Tab (\\t)': '\t'
    }
    selected_separator = separator_map[separator_option]

# Örnek İndirme Butonu - EXPANDER YOK, DİREKT BUTON
col1, col2 = st.columns(2)

with col1:
    if uploaded_files:
        if st.button("🚀 Tüm Dosyaları Yükle", type="primary", use_container_width=True):
            upload_results = []
            
            for uploaded_file in uploaded_files:
                filename = uploaded_file.name.lower()
                
                matched_key = None
                for key, definition in data_definitions.items():
                    if key in filename or definition['name'].lower().replace(' ', '_') in filename:
                        matched_key = key
                        break
                
                if not matched_key:
                    upload_results.append({
                        'Dosya': uploaded_file.name,
                        'Durum': '❌ Eşleştirilemedi'
                    })
                    continue
                
                definition = data_definitions[matched_key]
                
                try:
                    if selected_separator == 'auto':
                        df, used_sep = read_csv_safe(uploaded_file)
                    else:
                        df = pd.read_csv(uploaded_file, sep=selected_separator, encoding='utf-8-sig', 
                                       quoting=1, on_bad_lines='warn')
                    
                    existing_cols = set(df.columns)
                    required_cols = set(definition['columns'])
                    missing_cols = required_cols - existing_cols
                    
                    if missing_cols:
                        upload_results.append({
                            'Dosya': uploaded_file.name,
                            'Durum': f"❌ Eksik kolon: {', '.join(list(missing_cols)[:3])}"
                        })
                    else:
                        df_clean = df[definition['columns']].copy()
                        
                        # String kolonları temizle
                        string_columns = df_clean.select_dtypes(include=['object']).columns
                        for col in string_columns:
                            df_clean[col] = df_clean[col].str.strip() if df_clean[col].dtype == 'object' else df_clean[col]
                        
                        # 🆕 SAYISAL KOLONLARI ZORLA (Özel dosyalar için)
                        if matched_key == 'anlik_stok_satis':
                            # Anlık Stok/Satış için sayısal kolonları zorla
                            numeric_cols = ['stok', 'yol', 'satis', 'ciro', 'smm']
                            for col in numeric_cols:
                                if col in df_clean.columns:
                                    df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
                        
                        elif matched_key == 'depo_stok':
                            # Depo Stok için sayısal kolonları zorla
                            if 'stok' in df_clean.columns:
                                df_clean['stok'] = pd.to_numeric(df_clean['stok'], errors='coerce').fillna(0)
                        
                        elif matched_key == 'kpi':
                            # KPI için sayısal kolonları zorla
                            numeric_cols = ['min_deger', 'max_deger', 'forward_cover']
                            for col in numeric_cols:
                                if col in df_clean.columns:
                                    df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
                        
                        st.session_state[definition['state_key']] = df_clean
                        upload_results.append({
                            'Dosya': uploaded_file.name,
                            'Durum': f"✅ {len(df_clean):,} satır"
                        })
                
                except Exception as e:
                    upload_results.append({
                        'Dosya': uploaded_file.name,
                        'Durum': f"❌ Hata: {str(e)[:30]}"
                    })
            
            st.markdown("---")
            for result in upload_results:
                if '✅' in result['Durum']:
                    st.success(f"{result['Dosya']}: {result['Durum']}")
                else:
                    st.error(f"{result['Dosya']}: {result['Durum']}")
            
            time.sleep(1)
            st.rerun()

with col2:
    # Örnek CSV indirme butonu
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename, file_info in example_csvs.items():
            csv_data = write_csv_safe(file_info['data'])
            zip_file.writestr(filename, csv_data)
    
    st.download_button(
        label="📥 Örnek CSV Dosyalarını İndir",
        data=zip_buffer.getvalue(),
        file_name="ornek_csv_dosyalari.zip",
        mime="application/zip",
        type="secondary",
        use_container_width=True
    )

st.markdown("---")


# ============================================
# VERİ YÜKLEME DURUMU TABLOSU - DÜZELTİLMİŞ
# ============================================
st.subheader("📊 Veri Yükleme Durumu")

status_data = []
for key, definition in data_definitions.items():
    data = st.session_state.get(definition['state_key'])
    
    if data is not None and len(data) > 0:
        status = '✅ Başarılı'
        kolon_sayisi = str(len(data.columns))  # 🆕 String'e çevir (Arrow hatası için)
        boyut_mb = f"{data.memory_usage(deep=True).sum() / 1024**2:.2f}"
    else:
        status = '❌ Yüklenmedi'
        kolon_sayisi = '-'
        boyut_mb = '-'
    
    status_data.append({
        'CSV Adı': f"{definition['icon']} {definition['name']}",
        'Zorunlu': 'Evet ⚠️' if definition['required'] else 'Hayır ℹ️',
        'Kolon Sayısı': kolon_sayisi,
        'Durum': status,
        'Boyut (MB)': boyut_mb
    })

status_df = pd.DataFrame(status_data)

st.dataframe(
    status_df,
    use_container_width=True,
    hide_index=True,
    height=350
)

# Özet metrikler
col1, col2, col3 = st.columns(3)
with col1:
    zorunlu_count = sum(1 for d in data_definitions.values() if d['required'])
    zorunlu_loaded = sum(1 for k, d in data_definitions.items() 
                        if d['required'] and st.session_state.get(d['state_key']) is not None)
    st.metric("Zorunlu Dosyalar", f"{zorunlu_loaded}/{zorunlu_count}")

with col2:
    opsiyonel_count = sum(1 for d in data_definitions.values() if not d['required'])
    opsiyonel_loaded = sum(1 for k, d in data_definitions.items() 
                          if not d['required'] and st.session_state.get(d['state_key']) is not None)
    st.metric("Opsiyonel Dosyalar", f"{opsiyonel_loaded}/{opsiyonel_count}")

with col3:
    all_ready = zorunlu_loaded == zorunlu_count
    st.metric("Sistem Durumu", "Hazır ✅" if all_ready else "Eksik ⚠️")

st.markdown("---")




# TEK DOSYA DETAYI
st.subheader("🔍 Detaylı Veri İncelemesi")

selected_data = st.selectbox(
    "İncelemek istediğiniz veriyi seçin:",
    options=[k for k in data_definitions.keys() if st.session_state.get(data_definitions[k]['state_key']) is not None],
    format_func=lambda x: f"{data_definitions[x]['icon']} {data_definitions[x]['name']}",
    key="detail_select"
) if any(st.session_state.get(data_definitions[k]['state_key']) is not None for k in data_definitions.keys()) else None

if selected_data:
    current_def = data_definitions[selected_data]
    data = st.session_state[current_def['state_key']]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Satır", f"{len(data):,}")
    with col2:
        st.metric("Kolon", len(data.columns))
    with col3:
        st.metric("Bellek", f"{data.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

st.markdown("---")

# CSV İNDİR
st.subheader("📤 Veri Dosyası İndir")

if any(st.session_state.get(data_definitions[k]['state_key']) is not None for k in data_definitions.keys()):
    export_data = st.selectbox(
        "İndirmek istediğiniz veriyi seçin:",
        options=[k for k in data_definitions.keys() if st.session_state.get(data_definitions[k]['state_key']) is not None],
        format_func=lambda x: f"{data_definitions[x]['icon']} {data_definitions[x]['name']}",
        key="export_select"
    )
    
    if export_data:
        export_def = data_definitions[export_data]
        export_df = st.session_state[export_def['state_key']]
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            csv_data = write_csv_safe(export_df)
            st.download_button(
                label=f"📥 CSV İndir (;)",
                data=csv_data,
                file_name=f"{export_def['name'].lower().replace(' ', '_')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            csv_data_comma = export_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label=f"📥 CSV İndir (,)",
                data=csv_data_comma,
                file_name=f"{export_def['name'].lower().replace(' ', '_')}_comma.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col3:
            if st.button("🗑️ Bu Veriyi Sil", use_container_width=True):
                st.session_state[export_def['state_key']] = None
                st.success(f"✅ {export_def['name']} silindi!")
                time.sleep(0.5)
                st.rerun()
else:
    st.info("İndirilebilecek veri yok")

st.markdown("---")

# Başarı mesajı ve yönlendirme
required_loaded_final = sum(1 for k, d in data_definitions.items() 
                           if d['required'] and st.session_state.get(d['state_key']) is not None)
required_count_final = sum(1 for d in data_definitions.values() if d['required'])

if required_loaded_final == required_count_final and required_count_final > 0:
    st.success("✅ **Tüm zorunlu veriler yüklendi!** Modüllere geçebilirsiniz.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➡️ Sevkiyat Modülüne Git", use_container_width=True):
            st.switch_page("pages/2_Sevkiyat.py")
    with col2:
        if st.button("➡️ Alım Sipariş Modülüne Git", use_container_width=True):
            st.switch_page("pages/4_PO.py")
