import streamlit as st
import pandas as pd
import numpy as np
import time

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="Alım Sipariş (PO)",
    page_icon="💵",
    layout="wide"
)

# Session state başlatma
if 'urun_master' not in st.session_state:
    st.session_state.urun_master = None
if 'magaza_master' not in st.session_state:
    st.session_state.magaza_master = None
if 'anlik_stok_satis' not in st.session_state:
    st.session_state.anlik_stok_satis = None
if 'depo_stok' not in st.session_state:
    st.session_state.depo_stok = None
if 'kpi' not in st.session_state:
    st.session_state.kpi = None
if 'segmentation_params' not in st.session_state:
    st.session_state.segmentation_params = {
        'product_ranges': [(0, 4), (5, 8), (9, 12), (12, 15), (15, 20), (20, float('inf'))],
        'store_ranges': [(0, 4), (5, 8), (9, 12), (12, 15), (15, 20), (20, float('inf'))]
    }
if 'cover_segment_matrix' not in st.session_state:
    st.session_state.cover_segment_matrix = None
if 'sevkiyat_sonuc' not in st.session_state:
    st.session_state.sevkiyat_sonuc = None
if 'alim_siparis_sonuc' not in st.session_state:
    st.session_state.alim_siparis_sonuc = None
if 'po_yasak' not in st.session_state:
    st.session_state.po_yasak = None
if 'po_detay_kpi' not in st.session_state:
    st.session_state.po_detay_kpi = None

# Sidebar menü 
st.sidebar.title("💵 Alım Sipariş (Purchase Order)")
menu = st.sidebar.radio(
    "Menü",
    ["🏠 Ana Sayfa", "💵 Alım Sipariş Hesaplama", "📊 Alım Sipariş Raporları", "📦 Depo Bazlı Sipariş"]
)

# ============================================
# 🏠 ANA SAYFA
# ============================================
if menu == "🏠 Ana Sayfa":
    st.title("💵 Alım Sipariş (Purchase Order) Sistemi")
    st.markdown("---")
    
    # VERİ KONTROLÜ
    required_data = {
        "Anlık Stok/Satış": st.session_state.anlik_stok_satis,
        "Depo Stok": st.session_state.depo_stok,
        "KPI": st.session_state.kpi
    }
    
    optional_data = {
        "PO Yasak": st.session_state.po_yasak,
        "PO Detay KPI": st.session_state.po_detay_kpi,
        "Ürün Master": st.session_state.urun_master,
        "Mağaza Master": st.session_state.magaza_master
    }
    
    missing_data = [name for name, data in required_data.items() if data is None]
    
    if missing_data:
        st.info("""
        **👉 Lütfen önce veri yükleme sayfasından CSV dosyalarınızı yükleyin.**
        
        **Zorunlu dosyalar:**
        - Anlık Stok/Satış
        - Depo Stok
        - KPI
        
        **Opsiyonel dosyalar (önerilir):**
        - Ürün Master (koli bilgisi, durum, ithal bilgisi için)
        - PO Yasak (yasak ürünler ve açık siparişler için)
        - PO Detay KPI (marka/MG bazında özel hedefler için)
        """)
        
        if st.button("➡️ Veri Yükleme Sayfasına Git", type="primary", use_container_width=True):
            st.switch_page("pages/0_Veri_Yukleme.py")
        
        st.stop()
    
    # Opsiyonel veri durumu
    st.markdown("### 📊 Veri Durumu")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Zorunlu Veriler:**")
        for name, data in required_data.items():
            if data is not None:
                st.success(f"✅ {name}")
            else:
                st.error(f"❌ {name}")
    
    with col2:
        st.markdown("**Opsiyonel Veriler:**")
        for name, data in optional_data.items():
            if data is not None:
                st.success(f"✅ {name}")
            else:
                st.warning(f"⚠️ {name}")
    
    st.markdown("---")
    
    st.markdown("""
    ### 🎯 Yenilikler ve Özellikler
    
    **🆕 Gelişmiş Özellikler:**
    
    1. **📋 PO Yasak Kontrolü**
       - Yasak ürünleri otomatik filtreleme
       - Açık sipariş miktarlarını düşme
    
    2. **🎯 Detaylı KPI Hedefleri**
       - Marka + Mal Grubu bazında özel cover ve marj hedefleri
       - Dinamik hedef yönetimi
    
    3. **📦 Koli Bazında Sipariş**
       - Otomatik koli yuvarlaması
       - Adet ve koli bazında gösterim
    
    4. **✅ Ürün Durumu Kontrolü**
       - Pasif ürünleri otomatik çıkarma
       - İthal ürünler için farklı forward cover
    
    5. **🏪 Depo Bazlı Çıktı**
       - Her depo için ayrı sipariş listesi
       - Tedarikçi bazında gruplama
    """)

# ============================================
# 💵 ALIM SİPARİŞ HESAPLAMA
# ============================================
# ============================================
# 💵 ALIM SİPARİŞ HESAPLAMA - MAĞAZA BAZLI + GENLEŞTİRME + YASAK + KPI FC
# ============================================
elif menu == "💵 Alım Sipariş Hesaplama":
    st.title("💵 Alım Sipariş Hesaplama")
    st.markdown("---")
    
    # Veri kontrolleri
    required_data = {
        "Anlık Stok/Satış": st.session_state.anlik_stok_satis,
        "Depo Stok": st.session_state.depo_stok,
        "KPI": st.session_state.kpi,
        "Mağaza Master": st.session_state.magaza_master
    }
    
    missing_data = [name for name, data in required_data.items() if data is None]
    
    if missing_data:
        st.error(f"❌ Eksik veriler: {', '.join(missing_data)}")
        st.info("👉 Lütfen önce veri yükleme sayfasından gerekli verileri yükleyin.")
        st.stop()
    
    st.success("✅ Tüm gerekli veriler hazır!")
    
    # Opsiyonel veri bilgisi
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.po_yasak is not None:
            st.info("✅ PO Yasak aktif")
        else:
            st.warning("⚠️ PO Yasak yok")
    with col2:
        if st.session_state.urun_master is not None:
            st.info("✅ Ürün Master aktif")
        else:
            st.warning("⚠️ Ürün Master yok")
    
    st.markdown("---")
    
    # Parametreler
    st.subheader("🎯 Hesaplama Parametreleri")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        forward_cover = st.number_input(
            "Forward Cover",
            min_value=1.0,
            max_value=30.0,
            value=5.0,
            step=0.5,
            help="Hedef forward cover değeri (KPI'dan otomatik alınabilir)"
        )
    
    with col2:
        fc_ek = st.number_input(
            "Forward Cover Üretim Süresi (Safety Stock)",
            min_value=0,
            max_value=14,
            value=2,
            step=1,
            help="Forward cover'a eklenecek güvenlik stoğu"
        )
    
    with col3:
        depo_stok_threshold = st.number_input(
            "Min Depo Stok Eşiği",
            min_value=0,
            max_value=1000000,
            value=999,
            step=100,
            help="Bu değerden yüksek depo stoklu ürünler için PO hesaplanmaz"
        )
    
    st.markdown("---")
    
    # Cover Segment Matrix
    st.subheader("📊 Cover Segment Genişletme Katsayıları (Matris)")
    
    product_ranges = st.session_state.segmentation_params['product_ranges']
    store_ranges = st.session_state.segmentation_params['store_ranges']
    
    cover_segments = [f"{int(r[0])}-{int(r[1]) if r[1] != float('inf') else 'inf'}" for r in product_ranges]
    store_segments = [f"{int(r[0])}-{int(r[1]) if r[1] != float('inf') else 'inf'}" for r in store_ranges]
    
    def sort_segments(segments):
        def get_sort_key(seg):
            try:
                return int(seg.split('-')[0])
            except:
                return 9999
        return sorted(segments, key=get_sort_key)
    
    cover_segments_sorted = sort_segments(cover_segments)
    store_segments_sorted = sort_segments(store_segments)
    
    # İlk kez oluşturuluyorsa
    if st.session_state.cover_segment_matrix is None or \
       not isinstance(st.session_state.cover_segment_matrix, pd.DataFrame) or \
       len(st.session_state.cover_segment_matrix.columns) < 2:
        
        default_matrix = pd.DataFrame(1.0, index=cover_segments_sorted, columns=store_segments_sorted)
        
        for i, prod_seg in enumerate(cover_segments_sorted):
            prod_start = int(prod_seg.split('-')[0])
            if prod_start < 5:
                default_matrix.loc[prod_seg, :] = 1.2
            elif prod_start < 10:
                default_matrix.loc[prod_seg, :] = 1.1
            elif prod_start < 15:
                default_matrix.loc[prod_seg, :] = 1.05
            else:
                default_matrix.loc[prod_seg, :] = 0.75
        
        st.session_state.cover_segment_matrix = default_matrix
    
    # Editable matris göster
    matrix_display = st.session_state.cover_segment_matrix.reset_index()
    matrix_display.columns = ['Ürün Cover ↓ / Mağaza Cover →'] + list(st.session_state.cover_segment_matrix.columns)
    
    edited_cover_matrix_temp = st.data_editor(
        matrix_display,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        column_config={
            'Ürün Cover ↓ / Mağaza Cover →': st.column_config.TextColumn(
                "Ürün Cover ↓ / Mağaza Cover →",
                disabled=True,
                width="medium"
            )
        }
    )
    
    # Güvenli dönüşüm
    try:
        edited_df = pd.DataFrame(edited_cover_matrix_temp)
        first_col = edited_df.columns[0]
        edited_cover_matrix = edited_df.set_index(first_col)
    except:
        edited_cover_matrix = st.session_state.cover_segment_matrix
    
    if st.button("💾 Matris Kaydet"):
        st.session_state.cover_segment_matrix = edited_cover_matrix
        st.success("✅ Kaydedildi!")
    
    st.markdown("---")
    
    # HESAPLAMA
    if st.button("🚀 PO İhtiyacı Hesapla", type="primary", use_container_width=True):
        try:
            with st.spinner("📊 Hesaplama yapılıyor..."):
                
                start_time = time.time()
                
                # 1. VERİLERİ HAZIRLA
                anlik_df = st.session_state.anlik_stok_satis.copy()
                depo_df = st.session_state.depo_stok.copy()
                magaza_master = st.session_state.magaza_master.copy()
                kpi_df = st.session_state.kpi.copy()
                cover_matrix = st.session_state.cover_segment_matrix.copy()
                
                st.write("**📊 Veri Boyutları:**")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Anlık Stok/Satış", f"{len(anlik_df):,}")
                with col2:
                    st.metric("Depo Stok", f"{len(depo_df):,}")
                with col3:
                    st.metric("Mağaza Master", f"{len(magaza_master):,}")
                with col4:
                    st.metric("KPI", f"{len(kpi_df):,}")
                
                # Veri tiplerini düzelt
                anlik_df['urun_kod'] = anlik_df['urun_kod'].astype(str)
                anlik_df['magaza_kod'] = anlik_df['magaza_kod'].astype(str)
                depo_df['urun_kod'] = depo_df['urun_kod'].astype(str)
                depo_df['depo_kod'] = depo_df['depo_kod'].astype(str)
                magaza_master['magaza_kod'] = magaza_master['magaza_kod'].astype(str)
                magaza_master['depo_kod'] = magaza_master['depo_kod'].astype(str)
                
                # 2. MAĞAZA-DEPO EŞLEŞTİRMESİ
                st.info("🔗 Mağaza-Depo eşleştirmesi yapılıyor...")
                
                df = anlik_df.merge(
                    magaza_master[['magaza_kod', 'depo_kod']],
                    on='magaza_kod',
                    how='left'
                )
                
                eksik_depo = df['depo_kod'].isna().sum()
                if eksik_depo > 0:
                    st.warning(f"⚠️ {eksik_depo} satırda depo kodu bulunamadı (default '1' atanacak)")
                    df['depo_kod'] = df['depo_kod'].fillna('1')
                
                st.write(f"✅ Mağaza-Depo eşleşmesi: {len(df):,} satır")
                
                # 3. DEPO STOK EKLE
                st.info("📦 Depo stokları ekleniyor...")
                
                depo_stok_map = depo_df.groupby(['depo_kod', 'urun_kod'])['stok'].sum().reset_index()
                depo_stok_map.columns = ['depo_kod', 'urun_kod', 'depo_stok']
                
                df = df.merge(
                    depo_stok_map,
                    on=['depo_kod', 'urun_kod'],
                    how='left'
                )
                df['depo_stok'] = df['depo_stok'].fillna(0)
                
                st.write(f"✅ Depo stokları eklendi")
                
                # 4. KPI'DAN MIN DEĞER VE FORWARD COVER EKLE
                st.info("📋 KPI değerleri ekleniyor...")
                
                if st.session_state.urun_master is not None and 'mg' in st.session_state.urun_master.columns:
                    urun_master = st.session_state.urun_master[['urun_kod', 'mg']].copy()
                    urun_master['urun_kod'] = urun_master['urun_kod'].astype(str)
                    urun_master['mg'] = urun_master['mg'].astype(str)
                    
                    df = df.merge(urun_master, on='urun_kod', how='left')
                    df['mg'] = df['mg'].fillna('0')
                    
                    if 'mg_id' in kpi_df.columns:
                        kpi_lookup = kpi_df.copy()
                        kpi_lookup['mg_id'] = kpi_lookup['mg_id'].astype(str)
                        
                        # Min değer
                        if 'min_deger' in kpi_lookup.columns:
                            df = df.merge(
                                kpi_lookup[['mg_id', 'min_deger']],
                                left_on='mg',
                                right_on='mg_id',
                                how='left'
                            )
                            df['min_deger'] = df['min_deger'].fillna(0)
                            df.drop('mg_id', axis=1, inplace=True, errors='ignore')
                        else:
                            df['min_deger'] = 0
                        
                        # Forward Cover (KPI'dan)
                        if 'forward_cover' in kpi_lookup.columns:
                            fc_kpi = kpi_lookup[['mg_id', 'forward_cover']].copy()
                            fc_kpi.columns = ['mg_id', 'fc_kpi']
                            
                            df = df.merge(
                                fc_kpi,
                                left_on='mg',
                                right_on='mg_id',
                                how='left'
                            )
                            df['forward_cover_final'] = df['fc_kpi'].fillna(forward_cover)
                            df.drop(['mg_id', 'fc_kpi'], axis=1, inplace=True, errors='ignore')
                            
                            kpi_fc_count = (df['forward_cover_final'] != forward_cover).sum()
                            if kpi_fc_count > 0:
                                st.info(f"ℹ️ {kpi_fc_count:,} satır için KPI'dan FC alındı")
                        else:
                            df['forward_cover_final'] = forward_cover
                    else:
                        df['min_deger'] = 0
                        df['forward_cover_final'] = forward_cover
                else:
                    df['mg'] = '0'
                    df['min_deger'] = 0
                    df['forward_cover_final'] = forward_cover
                
                st.write(f"✅ KPI değerleri eklendi")
                
                # 5. PO YASAK KONTROLÜ
                if st.session_state.po_yasak is not None:
                    st.info("🚫 PO Yasak kontrolü yapılıyor...")
                    
                    po_yasak = st.session_state.po_yasak.copy()
                    po_yasak['urun_kodu'] = po_yasak['urun_kodu'].astype(str)
                    
                    df = df.merge(
                        po_yasak[['urun_kodu', 'yasak_durum', 'acik_siparis']],
                        left_on='urun_kod',
                        right_on='urun_kodu',
                        how='left'
                    )
                    
                    df['yasak_durum'] = df['yasak_durum'].fillna(0)
                    df['acik_siparis'] = df['acik_siparis'].fillna(0)
                    
                    yasak_sayisi = (df['yasak_durum'] == 1).sum()
                    df = df[df['yasak_durum'] != 1]
                    
                    if yasak_sayisi > 0:
                        st.warning(f"⚠️ {yasak_sayisi:,} yasak satır çıkarıldı")
                    
                    st.write(f"✅ PO Yasak kontrolü tamamlandı")
                else:
                    df['acik_siparis'] = 0
                
                # 6. SEGMENTASYON VE GENLEŞTİRME KATSAYISI
                st.info("📊 Segment ve genleştirme katsayıları hesaplanıyor...")
                
                # Ürün bazında toplam stok/satış
                urun_agg = anlik_df.groupby('urun_kod').agg({
                    'stok': 'sum',
                    'satis': 'sum'
                }).reset_index()
                urun_agg['urun_stok_satis'] = urun_agg['stok'] / urun_agg['satis'].replace(0, 1)
                
                # Mağaza bazında toplam stok/satış
                magaza_agg = anlik_df.groupby('magaza_kod').agg({
                    'stok': 'sum',
                    'satis': 'sum'
                }).reset_index()
                magaza_agg['magaza_stok_satis'] = magaza_agg['stok'] / magaza_agg['satis'].replace(0, 1)
                
                # Ürün segment ataması
                urun_agg['urun_segment'] = pd.cut(
                    urun_agg['urun_stok_satis'],
                    bins=[r[0] for r in product_ranges] + [product_ranges[-1][1]],
                    labels=cover_segments_sorted,
                    include_lowest=True
                ).astype(str)
                
                # Mağaza segment ataması
                magaza_agg['magaza_segment'] = pd.cut(
                    magaza_agg['magaza_stok_satis'],
                    bins=[r[0] for r in store_ranges] + [store_ranges[-1][1]],
                    labels=store_segments_sorted,
                    include_lowest=True
                ).astype(str)
                
                # Ana dataframe'e segment bilgilerini ekle
                df = df.merge(
                    urun_agg[['urun_kod', 'urun_segment']],
                    on='urun_kod',
                    how='left'
                )
                df['urun_segment'] = df['urun_segment'].fillna('0-4')
                
                df = df.merge(
                    magaza_agg[['magaza_kod', 'magaza_segment']],
                    on='magaza_kod',
                    how='left'
                )
                df['magaza_segment'] = df['magaza_segment'].fillna('0-4')
                
                # Genleştirme katsayısını matristen al
                if isinstance(cover_matrix, pd.DataFrame) and len(cover_matrix.columns) > 1:
                    matrix_long = cover_matrix.stack().reset_index()
                    matrix_long.columns = ['urun_segment', 'magaza_segment', 'genlestirme_katsayisi']
                    matrix_long['urun_segment'] = matrix_long['urun_segment'].astype(str)
                    matrix_long['magaza_segment'] = matrix_long['magaza_segment'].astype(str)
                    
                    df = df.merge(
                        matrix_long,
                        on=['urun_segment', 'magaza_segment'],
                        how='left'
                    )
                    df['genlestirme_katsayisi'] = df['genlestirme_katsayisi'].fillna(1.0)
                else:
                    df['genlestirme_katsayisi'] = 1.0
                
                st.write(f"✅ Genleştirme katsayıları eklendi")
                
                # 7-8. DEPO-ÜRÜN BAZINDA GRUPLA VE PO HESAPLA
                st.info("📊 Depo-Ürün bazında gruplama ve PO hesaplama...")
                
                # SMM bilgisini kontrol et
                if 'smm' not in df.columns:
                    df['smm'] = 0
                
                # Önce depo-ürün bazında topla
                po_sonuc = df.groupby(['depo_kod', 'urun_kod']).agg({
                    'satis': 'sum',
                    'stok': 'sum',
                    'yol': 'sum',
                    'depo_stok': 'first',
                    'min_deger': 'first',
                    'acik_siparis': 'sum',
                    'forward_cover_final': 'first',
                    'genlestirme_katsayisi': 'first',
                    'smm': 'first',
                    'magaza_kod': 'nunique'
                }).reset_index()
                
                po_sonuc.columns = [
                    'depo_kod', 'urun_kod', 'toplam_satis', 'toplam_magaza_stok', 
                    'toplam_yol', 'depo_stok', 'min_deger', 'toplam_acik_siparis',
                    'forward_cover', 'genlestirme', 'smm', 'magaza_sayisi'
                ]
                
                # Brüt ihtiyaç (TOPLAM bazında)
                po_sonuc['brut_ihtiyac'] = (
                    (po_sonuc['forward_cover'] + fc_ek) * 
                    po_sonuc['toplam_satis'] * 
                    po_sonuc['genlestirme']
                )
                
                # Net ihtiyaç = Brüt - Mağaza Stok - Yol - Depo Stok - Açık Sipariş
                po_sonuc['net_ihtiyac'] = (
                    po_sonuc['brut_ihtiyac'] - 
                    po_sonuc['toplam_magaza_stok'] - 
                    po_sonuc['toplam_yol'] - 
                    po_sonuc['depo_stok'] - 
                    po_sonuc['toplam_acik_siparis']
                )
                
                # Min kontrolü (toplam mağaza stoku < min ise)
                po_sonuc['min_ihtiyac'] = np.where(
                    po_sonuc['min_deger'] > po_sonuc['toplam_magaza_stok'],
                    po_sonuc['min_deger'] - po_sonuc['toplam_magaza_stok'],
                    0
                )
                
                # PO ihtiyacı
                po_sonuc['po_ihtiyac'] = np.maximum(po_sonuc['net_ihtiyac'], po_sonuc['min_ihtiyac'])
                po_sonuc['po_ihtiyac'] = po_sonuc['po_ihtiyac'].clip(lower=0)
                
                st.write(f"✅ PO ihtiyacı hesaplandı: {len(po_sonuc):,} depo-ürün kombinasyonu")
                
                # DEPO STOK EŞİĞİ KONTROLÜ
                yuksek_stok_sayisi = (po_sonuc['depo_stok'] > depo_stok_threshold).sum()
                po_sonuc.loc[po_sonuc['depo_stok'] > depo_stok_threshold, 'po_ihtiyac'] = 0
                
                if yuksek_stok_sayisi > 0:
                    st.info(f"ℹ️ {yuksek_stok_sayisi:,} üründe depo stok > {depo_stok_threshold}, PO sıfırlandı")
                
                po_sonuc_pozitif = po_sonuc[po_sonuc['po_ihtiyac'] > 0].copy()
                
                for col in ['po_ihtiyac', 'brut_ihtiyac', 'net_ihtiyac', 'toplam_satis', 'toplam_magaza_stok', 'toplam_yol', 'depo_stok', 'toplam_acik_siparis']:
                    if col in po_sonuc_pozitif.columns:
                        po_sonuc_pozitif[col] = po_sonuc_pozitif[col].round().astype(int)
                
                end_time = time.time()
                
                # 9. KAYDET
                st.session_state.alim_siparis_sonuc = po_sonuc_pozitif.copy()
                
                st.success(f"✅ Hesaplama tamamlandı!")
                st.balloons()
                
                # ============================================
                # 📊 ÖZET METRİKLER TABLOSU
                # ============================================
                st.markdown("---")
                st.subheader("📊 Hesaplama Özet Metrikleri")
                
                # PO Tutarı hesapla (PO Adet × SMM)
                if 'smm' in po_sonuc_pozitif.columns:
                    po_sonuc_pozitif['po_tutar'] = po_sonuc_pozitif['po_ihtiyac'] * po_sonuc_pozitif['smm']
                    toplam_po_tutar = po_sonuc_pozitif['po_tutar'].sum()
                else:
                    toplam_po_tutar = 0
                
                # SMM bilgisini ana veri setinden al (tüm sistem için)
                if 'smm' in po_sonuc.columns:
                    po_sonuc['magaza_stok_tutar'] = po_sonuc['toplam_magaza_stok'] * po_sonuc['smm']
                    po_sonuc['depo_stok_tutar'] = po_sonuc['depo_stok'] * po_sonuc['smm']
                    po_sonuc['yol_tutar'] = po_sonuc['toplam_yol'] * po_sonuc['smm']
                    po_sonuc['acik_siparis_tutar'] = po_sonuc['toplam_acik_siparis'] * po_sonuc['smm']
                    po_sonuc['satis_tutar'] = po_sonuc['toplam_satis'] * po_sonuc['smm']
                    
                    # Tüm sistem tutarları
                    toplam_magaza_stok_tutar = po_sonuc['magaza_stok_tutar'].sum()
                    toplam_depo_stok_tutar = po_sonuc['depo_stok_tutar'].sum()
                    toplam_yol_tutar = po_sonuc['yol_tutar'].sum()
                    toplam_acik_sip_tutar = po_sonuc['acik_siparis_tutar'].sum()
                    toplam_satis_tutar = po_sonuc['satis_tutar'].sum()
                else:
                    toplam_magaza_stok_tutar = 0
                    toplam_depo_stok_tutar = 0
                    toplam_yol_tutar = 0
                    toplam_acik_sip_tutar = 0
                    toplam_satis_tutar = 0
                
                # Metrikleri hesapla - TÜM SİSTEM
                algoritma_suresi = end_time - start_time
                toplam_po_adet = po_sonuc_pozitif['po_ihtiyac'].sum()
                
                toplam_magaza_stok_sistem = po_sonuc['toplam_magaza_stok'].sum()
                toplam_depo_stok_sistem = po_sonuc['depo_stok'].sum()
                toplam_yol_sistem = po_sonuc['toplam_yol'].sum()
                toplam_acik_sip_sistem = po_sonuc['toplam_acik_siparis'].sum()
                toplam_satis_sistem = po_sonuc['toplam_satis'].sum()
                urun_sayisi_sistem = po_sonuc['urun_kod'].nunique()
                
                # PO Hesaplananlar
                urun_sayisi_po = po_sonuc_pozitif['urun_kod'].nunique()
                depo_sayisi = po_sonuc_pozitif['depo_kod'].nunique()
                
                # Özet tablosu oluştur - ADET ve TUTAR kolonları
                ozet_data = {
                    'Metrik': [
                        '📦 PO İhtiyacı',
                        '🏪 Mağaza Stok (Tüm Sistem)',
                        '🏭 Depo Stok (Tüm Sistem)',
                        '🚚 Yol (Tüm Sistem)',
                        '📋 Açık Sipariş (Tüm Sistem)',
                        '💵 Satış / Ciro (Tüm Sistem)',
                        '🏷️ Ürün Sayısı (Tüm Sistem)',
                        '🏷️ Ürün Sayısı (PO Hesaplanan)',
                        '🏪 Depo Sayısı',
                        '📊 Depo-Ürün Kombinasyonu',
                        '⏱️ Algoritma Süresi'
                    ],
                    'Adet': [
                        f"{toplam_po_adet:,.0f}",
                        f"{toplam_magaza_stok_sistem:,.0f}",
                        f"{toplam_depo_stok_sistem:,.0f}",
                        f"{toplam_yol_sistem:,.0f}",
                        f"{toplam_acik_sip_sistem:,.0f}",
                        f"{toplam_satis_sistem:,.0f}",
                        f"{urun_sayisi_sistem:,}",
                        f"{urun_sayisi_po:,}",
                        f"{depo_sayisi}",
                        f"{len(po_sonuc_pozitif):,}",
                        f"{algoritma_suresi:.2f} sn"
                    ],
                    'Tutar (₺)': [
                        f"{toplam_po_tutar:,.2f}",
                        f"{toplam_magaza_stok_tutar:,.2f}",
                        f"{toplam_depo_stok_tutar:,.2f}",
                        f"{toplam_yol_tutar:,.2f}",
                        f"{toplam_acik_sip_tutar:,.2f}",
                        f"{toplam_satis_tutar:,.2f}",
                        "-",
                        "-",
                        "-",
                        "-",
                        "-"
                    ]
                }
                
                ozet_df = pd.DataFrame(ozet_data)
                
                # Tabloyu göster
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.dataframe(
                        ozet_df,
                        use_container_width=True,
                        hide_index=True,
                        height=450
                    )
                
                with col2:
                    st.metric(
                        "🎯 Toplam PO Adet", 
                        f"{toplam_po_adet:,.0f}"
                    )
                    
                    st.metric(
                        "💰 Toplam PO Tutar", 
                        f"₺{toplam_po_tutar:,.0f}"
                    )
                    
                    st.metric(
                        "⚡ İşlem Süresi", 
                        f"{algoritma_suresi:.2f} sn"
                    )
                    
                    toplam_stok_sistemi = toplam_magaza_stok_sistem + toplam_yol_sistem + toplam_depo_stok_sistem
                    st.metric(
                        "💼 Toplam Sistem Stok",
                        f"{toplam_stok_sistemi:,.0f}"
                    )
                    
                    # PO oranı
                    if urun_sayisi_sistem > 0:
                        po_oran = (urun_sayisi_po / urun_sayisi_sistem) * 100
                        st.metric(
                            "📊 PO Gereken Ürün Oranı",
                            f"%{po_oran:.1f}"
                        )
                
                st.markdown("---")
                
                # DEPO BAZINDA ÖZET
                st.subheader("🏪 Depo Bazında Özet")
                
                depo_ozet = po_sonuc_pozitif.groupby('depo_kod').agg({
                    'po_ihtiyac': 'sum',
                    'urun_kod': 'nunique'
                }).reset_index()
                
                if 'po_tutar' in po_sonuc_pozitif.columns:
                    depo_tutar = po_sonuc_pozitif.groupby('depo_kod')['po_tutar'].sum().reset_index()
                    depo_ozet = depo_ozet.merge(depo_tutar, on='depo_kod', how='left')
                    depo_ozet.columns = ['Depo Kodu', 'Toplam PO Adet', 'Ürün Sayısı', 'Toplam PO Tutar']
                else:
                    depo_ozet.columns = ['Depo Kodu', 'Toplam PO Adet', 'Ürün Sayısı']
                
                depo_ozet = depo_ozet.sort_values('Toplam PO Adet', ascending=False)
                
                st.dataframe(depo_ozet, use_container_width=True, hide_index=True)
                
                # DETAY TABLO
                st.markdown("---")
                st.subheader("📋 PO Detayı (Top 1000)")
                
                display_df = po_sonuc_pozitif.sort_values('po_ihtiyac', ascending=False).head(1000)
                st.dataframe(display_df, use_container_width=True, height=400)
                
                # EXPORT
                st.markdown("---")
                col1, col2 = st.columns(2)
                
                with col1:
                    csv_data = po_sonuc_pozitif.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 Tüm PO İndir (CSV)",
                        data=csv_data,
                        file_name=f"po_ihtiyac_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col2:
                    ozet_csv = depo_ozet.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 Depo Özeti İndir (CSV)",
                        data=ozet_csv,
                        file_name=f"po_depo_ozet_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
        
        except Exception as e:
            st.error(f"❌ Hata: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

# ============================================
# 📊 ALIM SİPARİŞ RAPORLARI
# ============================================
                    
# ============================================
# 📊 ALIM SİPARİŞ RAPORLARI
# ============================================
elif menu == "📊 Alım Sipariş Raporları":
    st.title("📊 Alım Sipariş Raporları")
    st.markdown("---")
    
    if st.session_state.alim_siparis_sonuc is None:
        st.warning("⚠️ Henüz alım sipariş hesaplaması yapılmadı!")
        st.info("Lütfen önce 'Alım Sipariş Hesaplama' menüsünden hesaplama yapın.")
        st.stop()
    
    sonuc_df = st.session_state.alim_siparis_sonuc.copy()
    
    # PO ihtiyacı kolonu
    if 'po_ihtiyac' in sonuc_df.columns:
        alim_column = 'po_ihtiyac'
    elif 'alim_siparis_final' in sonuc_df.columns:
        alim_column = 'alim_siparis_final'
    else:
        alim_column = 'alim_siparis'
    
    # Sadece alım > 0 olanlar
    alim_df = sonuc_df[sonuc_df[alim_column] > 0].copy()
    
    if len(alim_df) == 0:
        st.info("ℹ️ Alım sipariş ihtiyacı olan ürün bulunamadı.")
        st.stop()
    
    # Genel özet
    st.subheader("📈 Genel Özet")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📦 Toplam PO", f"{alim_df[alim_column].sum():,.0f}")
    
    with col2:
        st.metric("🏷️ Ürün Sayısı", f"{alim_df['urun_kod'].nunique()}")
    
    with col3:
        if 'depo_kod' in alim_df.columns:
            st.metric("🏪 Depo Sayısı", f"{alim_df['depo_kod'].nunique()}")
    
    with col4:
        if 'toplam_acik_siparis' in alim_df.columns:
            acik_dusülen = alim_df['toplam_acik_siparis'].sum()
            st.metric("📋 Açık Sipariş Düşüldü", f"{acik_dusülen:,.0f}")
    
    st.markdown("---")
    
    # Tab'lar
    tab1, tab2, tab3 = st.tabs(["🏪 Depo Analizi", "📊 Detay Tablo", "📈 Özet İstatistikler"])
    
    # DEPO ANALİZİ
    with tab1:
        st.subheader("🏪 Depo Bazında Analiz")
        
        if 'depo_kod' in alim_df.columns:
            depo_analiz = alim_df.groupby('depo_kod').agg({
                alim_column: 'sum',
                'urun_kod': 'nunique',
                'toplam_satis': 'sum',
                'toplam_magaza_stok': 'sum',
                'depo_stok': 'sum'
            }).reset_index()
            
            depo_analiz.columns = ['Depo Kodu', 'Toplam PO', 'Ürün Sayısı', 'Toplam Satış', 'Mağaza Stok', 'Depo Stok']
            depo_analiz = depo_analiz.sort_values('Toplam PO', ascending=False)
            
            st.dataframe(
                depo_analiz.style.format({
                    'Toplam PO': '{:,.0f}',
                    'Ürün Sayısı': '{:.0f}',
                    'Toplam Satış': '{:,.0f}',
                    'Mağaza Stok': '{:,.0f}',
                    'Depo Stok': '{:,.0f}'
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("ℹ️ Depo bilgisi bulunamadı")
    
    # DETAY TABLO
    with tab2:
        st.subheader("📋 PO Detay Tablosu")
        
        display_cols = ['depo_kod', 'urun_kod', alim_column, 'toplam_satis', 
                       'toplam_magaza_stok', 'toplam_yol', 'depo_stok']
        
        if 'toplam_acik_siparis' in alim_df.columns:
            display_cols.append('toplam_acik_siparis')
        
        if 'magaza_sayisi' in alim_df.columns:
            display_cols.append('magaza_sayisi')
        
        # Sadece mevcut kolonları al
        display_cols = [col for col in display_cols if col in alim_df.columns]
        
        display_df = alim_df[display_cols].sort_values(alim_column, ascending=False)
        
        st.dataframe(
            display_df.style.format({
                alim_column: '{:,.0f}',
                'toplam_satis': '{:,.0f}',
                'toplam_magaza_stok': '{:,.0f}',
                'toplam_yol': '{:,.0f}',
                'depo_stok': '{:,.0f}',
                'toplam_acik_siparis': '{:,.0f}',
                'magaza_sayisi': '{:.0f}'
            }),
            use_container_width=True,
            height=500
        )
    
    # ÖZET İSTATİSTİKLER
    with tab3:
        st.subheader("📈 Özet İstatistikler")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**PO İhtiyacı Dağılımı:**")
            st.write(f"- Ortalama: {alim_df[alim_column].mean():,.0f}")
            st.write(f"- Medyan: {alim_df[alim_column].median():,.0f}")
            st.write(f"- Min: {alim_df[alim_column].min():,.0f}")
            st.write(f"- Max: {alim_df[alim_column].max():,.0f}")
        
        with col2:
            st.write("**Stok Durumu:**")
            if 'toplam_magaza_stok' in alim_df.columns:
                st.write(f"- Toplam Mağaza Stok: {alim_df['toplam_magaza_stok'].sum():,.0f}")
            if 'depo_stok' in alim_df.columns:
                st.write(f"- Toplam Depo Stok: {alim_df['depo_stok'].sum():,.0f}")
            if 'toplam_yol' in alim_df.columns:
                st.write(f"- Toplam Yol: {alim_df['toplam_yol'].sum():,.0f}")
    
    # Export
    st.markdown("---")
    csv_data = alim_df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 Tüm Veriyi İndir (CSV)",
        data=csv_data,
        file_name=f"po_rapor_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        use_container_width=True
    )
# ============================================
# 📦 DEPO BAZLI SİPARİŞ
# ============================================
elif menu == "📦 Depo Bazlı Sipariş":
    st.title("📦 Depo Bazlı Sipariş Listeleri")
    st.markdown("---")
    
    if st.session_state.alim_siparis_sonuc is None:
        st.warning("⚠️ Henüz alım sipariş hesaplaması yapılmadı!")
        st.info("Lütfen önce 'Alım Sipariş Hesaplama' menüsünden hesaplama yapın.")
        st.stop()
    
    sonuc_df = st.session_state.alim_siparis_sonuc.copy()
    
    # PO ihtiyacı kolonu
    if 'po_ihtiyac' in sonuc_df.columns:
        alim_column = 'po_ihtiyac'
    elif 'alim_siparis_final' in sonuc_df.columns:
        alim_column = 'alim_siparis_final'
    else:
        alim_column = 'alim_siparis'
    
    # Pozitif alımları filtrele
    alim_df = sonuc_df[sonuc_df[alim_column] > 0].copy()
    
    if len(alim_df) == 0:
        st.info("ℹ️ Alım sipariş ihtiyacı olan ürün bulunamadı.")
        st.stop()
    
    # Depo kodu yoksa default ata
    if 'depo_kod' not in alim_df.columns:
        alim_df['depo_kod'] = 'D001'
        st.info("ℹ️ Depo kodu bulunamadı, tüm siparişler D001 olarak gösteriliyor")
    
    # Depo seçimi
    depo_listesi = sorted(alim_df['depo_kod'].dropna().unique())
    
    col1, col2 = st.columns([2, 3])
    with col1:
        selected_depo = st.selectbox(
            "📍 Depo Seçin",
            options=['Tümü'] + list(depo_listesi),
            key="depo_select"
        )
    
    # Seçili depoya göre filtrele
    if selected_depo != 'Tümü':
        display_df = alim_df[alim_df['depo_kod'] == selected_depo].copy()
        st.subheader(f"📦 {selected_depo} Deposu Sipariş Listesi")
    else:
        display_df = alim_df.copy()
        st.subheader("📦 Tüm Depolar Sipariş Listesi")
    
    # Özet metrikler
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        toplam_adet = display_df[alim_column].sum()
        st.metric("📦 Toplam PO", f"{toplam_adet:,.0f}")
    
    with col2:
        urun_sayisi = display_df['urun_kod'].nunique()
        st.metric("🏷️ Ürün Sayısı", f"{urun_sayisi}")
    
    with col3:
        if 'toplam_satis' in display_df.columns:
            toplam_satis = display_df['toplam_satis'].sum()
            st.metric("💰 Toplam Satış", f"{toplam_satis:,.0f}")
    
    with col4:
        if 'magaza_sayisi' in display_df.columns:
            toplam_magaza = display_df['magaza_sayisi'].sum()
            st.metric("🏪 Mağaza-Ürün", f"{toplam_magaza:,}")
    
    st.markdown("---")
    
    # Detaylı tablo
    st.subheader("📋 Sipariş Detayı")
    
    # Gösterilecek sütunları belirle
    display_cols = ['urun_kod', alim_column, 'toplam_satis', 'toplam_magaza_stok', 
                   'toplam_yol', 'depo_stok']
    
    if 'toplam_acik_siparis' in display_df.columns:
        display_cols.append('toplam_acik_siparis')
    
    if 'magaza_sayisi' in display_df.columns:
        display_cols.append('magaza_sayisi')
    
    if 'depo_kod' in display_df.columns and selected_depo == 'Tümü':
        display_cols.insert(0, 'depo_kod')
    
    # Sadece mevcut sütunları göster
    display_cols = [col for col in display_cols if col in display_df.columns]
    
    final_df = display_df[display_cols].sort_values(alim_column, ascending=False)
    
    # Sütun isimlerini düzenle
    column_rename = {
        'depo_kod': 'Depo',
        'urun_kod': 'Ürün Kodu',
        alim_column: 'PO İhtiyacı',
        'toplam_satis': 'Toplam Satış',
        'toplam_magaza_stok': 'Mağaza Stok',
        'toplam_yol': 'Yol',
        'depo_stok': 'Depo Stok',
        'toplam_acik_siparis': 'Açık Sipariş',
        'magaza_sayisi': 'Mağaza Sayısı'
    }
    
    final_df = final_df.rename(columns=column_rename)
    
    # Formatla ve göster
    format_dict = {
        'PO İhtiyacı': '{:,.0f}',
        'Toplam Satış': '{:,.0f}',
        'Mağaza Stok': '{:,.0f}',
        'Yol': '{:,.0f}',
        'Depo Stok': '{:,.0f}',
        'Açık Sipariş': '{:,.0f}',
        'Mağaza Sayısı': '{:.0f}'
    }
    
    # Sadece mevcut sütunları formatla
    format_dict = {k: v for k, v in format_dict.items() if k in final_df.columns}
    
    st.dataframe(
        final_df.style.format(format_dict),
        use_container_width=True,
        height=500
    )
    
    # Export
    st.markdown("---")
    st.subheader("📥 Dışa Aktar")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Mevcut görünümü indir
        csv_data = final_df.to_csv(index=False, encoding='utf-8-sig')
        filename = f"po_siparis_{selected_depo}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv"
        
        st.download_button(
            label="📥 Bu Listeyi İndir (CSV)",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # Tüm depoları indir
        if selected_depo != 'Tümü':
            tum_csv = alim_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Tüm Depolar (CSV)",
                data=tum_csv,
                file_name=f"po_tum_depolar_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )







