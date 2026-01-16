import streamlit as st
import pandas as pd
import time
import numpy as np
import io

# Sayfa config
st.set_page_config(
    page_title="Retail Sevkiyat Planlama",
    page_icon="📦", 
    layout="wide"
)

# ============================================
# SESSION STATE BAŞLATMA - TEK SEFERDE
# ============================================

# Veri dosyaları
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

# Segmentasyon parametreleri - TEK TANIMLA
if 'segmentation_params' not in st.session_state:
    st.session_state.segmentation_params = {
        'product_ranges': [(0, 4), (5, 8), (9, 12), (12, 15), (15, 20), (20, float('inf'))],
        'store_ranges': [(0, 4), (5, 8), (9, 12), (12, 15), (15, 20), (20, float('inf'))]
    }

# Matrisler
if 'initial_matris' not in st.session_state:
    st.session_state.initial_matris = None
if 'target_matrix' not in st.session_state:
    st.session_state.target_matrix = None
if 'sisme_orani' not in st.session_state:
    st.session_state.sisme_orani = None
if 'genlestirme_orani' not in st.session_state:
    st.session_state.genlestirme_orani = None
if 'min_oran' not in st.session_state:
    st.session_state.min_oran = None

# Diğer
if 'siralama_data' not in st.session_state:
    st.session_state.siralama_data = None
if 'sevkiyat_sonuc' not in st.session_state:
    st.session_state.sevkiyat_sonuc = None
if 'yeni_urun_listesi' not in st.session_state:
    st.session_state.yeni_urun_listesi = None

# Hedef Matris'ten gelen segmentler (otomatik kaydedilecek)
if 'urun_segment_map' not in st.session_state:
    st.session_state.urun_segment_map = None
if 'magaza_segment_map' not in st.session_state:
    st.session_state.magaza_segment_map = None
if 'prod_segments' not in st.session_state:
    st.session_state.prod_segments = None
if 'store_segments' not in st.session_state:
    st.session_state.store_segments = None

# Sidebar menü 
menu = st.sidebar.radio(
    "Menü",
    ["🏠 Ana Sayfa", "🫧 Segmentasyon", "🎲 Hedef Matris", 
     "🔢 Sıralama", "📐 Hesaplama", "📈 Raporlar", "💾 Master Data"]
)

# ============================================
# 🏠 ANA SAYFA
# ============================================
if menu == "🏠 Ana Sayfa":
    st.title("🌟 Sevkiyat Planlama Sistemi")
    st.markdown("---")
    
    st.info("""
    **📋 Veri Yükleme:** Sol menüden "Veri Yükleme" sayfasına gidin.
    **💵 Alım Sipariş:** Hesaplama sonrası "Alım Sipariş (PO)" sayfasına gidin.
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➡️ Veri Yükleme Sayfasına Git", width='stretch'):
            st.switch_page("pages/0_Veri_Yukleme.py")
    with col2:
        if st.button("➡️ Alım Sipariş Sayfasına Git", width='stretch'):
            st.switch_page("pages/4_PO.py")
    
    st.markdown("---")
    
# ============================================
# 🫧 SEGMENTASYON AYARLARI - DÜZELTİLMİŞ
# ============================================
elif menu == "🫧 Segmentasyon":
    st.title("🫧 Segmentasyon")
    st.markdown("---")
    
    st.info("**Stok/Satış oranına göre** ürün ve mağazaları gruplandırma (Mağaza Stok / Toplam Satış)")
    
    if st.session_state.anlik_stok_satis is None:
        st.warning("⚠️ Önce 'Veri Yükleme' bölümünden anlık stok/satış verisini yükleyin!")
        st.stop()
    
    # Ürün bazında toplam stok/satış hesapla
    data = st.session_state.anlik_stok_satis.copy()
    
    # Ürün bazında gruplama
    urun_aggregated = data.groupby('urun_kod').agg({
        'stok': 'sum',
        'yol': 'sum',
        'satis': 'sum',
        'ciro': 'sum'
    }).reset_index()
    urun_aggregated['stok_satis_orani'] = urun_aggregated['stok'] / urun_aggregated['satis'].replace(0, 1)
    
    if st.session_state.urun_master is not None:
        urun_master = st.session_state.urun_master[['urun_kod', 'marka_kod']].copy()
        urun_master['urun_kod'] = urun_master['urun_kod'].astype(str)
        urun_aggregated['urun_kod'] = urun_aggregated['urun_kod'].astype(str)
        urun_aggregated = urun_aggregated.merge(urun_master, on='urun_kod', how='left')
    else:
        urun_aggregated['marka_kod'] = 'Bilinmiyor'
    
    # Mağaza bazında gruplama
    magaza_aggregated = data.groupby('magaza_kod').agg({
        'stok': 'sum',
        'yol': 'sum',
        'satis': 'sum',
        'ciro': 'sum'
    }).reset_index()
    magaza_aggregated['stok_satis_orani'] = magaza_aggregated['stok'] / magaza_aggregated['satis'].replace(0, 1)
    
    st.markdown("---")
    
    # Ürün segmentasyonu
    st.subheader("🏷️ Ürün Segmentasyonu")
    
    use_default_product = st.checkbox("Varsayılan aralıkları kullan (Ürün)", value=True, key="seg_use_default_product")
    
    if use_default_product:
        st.write("**Varsayılan Aralıklar**: 0-4, 5-8, 9-12, 12-15, 15-20, 20+")
        product_ranges = [(0, 4), (5, 8), (9, 12), (12, 15), (15, 20), (20, float('inf'))]
    else:
        st.write("Özel aralıklar tanımlayın:")
        num_ranges = st.number_input("Kaç aralık?", min_value=2, max_value=10, value=6, key="seg_num_ranges_product")
        
        product_ranges = []
        for i in range(num_ranges):
            col1, col2 = st.columns(2)
            with col1:
                min_val = st.number_input(f"Aralık {i+1} - Min", value=i*5, key=f"prod_min_{i}")
            with col2:
                max_val = st.number_input(f"Aralık {i+1} - Max", value=(i+1)*5 if i < num_ranges-1 else 999, key=f"prod_max_{i}")
            product_ranges.append((min_val, max_val))
    
    # Ürün segment labels
    product_labels = [f"{int(r[0])}-{int(r[1]) if r[1] != float('inf') else 'inf'}" for r in product_ranges]
    
    # Segmentasyon uygula
    temp_prod = urun_aggregated.copy()
    
    # SATIŞ OLMAYAN ÜRÜNLER İÇİN DÜZELTME: cover inf olan ürünleri 12-15'e ata
    temp_prod['stok_satis_orani_adj'] = temp_prod['stok_satis_orani'].replace([np.inf, -np.inf], 13.5)
    temp_prod.loc[temp_prod['satis'] == 0, 'stok_satis_orani_adj'] = 13.5  # Satış 0 ise 12-15'e at
    
    temp_prod['segment'] = pd.cut(
        temp_prod['stok_satis_orani_adj'], 
        bins=[r[0] for r in product_ranges] + [product_ranges[-1][1]],
        labels=product_labels,
        include_lowest=True
    )
    
    st.write("**Ürün Dağılımı:**")
    segment_dist = temp_prod['segment'].value_counts().sort_index()
    col1, col2 = st.columns([1, 2])
    with col1:
        st.dataframe(segment_dist, width='content', height=200)
    with col2:
        st.bar_chart(segment_dist)
    
    st.markdown("---")
    
    # Mağaza segmentasyonu
    st.subheader("🏪 Mağaza Segmentasyonu")
    
    use_default_store = st.checkbox("Varsayılan aralıkları kullan (Mağaza)", value=True, key="seg_use_default_store")
    
    if use_default_store:
        st.write("**Varsayılan Aralıklar**: 0-4, 5-8, 9-12, 12-15, 15-20, 20+")
        store_ranges = [(0, 4), (5, 8), (9, 12), (12, 15), (15, 20), (20, float('inf'))]
    else:
        st.write("Özel aralıklar tanımlayın:")
        num_ranges_store = st.number_input("Kaç aralık?", min_value=2, max_value=10, value=6, key="store_ranges")
        
        store_ranges = []
        for i in range(num_ranges_store):
            col1, col2 = st.columns(2)
            with col1:
                min_val = st.number_input(f"Aralık {i+1} - Min", value=i*5, key=f"store_min_{i}")
            with col2:
                max_val = st.number_input(f"Aralık {i+1} - Max", value=(i+1)*5 if i < num_ranges_store-1 else 999, key=f"store_max_{i}")
            store_ranges.append((min_val, max_val))
    
    # Mağaza segment labels
    store_labels = [f"{int(r[0])}-{int(r[1]) if r[1] != float('inf') else 'inf'}" for r in store_ranges]
    
    # Segmentasyon uygula
    temp_store = magaza_aggregated.copy()
    
    # SATIŞ OLMAYAN MAĞAZALAR İÇİN DÜZELTME: cover inf olanları 12-15'e ata
    temp_store['stok_satis_orani_adj'] = temp_store['stok_satis_orani'].replace([np.inf, -np.inf], 13.5)
    temp_store.loc[temp_store['satis'] == 0, 'stok_satis_orani_adj'] = 13.5  # Satış 0 ise 12-15'e at
    
    temp_store['segment'] = pd.cut(
        temp_store['stok_satis_orani_adj'], 
        bins=[r[0] for r in store_ranges] + [store_ranges[-1][1]],
        labels=store_labels,
        include_lowest=True
    )
    
    st.write("**Mağaza Dağılımı:**")
    segment_dist_store = temp_store['segment'].value_counts().sort_index()
    col1, col2 = st.columns([1, 2])
    with col1:
        st.dataframe(segment_dist_store, width='content', height=200)
    with col2:
        st.bar_chart(segment_dist_store)
    
    st.markdown("---")
    
    # Kaydet butonu
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("💾 Segmentasyonu Kaydet", type="primary"):
            st.session_state.segmentation_params = {
                'product_ranges': product_ranges,
                'store_ranges': store_ranges
            }
            # Seg_ prefix ekle - Excel tarih sorunu çözümü
            st.session_state.prod_segments = ["Seg_" + lbl for lbl in product_labels]
            st.session_state.store_segments = ["Seg_" + lbl for lbl in store_labels]
            
            # String key'lerle kaydet - veri tipi uyumu için
            st.session_state.urun_segment_map = {str(k).strip(): "Seg_" + str(v) for k, v in temp_prod.set_index('urun_kod')['segment'].to_dict().items()}
            st.session_state.magaza_segment_map = {str(k).strip(): "Seg_" + str(v) for k, v in temp_store.set_index('magaza_kod')['segment'].to_dict().items()}
            
            st.success(f"✅ Ayarlar kaydedildi! Ürün map: {len(st.session_state.urun_segment_map)}, Mağaza map: {len(st.session_state.magaza_segment_map)}")
    with col2:
        st.info("ℹ️ Kaydetmeseniz de default değerler kullanılacaktır.")
            
    st.markdown("---")
    
    # ============================================
    # DETAY VERİLERİNİ HAZIRLA (YENİ EKLENEN KISIM)
    # ============================================
    # Ürün detayı
    urun_detail = temp_prod.copy()
    if 'marka_kod' in urun_detail.columns:
        urun_detail = urun_detail[['urun_kod', 'marka_kod', 'stok', 'satis', 'stok_satis_orani', 'segment']]
        urun_detail.columns = ['Ürün Kodu', 'Marka Kodu', 'Toplam Stok', 'Toplam Satış', 'Stok/Satış Oranı', 'Segment']
    else:
        urun_detail = urun_detail[['urun_kod', 'stok', 'satis', 'stok_satis_orani', 'segment']]
        urun_detail.columns = ['Ürün Kodu', 'Toplam Stok', 'Toplam Satış', 'Stok/Satış Oranı', 'Segment']
    
    # Mağaza detayı
    magaza_detail = temp_store.copy()
    magaza_detail = magaza_detail[['magaza_kod', 'stok', 'satis', 'stok_satis_orani', 'segment']]
    magaza_detail.columns = ['Mağaza Kodu', 'Toplam Stok', 'Toplam Satış', 'Stok/Satış Oranı', 'Segment']
    
    # ============================================
    # HER İKİSİNİ BİRLİKTE İNDİR
    # ============================================
    st.subheader("📥 Tüm Segmentasyon Verilerini İndir")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Excel formatında (iki sheet)
        if st.button("📊 Excel İndir (Ürün + Mağaza)", key="seg_export_excel"):
            try:
                from io import BytesIO
                
                # Excel writer oluştur
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    urun_detail.to_excel(writer, sheet_name='Ürün Segmentasyon', index=False)
                    magaza_detail.to_excel(writer, sheet_name='Mağaza Segmentasyon', index=False)
                
                output.seek(0)
                
                st.download_button(
                    label="⬇️ Excel Dosyasını İndir",
                    data=output.getvalue(),
                    file_name="segmentasyon_tam_detay.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except ImportError:
                st.error("❌ Excel export için 'openpyxl' kütüphanesi gerekli. Lütfen yükleyin: pip install openpyxl")
    
    with col2:
        # ZIP formatında (iki CSV)
        if st.button("📦 ZIP İndir (2 CSV)", key="seg_export_zip"):
            import zipfile
            from io import BytesIO
            
            zip_buffer = BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Ürün CSV
                urun_csv = urun_detail.to_csv(index=False, encoding='utf-8-sig')
                zip_file.writestr('urun_segmentasyon.csv', urun_csv)
                
                # Mağaza CSV
                magaza_csv = magaza_detail.to_csv(index=False, encoding='utf-8-sig')
                zip_file.writestr('magaza_segmentasyon.csv', magaza_csv)
            
            zip_buffer.seek(0)
            
            st.download_button(
                label="⬇️ ZIP Dosyasını İndir",
                data=zip_buffer.getvalue(),
                file_name="segmentasyon_detay.zip",
                mime="application/zip"
            )

# ============================================
# 🎲 HEDEF MATRİS 
# ============================================

# ============================================
# 🎲 HEDEF MATRİS - DÜZENLENEBİLİR VERSİYON (ADIM 2)
# ============================================
elif menu == "🎲 Hedef Matris":
    st.title("🎲 Hedef Matris Parametreleri")
    st.markdown("---")
    
    # Segmentleri kontrol et
    if (st.session_state.prod_segments is None or 
        st.session_state.store_segments is None):
        st.warning("⚠️ Önce 'Segmentasyon' bölümüne gidin ve segmentasyonu kaydedin!")
        st.stop()
    
    prod_segments = st.session_state.prod_segments  # Sütunlar
    store_segments = st.session_state.store_segments  # Satırlar
    
    st.info(f"📏 Matris Boyutu: {len(store_segments)} Mağaza Segment × {len(prod_segments)} Ürün Segment")
    st.success("✨ **Artık hücrelere tıklayarak değerleri düzenleyebilirsiniz!**")
    st.markdown("---")
    
    # ============================================
    # 1️⃣ ŞİŞME ORANI MATRİSİ
    # ============================================
    st.subheader("1️⃣ Şişme Oranı Matrisi")
    st.caption("📊 Default: 0.5 | Düzenlemek için hücreye çift tıklayın")
    
    # Matris oluştur veya yükle
    if st.session_state.sisme_orani is not None:
        sisme_df = st.session_state.sisme_orani.copy()
    else:
        sisme_df = pd.DataFrame(0.5, index=store_segments, columns=prod_segments)
    
    # Index'i kolon olarak ekle (data_editor için gerekli)
    sisme_display = sisme_df.reset_index()
    sisme_display.rename(columns={'index': 'Mağaza↓ / Ürün→'}, inplace=True)
    
    # Düzenlenebilir tablo
    edited_sisme = st.data_editor(
        sisme_display,
        key="editor_sisme_v1",
        hide_index=True,
        width='stretch',
        num_rows="fixed",
        disabled=["Mağaza↓ / Ürün→"]  # İlk sütun düzenlenemez
    )
    
    st.markdown("---")
    
    # ============================================
    # 2️⃣ GENLEŞTİRME ORANI MATRİSİ
    # ============================================
    st.subheader("2️⃣ Genleştirme Oranı Matrisi")
    st.caption("📊 Default: 1.0 | Düzenlemek için hücreye çift tıklayın")
    
    if st.session_state.genlestirme_orani is not None:
        genles_df = st.session_state.genlestirme_orani.copy()
    else:
        genles_df = pd.DataFrame(1.0, index=store_segments, columns=prod_segments)
    
    genles_display = genles_df.reset_index()
    genles_display.rename(columns={'index': 'Mağaza↓ / Ürün→'}, inplace=True)
    
    edited_genles = st.data_editor(
        genles_display,
        key="editor_genles_v1",
        hide_index=True,
        width='stretch',
        num_rows="fixed",
        disabled=["Mağaza↓ / Ürün→"]
    )
    
    st.markdown("---")
    
    # ============================================
    # 3️⃣ MIN ORAN MATRİSİ
    # ============================================
    st.subheader("3️⃣ Min Oran Matrisi")
    st.caption("📊 Default: 1.0 | Düzenlemek için hücreye çift tıklayın")
    
    if st.session_state.min_oran is not None:
        min_df = st.session_state.min_oran.copy()
    else:
        min_df = pd.DataFrame(1.0, index=store_segments, columns=prod_segments)
    
    min_display = min_df.reset_index()
    min_display.rename(columns={'index': 'Mağaza↓ / Ürün→'}, inplace=True)
    
    edited_min = st.data_editor(
        min_display,
        key="editor_min_v1",
        hide_index=True,
        width='stretch',
        num_rows="fixed",
        disabled=["Mağaza↓ / Ürün→"]
    )
    
    st.markdown("---")
    
    # ============================================
    # 4️⃣ INITIAL MATRİS
    # ============================================
    st.subheader("4️⃣ Initial Matris")
    st.caption("📊 Default: 1.0 | Düzenlemek için hücreye çift tıklayın")
    
    if st.session_state.initial_matris is not None:
        initial_df = st.session_state.initial_matris.copy()
    else:
        initial_df = pd.DataFrame(1.0, index=store_segments, columns=prod_segments)
    
    initial_display = initial_df.reset_index()
    initial_display.rename(columns={'index': 'Mağaza↓ / Ürün→'}, inplace=True)
    
    edited_initial = st.data_editor(
        initial_display,
        key="editor_initial_v1",
        hide_index=True,
        width='stretch',
        num_rows="fixed",
        disabled=["Mağaza↓ / Ürün→"]
    )
    
    st.markdown("---")
    
    # ============================================
    # KAYDET BUTONU
    # ============================================
    st.subheader("💾 Değişiklikleri Kaydet")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if st.button("💾 KAYDET", type="primary", width='stretch', key="save_matrices_btn"):
            try:
                # Düzenlenmiş dataframe'leri index'e çevir ve kaydet
                st.session_state.sisme_orani = edited_sisme.set_index('Mağaza↓ / Ürün→')
                st.session_state.genlestirme_orani = edited_genles.set_index('Mağaza↓ / Ürün→')
                st.session_state.min_oran = edited_min.set_index('Mağaza↓ / Ürün→')
                st.session_state.initial_matris = edited_initial.set_index('Mağaza↓ / Ürün→')
                
                st.success("✅ Tüm matrisler başarıyla kaydedildi!")
                st.balloons()
                
                # Doğrulama bilgisi
                st.info(f"""
                **Kaydedilen Boyutlar:**
                - Şişme Oranı: {st.session_state.sisme_orani.shape[0]} × {st.session_state.sisme_orani.shape[1]}
                - Genleştirme: {st.session_state.genlestirme_orani.shape[0]} × {st.session_state.genlestirme_orani.shape[1]}
                - Min Oran: {st.session_state.min_oran.shape[0]} × {st.session_state.min_oran.shape[1]}
                - Initial: {st.session_state.initial_matris.shape[0]} × {st.session_state.initial_matris.shape[1]}
                """)
                
            except Exception as e:
                st.error(f"❌ Kaydetme hatası: {str(e)}")
    
    with col2:
        st.info("💡 **İpucu:** Değerleri değiştirdikten sonra 'Kaydet' butonuna basın. Kaydedilmeyen değişiklikler kaybolur!")
    
    st.markdown("---")
    
    # ============================================
    # İNDİRME SEÇENEKLERİ (BONUS)
    # ============================================
    with st.expander("📥 Matrisleri Excel/CSV Olarak İndir"):
        st.write("**Kaydedilmiş matrisleri dışa aktarın:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Excel formatında (tüm matrisler tek dosyada)
            if st.button("📊 Excel İndir (Tüm Matrisler)", key="download_excel"):
                try:
                    from io import BytesIO
                    
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        if st.session_state.sisme_orani is not None:
                            st.session_state.sisme_orani.to_excel(writer, sheet_name='Şişme Oranı')
                        if st.session_state.genlestirme_orani is not None:
                            st.session_state.genlestirme_orani.to_excel(writer, sheet_name='Genleştirme')
                        if st.session_state.min_oran is not None:
                            st.session_state.min_oran.to_excel(writer, sheet_name='Min Oran')
                        if st.session_state.initial_matris is not None:
                            st.session_state.initial_matris.to_excel(writer, sheet_name='Initial')
                    
                    output.seek(0)
                    
                    st.download_button(
                        label="⬇️ Excel Dosyasını İndir",
                        data=output.getvalue(),
                        file_name="hedef_matrisler.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                except Exception as e:
                    st.error(f"Excel indirme hatası: {e}")
        
        with col2:
            # CSV formatında (ZIP içinde 4 dosya)
            if st.button("📦 CSV İndir (ZIP)", key="download_csv"):
                try:
                    import zipfile
                    from io import BytesIO
                    
                    zip_buffer = BytesIO()
                    
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        if st.session_state.sisme_orani is not None:
                            csv_data = st.session_state.sisme_orani.to_csv(encoding='utf-8-sig')
                            zip_file.writestr('sisme_orani.csv', csv_data)
                        
                        if st.session_state.genlestirme_orani is not None:
                            csv_data = st.session_state.genlestirme_orani.to_csv(encoding='utf-8-sig')
                            zip_file.writestr('genlestirme_orani.csv', csv_data)
                        
                        if st.session_state.min_oran is not None:
                            csv_data = st.session_state.min_oran.to_csv(encoding='utf-8-sig')
                            zip_file.writestr('min_oran.csv', csv_data)
                        
                        if st.session_state.initial_matris is not None:
                            csv_data = st.session_state.initial_matris.to_csv(encoding='utf-8-sig')
                            zip_file.writestr('initial_matris.csv', csv_data)
                    
                    zip_buffer.seek(0)
                    
                    st.download_button(
                        label="⬇️ ZIP Dosyasını İndir",
                        data=zip_buffer.getvalue(),
                        file_name="hedef_matrisler.zip",
                        mime="application/zip"
                    )
                except Exception as e:
                    st.error(f"CSV indirme hatası: {e}")



# ============================================
# 🔢 SIRALAMA - İHTİYAÇ ÖNCELİKLENDİRME
# ============================================
elif menu == "🔢 Sıralama":
    st.title("🔢 Sıralama Öncelikleri")
    st.markdown("---")
    
    # Session state başlatma
    if 'oncelik_siralama' not in st.session_state:
        st.session_state.oncelik_siralama = None
    
    # Segment kontrolü
    if st.session_state.prod_segments is None:
        st.warning("⚠️ Önce 'Segmentasyon' sayfasına gidin ve segmentasyonu kaydedin!")
        st.stop()
    
    prod_segments = st.session_state.prod_segments
    
    st.info(f"📊 Toplam {len(prod_segments)} ürün segmenti için öncelik sıralaması yapacaksınız")
    st.markdown("---")
    
    # Açıklama
    st.markdown("""
    ### 📋 Nasıl Çalışır?
    
    Her **ürün segmenti** için ihtiyaç türlerinin öncelik sırasını belirleyin:
    
    - **RPT (Replenishment):** Normal stok tamamlama
    - **Initial:** Yeni ürün ilk dağıtımı  
    - **Min:** Minimum stok garantisi
    
    **Örnek:**
    - Segment **0-4** için: `1. RPT → 2. Initial → 3. Min`
    - Segment **5-8** için: `1. Initial → 2. RPT → 3. Min`
    
    **Depo stok dağıtımı** bu sıraya göre yapılacak.
    """)
    
    st.markdown("---")
    
    # Mevcut sıralamayı yükle veya default oluştur
    if st.session_state.oncelik_siralama is not None:
        siralama_dict = st.session_state.oncelik_siralama
        st.success("✅ Kaydedilmiş sıralama yüklendi")
    else:
        # Default: RPT → Initial → Min
        siralama_dict = {segment: ['RPT', 'Initial', 'Min'] for segment in prod_segments}
        st.info("ℹ️ Default sıralama gösteriliyor (RPT → Initial → Min)")
    
    st.markdown("---")
    
    # Sıralama tablosu
    st.subheader("🎯 Öncelik Sıralaması")
    
    # Düzenlenebilir tablo oluştur
    siralama_data = []
    for segment in prod_segments:
        current_order = siralama_dict.get(segment, ['RPT', 'Initial', 'Min'])
        siralama_data.append({
            'Ürün Segmenti': segment,
            '1. Öncelik': current_order[0],
            '2. Öncelik': current_order[1],
            '3. Öncelik': current_order[2]
        })
    
    siralama_df = pd.DataFrame(siralama_data)
    
    # Data editor ile düzenleme
    st.write("**Sıralamayı Düzenleyin:**")
    st.caption("Her segment için öncelik sırasını değiştirin (dropdown'dan seçin)")
    
    edited_df = st.data_editor(
        siralama_df,
        column_config={
            "Ürün Segmenti": st.column_config.TextColumn(
                "Ürün Segmenti",
                disabled=True,
                width="medium"
            ),
            "1. Öncelik": st.column_config.SelectboxColumn(
                "1. Öncelik",
                options=['RPT', 'Initial', 'Min'],
                required=True,
                width="medium"
            ),
            "2. Öncelik": st.column_config.SelectboxColumn(
                "2. Öncelik",
                options=['RPT', 'Initial', 'Min'],
                required=True,
                width="medium"
            ),
            "3. Öncelik": st.column_config.SelectboxColumn(
                "3. Öncelik",
                options=['RPT', 'Initial', 'Min'],
                required=True,
                width="medium"
            )
        },
        hide_index=True,
        width='stretch',
        key="siralama_editor"
    )
    
    st.markdown("---")
    
    # Validasyon ve Kaydet
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if st.button("💾 KAYDET", type="primary", width='stretch'):
            # Validasyon: Her satırda aynı değer tekrar etmemeli
            valid = True
            error_rows = []
            
            for idx, row in edited_df.iterrows():
                values = [row['1. Öncelik'], row['2. Öncelik'], row['3. Öncelik']]
                if len(values) != len(set(values)):
                    valid = False
                    error_rows.append(row['Ürün Segmenti'])
            
            if not valid:
                st.error(f"❌ Hata! Aynı öncelik tekrar ediyor: {', '.join(error_rows)}")
                st.warning("Her segment için RPT, Initial ve Min değerleri farklı olmalı!")
            else:
                # Dictionary formatında kaydet
                yeni_siralama = {}
                for _, row in edited_df.iterrows():
                    yeni_siralama[row['Ürün Segmenti']] = [
                        row['1. Öncelik'],
                        row['2. Öncelik'],
                        row['3. Öncelik']
                    ]
                
                st.session_state.oncelik_siralama = yeni_siralama
                st.success("✅ Sıralama kaydedildi!")
                st.balloons()
    
    with col2:
        st.info("💡 **İpucu:** Her satırda RPT, Initial ve Min farklı sırada olmalı")
    
    st.markdown("---")
    
    # Önizleme
    st.subheader("👁️ Kayıtlı Sıralama Önizlemesi")
    
    if st.session_state.oncelik_siralama is not None:
        import json
        preview_data = []
        for segment, order in st.session_state.oncelik_siralama.items():
            preview_data.append({
                'Segment': segment,
                'Sıralama': ' → '.join(order)
            })
        
        preview_df = pd.DataFrame(preview_data)
        st.dataframe(preview_df, width='stretch', hide_index=True, height=250)
        
        # JSON export
        with st.expander("📥 JSON Formatında İndir"):
            json_str = json.dumps(st.session_state.oncelik_siralama, indent=2, ensure_ascii=False)
            st.download_button(
                label="💾 JSON İndir",
                data=json_str,
                file_name="oncelik_siralama.json",
                mime="application/json"
            )
            st.code(json_str, language='json')
    else:
        st.warning("⚠️ Henüz kayıtlı sıralama yok")
    
    st.markdown("---")
    
    # Reset butonu
    if st.button("🔄 Default Sıralamaya Sıfırla"):
        st.session_state.oncelik_siralama = None
        st.success("✅ Sıfırlandı! Sayfa yenileniyor...")
        st.rerun()
    
    st.markdown("---")
    
    # Bilgilendirme
    st.info("""
    **ℹ️ Bu Sıralama Nerede Kullanılır?**
    
    **Hesaplama** bölümünde sevkiyat ihtiyaçları hesaplanırken:
    1. Tüm ürün-mağaza kombinasyonları için ihtiyaç hesaplanır (RPT/Initial/Min)
    2. Bu sıralama bilgisine göre öncelik atanır
    3. Depo stoku **bu öncelik sırasına göre dağıtılır**
    
    **Örnek:**
    - Segment 0-4 ürünü için önce **RPT** ihtiyaçları karşılanır
    - Sonra **Initial** (yeni ürün dağıtımı)
    - En son **Min** (minimum garantisi)
    
    **⚠️ Önemli:** Kaydet butonuna basmazsanız **default sıralama** (RPT → Initial → Min) kullanılır!
    """)
    
    st.markdown("---")
    
    # Kullanım Notu
    st.success("""
    ✅ **Hızlı Kullanım:**
    - Varsayılan sıralamayı kullanmak istiyorsanız → Hiçbir şey yapmanıza gerek yok!
    - Özel sıralama istiyorsanız → Tabloyu düzenleyin ve **Kaydet** butonuna basın
    """)

# ============================================
# 📐 HESAPLAMA - MAX YAKLAŞIMI İLE DÜZELTİLMİŞ
# ============================================
# Bu kodu 2_Sevkiyat.py dosyasında "elif menu == '📐 Hesaplama':" 
# bölümünün TAMAMINI değiştirmek için kullan

elif menu == "📐 Hesaplama":
    st.title("📐 Hesaplama")
    st.markdown("---")
    
    # Veri kontrolü
    required_data = {
        "Ürün Master": st.session_state.urun_master,
        "Mağaza Master": st.session_state.magaza_master,
        "Anlık Stok/Satış": st.session_state.anlik_stok_satis,
        "Depo Stok": st.session_state.depo_stok,
        "KPI": st.session_state.kpi
    }
    
    missing_data = [name for name, data in required_data.items() if data is None]
    
    if missing_data:
        st.warning("⚠️ Tüm zorunlu verileri yükleyin!")
        st.error(f"**Eksik:** {', '.join(missing_data)}")
        st.stop()
    
    st.success("✅ Tüm zorunlu veriler hazır!")
    
    # ============================================
    # HESAPLAMA PARAMETRELERİ
    # ============================================
    st.subheader("⚙️ Hesaplama Parametreleri")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Brüt Kar Marjı Sınırı
        st.markdown("**💰 Brüt Kar Marjı Kontrolü**")
        brut_kar_aktif = st.checkbox("Brüt kar marjı sınırı uygula", value=False, key="brut_kar_aktif")
        
        if brut_kar_aktif:
            brut_kar_siniri = st.number_input(
                "Minimum BKM % (Bu değerin altındaki ürünler için ihtiyaç hesaplanmaz)",
                min_value=0.0, max_value=100.0, value=30.0, step=1.0,
                key="brut_kar_siniri",
                help="Örnek: %30 yazarsanız, brüt kar marjı %30'un altındaki ürünler için sevkiyat hesaplanmaz"
            )
        else:
            brut_kar_siniri = 0.0
    
    with col2:
        # Paket Sevkiyatı
        st.markdown("**📦 Paket Sevkiyatı Kontrolü**")
        paket_sevk_aktif = st.checkbox("Paket bazlı sevkiyat uygula", value=False, key="paket_sevk_aktif")
        
        if paket_sevk_aktif:
            st.info("✅ Ürünler paket_ici miktarının katları olarak sevk edilecek. Şişme oranı kontrol edilecek.")
            st.caption("Örnek: Paket içi=10, İhtiyaç=8 → 10 adet sevk (şişme %25 < %50 OK)")
    
    st.markdown("---")
    
    # Hesapla Butonu
    if st.button("🚀 HESAPLA", type="primary", width='stretch'):
        baslaangic_zamani = time.time()

        try:
            # ============================================
            # 0. VERİ KALİTE KONTROLÜ
            # ============================================
            # Progress bar ve durum göstergesi
            progress_container = st.container()
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()
                detail_text = st.empty()

            def update_progress(pct, status, detail=""):
                progress_bar.progress(pct / 100)
                status_text.info(f"⏳ {status}")
                if detail:
                    detail_text.caption(detail)

            update_progress(5, "Veri kalitesi kontrol ediliyor...")
            
            # Zorunlu kolonları kontrol et
            anlik_zorunlu = ['urun_kod', 'magaza_kod', 'stok', 'yol', 'satis']
            depo_zorunlu = ['urun_kod', 'depo_kod', 'stok']
            magaza_zorunlu = ['magaza_kod', 'depo_kod']
            kpi_zorunlu = ['mg_id']
            
            hatalar = []
            
            # Anlık stok/satış kontrolü
            anlik_df = st.session_state.anlik_stok_satis
            if anlik_df is None or anlik_df.empty:
                hatalar.append("❌ Anlık Stok/Satış verisi boş!")
            else:
                eksik_kolonlar = [k for k in anlik_zorunlu if k not in anlik_df.columns]
                if eksik_kolonlar:
                    hatalar.append(f"❌ Anlık Stok/Satış'ta eksik kolonlar: {eksik_kolonlar}")
                # Sayısal kolonları kontrol et
                for col in ['stok', 'yol', 'satis']:
                    if col in anlik_df.columns:
                        if not pd.api.types.is_numeric_dtype(anlik_df[col]):
                            try:
                                pd.to_numeric(anlik_df[col], errors='coerce')
                            except:
                                hatalar.append(f"❌ '{col}' kolonu sayısal değil!")
            
            # Depo stok kontrolü
            depo_df_check = st.session_state.depo_stok
            if depo_df_check is None or depo_df_check.empty:
                hatalar.append("❌ Depo Stok verisi boş!")
            else:
                eksik_kolonlar = [k for k in depo_zorunlu if k not in depo_df_check.columns]
                if eksik_kolonlar:
                    hatalar.append(f"❌ Depo Stok'ta eksik kolonlar: {eksik_kolonlar}")
            
            # Mağaza master kontrolü
            magaza_df_check = st.session_state.magaza_master
            if magaza_df_check is None or magaza_df_check.empty:
                hatalar.append("❌ Mağaza Master verisi boş!")
            else:
                eksik_kolonlar = [k for k in magaza_zorunlu if k not in magaza_df_check.columns]
                if eksik_kolonlar:
                    hatalar.append(f"❌ Mağaza Master'da eksik kolonlar: {eksik_kolonlar}")
            
            # Hata varsa dur
            if hatalar:
                for hata in hatalar:
                    st.error(hata)
                st.warning("⚠️ Lütfen Veri Yükleme sayfasından verileri kontrol edin!")
                st.stop()

            # ============================================
            # 1. VERİ HAZIRLA
            # ============================================
            update_progress(10, "Veriler hazırlanıyor...", "Anlık stok/satış yükleniyor")

            df = st.session_state.anlik_stok_satis.copy()
            # Float'tan gelen .0 suffix'ini temizle
            df['urun_kod'] = df['urun_kod'].astype(str).str.replace(r'\.0$', '', regex=True)
            df['magaza_kod'] = df['magaza_kod'].astype(str).str.replace(r'\.0$', '', regex=True)

            # Sayısal kolonları zorla dönüştür
            for col in ['stok', 'yol', 'satis']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            depo_df = st.session_state.depo_stok.copy()
            depo_df['urun_kod'] = depo_df['urun_kod'].astype(str).str.replace(r'\.0$', '', regex=True)
            depo_df['depo_kod'] = depo_df['depo_kod'].astype(str).str.replace(r'\.0$', '', regex=True)
            depo_df['stok'] = pd.to_numeric(depo_df['stok'], errors='coerce').fillna(0)

            magaza_df = st.session_state.magaza_master.copy()
            magaza_df['magaza_kod'] = magaza_df['magaza_kod'].astype(str).str.replace(r'\.0$', '', regex=True)

            kpi_df = st.session_state.kpi.copy() if st.session_state.kpi is not None else pd.DataFrame()
            
            # ============================================
            # 1.5 BRÜT KAR MARJI HESAPLA VE FİLTRELE
            # ============================================
            update_progress(15, "Brüt kar marjı hesaplanıyor...", f"{len(df):,} satır işleniyor")
            brut_kar_filtre_sayisi = 0

            if brut_kar_aktif and brut_kar_siniri > 0:
                
                # BKM hesapla: (ciro - smm*satis) / ciro * 100 veya direkt smm/satis
                # smm = satılan malın maliyeti (toplam), ciro = satış hasılatı
                if 'smm' in df.columns and 'ciro' in df.columns:
                    # BKM% = (Ciro - SMM) / Ciro * 100
                    df['brut_kar_marji'] = np.where(
                        df['ciro'] > 0,
                        ((df['ciro'] - df['smm']) / df['ciro']) * 100,
                        0
                    )
                elif 'smm' in df.columns and 'satis' in df.columns:
                    # Alternatif: smm zaten oran olarak geliyorsa
                    df['brut_kar_marji'] = 100 - (df['smm'] * 100)
                else:
                    df['brut_kar_marji'] = 100  # SMM yoksa hepsini dahil et
                
                # Filtreleme öncesi say
                onceki_satir = len(df)
                
                # BKM sınırının altındakileri işaretle (ihtiyaç hesaplanmayacak)
                df['brut_kar_filtreli'] = df['brut_kar_marji'] < brut_kar_siniri
                brut_kar_filtre_sayisi = df['brut_kar_filtreli'].sum()
            else:
                df['brut_kar_filtreli'] = False
                df['brut_kar_marji'] = 100
            
            # ============================================
            # 1.6 PAKET İÇİ BİLGİSİ EKLE
            # ============================================
            update_progress(20, "Paket bilgileri ekleniyor...")
            if paket_sevk_aktif:
                urun_master = st.session_state.urun_master
                if (urun_master is not None and
                    'paket_ici' in urun_master.columns and
                    'urun_kod' in urun_master.columns):
                    try:
                        paket_info = urun_master[['urun_kod', 'paket_ici']].copy()
                        paket_info['urun_kod'] = paket_info['urun_kod'].astype(str).str.replace(r'\.0$', '', regex=True)
                        paket_info['paket_ici'] = pd.to_numeric(paket_info['paket_ici'], errors='coerce').fillna(1).astype(int)
                        paket_info.loc[paket_info['paket_ici'] < 1, 'paket_ici'] = 1

                        df = df.merge(paket_info, on='urun_kod', how='left')
                        df['paket_ici'] = df['paket_ici'].fillna(1).astype(int)
                    except Exception:
                        df['paket_ici'] = 1
                else:
                    df['paket_ici'] = 1
                    st.warning("⚠️ Ürün master'da paket_ici bilgisi bulunamadı, tüm ürünler için paket_ici=1 alındı.")
            else:
                df['paket_ici'] = 1
            
            # ============================================
            # 2. YENİ ÜRÜNLER
            # ============================================
            update_progress(25, "Yeni ürünler analiz ediliyor...")
            depo_sum = depo_df.groupby('urun_kod')['stok'].sum()
            yeni_adaylar = depo_sum[depo_sum > 300].index.tolist()

            urun_magaza_count = df[df['urun_kod'].isin(yeni_adaylar)].groupby('urun_kod')['magaza_kod'].nunique()
            total_magaza = df['magaza_kod'].nunique()
            yeni_urunler = urun_magaza_count[urun_magaza_count < total_magaza * 0.5].index.tolist()

            # NOT: Depo'da olup anlık_stok_satis'ta olmayan ürünler eklenmez
            # Çünkü bu ürünler için ürün master bilgisi (paket_ici, mg, segment vb.) eksik kalır
            # Bu ürünleri sevk etmek istiyorsanız, önce anlık_stok_satis CSV'sine ekleyin

            # 3. SEGMENTASYON - VERİ TİPİ UYUMLU
            update_progress(30, "Segmentasyon uygulanıyor...")
            if (st.session_state.urun_segment_map and st.session_state.magaza_segment_map):
                # Tüm key'leri string'e çevir ve strip uygula
                urun_seg_map_str = {str(k).strip(): str(v) for k, v in st.session_state.urun_segment_map.items()}
                magaza_seg_map_str = {str(k).strip(): str(v) for k, v in st.session_state.magaza_segment_map.items()}

                # df'deki kodları da string'e çevir ve strip uygula
                df['urun_kod'] = df['urun_kod'].astype(str).str.strip()
                df['magaza_kod'] = df['magaza_kod'].astype(str).str.strip()

                df['urun_segment'] = df['urun_kod'].map(urun_seg_map_str)
                df['magaza_segment'] = df['magaza_kod'].map(magaza_seg_map_str)

                # NaN'ları default değerle doldur
                df['urun_segment'] = df['urun_segment'].fillna('Seg_20-inf')
                df['magaza_segment'] = df['magaza_segment'].fillna('Seg_20-inf')
            else:
                df['urun_segment'] = 'Seg_20-inf'
                df['magaza_segment'] = 'Seg_20-inf'

            # ============================================
            # 4. KPI VE MG BİLGİLERİ
            # ============================================
            update_progress(35, "KPI değerleri uygulanıyor...")

            # default_fc hesapla (güvenli)
            default_fc = 7.0
            if not kpi_df.empty and 'forward_cover' in kpi_df.columns:
                fc_mean = kpi_df['forward_cover'].mean()
                if pd.notna(fc_mean):
                    default_fc = fc_mean

            df['min_deger'] = 0.0
            df['max_deger'] = 999999.0

            # MG bilgisi ekle (urun_kod ve mg kolonlarını kontrol et)
            urun_master = st.session_state.urun_master
            if (urun_master is not None and
                'mg' in urun_master.columns and
                'urun_kod' in urun_master.columns):
                try:
                    urun_m = urun_master[['urun_kod', 'mg']].copy()
                    urun_m['urun_kod'] = urun_m['urun_kod'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    urun_m['mg'] = urun_m['mg'].fillna('0').astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    df['urun_kod'] = df['urun_kod'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    df = df.merge(urun_m, on='urun_kod', how='left')
                    df['mg'] = df['mg'].fillna('0').str.replace(r'\.0$', '', regex=True).str.strip()
                except Exception:
                    df['mg'] = '0'
            else:
                df['mg'] = '0'

            # KPI değerlerini uygula
            if not kpi_df.empty and 'mg_id' in kpi_df.columns:
                kpi_lookup = {}
                for _, row in kpi_df.iterrows():
                    mg_key = str(row['mg_id']).strip()
                    kpi_lookup[mg_key] = {
                        'min': float(row.get('min_deger', 0)) if pd.notna(row.get('min_deger', 0)) else 0,
                        'max': float(row.get('max_deger', 999999)) if pd.notna(row.get('max_deger', 999999)) else 999999
                    }

                for mg_val in df['mg'].unique():
                    mg_val_stripped = str(mg_val).strip()
                    if mg_val_stripped in kpi_lookup:
                        mask = df['mg'] == mg_val
                        df.loc[mask, 'min_deger'] = kpi_lookup[mg_val_stripped]['min']
                        df.loc[mask, 'max_deger'] = kpi_lookup[mg_val_stripped]['max']
            
            # ============================================
            # 5. DEPO KODU EKLEMESİ
            # ============================================
            update_progress(40, "Depo kodları ekleniyor...")
            if 'depo_kod' in magaza_df.columns:
                df = df.merge(magaza_df[['magaza_kod', 'depo_kod']], on='magaza_kod', how='left')
                df['depo_kod'] = df['depo_kod'].fillna('1').astype(str)
            else:
                df['depo_kod'] = '1'

            # ============================================
            # 6. MATRİS DEĞERLERİ
            # ============================================
            update_progress(45, "Matris değerleri uygulanıyor...")
            df['genlestirme'] = 1.0
            df['sisme'] = 0.5
            df['min_oran'] = 1.0
            df['initial_katsayi'] = 1.0

            all_matrices_exist = all([
                st.session_state.genlestirme_orani is not None,
                st.session_state.sisme_orani is not None,
                st.session_state.min_oran is not None,
                st.session_state.initial_matris is not None
            ])

            if all_matrices_exist:
                # Genleştirme
                genles_long = st.session_state.genlestirme_orani.stack().reset_index()
                genles_long.columns = ['magaza_segment', 'urun_segment', 'genlestirme_mat']
                genles_long['magaza_segment'] = genles_long['magaza_segment'].astype(str)
                genles_long['urun_segment'] = genles_long['urun_segment'].astype(str)
                df = df.merge(genles_long, on=['magaza_segment', 'urun_segment'], how='left')
                df['genlestirme'] = df['genlestirme_mat'].fillna(df['genlestirme'])
                df.drop('genlestirme_mat', axis=1, inplace=True)

                # Şişme
                sisme_long = st.session_state.sisme_orani.stack().reset_index()
                sisme_long.columns = ['magaza_segment', 'urun_segment', 'sisme_mat']
                sisme_long['magaza_segment'] = sisme_long['magaza_segment'].astype(str)
                sisme_long['urun_segment'] = sisme_long['urun_segment'].astype(str)
                df = df.merge(sisme_long, on=['magaza_segment', 'urun_segment'], how='left')
                df['sisme'] = df['sisme_mat'].fillna(df['sisme'])
                df.drop('sisme_mat', axis=1, inplace=True)

                # Min Oran
                min_long = st.session_state.min_oran.stack().reset_index()
                min_long.columns = ['magaza_segment', 'urun_segment', 'min_oran_mat']
                min_long['magaza_segment'] = min_long['magaza_segment'].astype(str)
                min_long['urun_segment'] = min_long['urun_segment'].astype(str)
                df = df.merge(min_long, on=['magaza_segment', 'urun_segment'], how='left')
                df['min_oran'] = df['min_oran_mat'].fillna(df['min_oran'])
                df.drop('min_oran_mat', axis=1, inplace=True)

                # Initial
                initial_long = st.session_state.initial_matris.stack().reset_index()
                initial_long.columns = ['magaza_segment', 'urun_segment', 'initial_mat']
                initial_long['magaza_segment'] = initial_long['magaza_segment'].astype(str)
                initial_long['urun_segment'] = initial_long['urun_segment'].astype(str)
                df = df.merge(initial_long, on=['magaza_segment', 'urun_segment'], how='left')
                df['initial_katsayi'] = df['initial_mat'].fillna(df['initial_katsayi'])
                df.drop('initial_mat', axis=1, inplace=True)

            # ============================================
            # 7. İHTİYAÇ HESAPLA - MAX YAKLAŞIMI + MAX DEGER KONTROLÜ
            # ============================================
            update_progress(50, "İhtiyaçlar hesaplanıyor...", "MAX yaklaşımı uygulanıyor")
            
            # ⭐ KRİTİK DÜZELTME: RPT hesabında hedef stok MAX değeri aşmamalı!
            # Önce RAW hedef stoğu hesapla
            df['hedef_stok_raw'] = default_fc * df['satis'] * df['genlestirme']
            
            # Hedef stok = MIN(raw_hedef, max_deger)
            # Bu sayede mağaza kapasitesi korunur!
            df['hedef_stok'] = df[['hedef_stok_raw', 'max_deger']].min(axis=1)
            
            # RPT ihtiyacı = hedef_stok - (stok + yol)
            df['rpt_ihtiyac'] = df['hedef_stok'] - (df['stok'] + df['yol'])
            
            # Min ihtiyacı
            df['min_ihtiyac'] = (
                df['min_oran'] * df['min_deger']
            ) - (df['stok'] + df['yol'])
            
            # Initial ihtiyacı (sadece yeni ürünler için)
            df['initial_ihtiyac'] = 0.0
            if yeni_urunler:
                yeni_mask = df['urun_kod'].isin(yeni_urunler)
                df.loc[yeni_mask, 'initial_ihtiyac'] = (
                    df.loc[yeni_mask, 'min_deger'] * df.loc[yeni_mask, 'initial_katsayi']
                ) - (df.loc[yeni_mask, 'stok'] + df.loc[yeni_mask, 'yol'])
            
            # Negatif değerleri sıfırla
            df['rpt_ihtiyac'] = df['rpt_ihtiyac'].clip(lower=0)
            df['min_ihtiyac'] = df['min_ihtiyac'].clip(lower=0)
            df['initial_ihtiyac'] = df['initial_ihtiyac'].clip(lower=0)
            
            # ✅ MAX'I AL - TEK İHTİYAÇ
            df['ihtiyac'] = df[['rpt_ihtiyac', 'min_ihtiyac', 'initial_ihtiyac']].max(axis=1)
            
            # MAX tarafından sınırlanan satırları say
            max_sinirli = (df['hedef_stok'] < df['hedef_stok_raw']).sum()

            # ============================================
            # 7.5 BRÜT KAR FİLTRESİ UYGULA
            # ============================================
            if brut_kar_aktif and brut_kar_siniri > 0:
                # BKM sınırının altındaki ürünlerin ihtiyacını sıfırla
                df.loc[df['brut_kar_filtreli'] == True, 'ihtiyac'] = 0
            
            # Hangi türden geldiğini belirle
            def belirle_durum(row):
                if row['ihtiyac'] == 0:
                    if row.get('brut_kar_filtreli', False):
                        return 'BKM_Filtre'
                    return 'Yok'
                if row['ihtiyac'] == row['rpt_ihtiyac']:
                    return 'RPT'
                elif row['ihtiyac'] == row['initial_ihtiyac'] and row['initial_ihtiyac'] > 0:
                    return 'Initial'
                elif row['ihtiyac'] == row['min_ihtiyac']:
                    return 'Min'
                else:
                    return 'RPT'
            
            df['durum'] = df.apply(belirle_durum, axis=1)

            # ============================================
            # 8. YASAK KONTROL
            # ============================================
            update_progress(60, "Yasak kontrolleri yapılıyor...")
            if (st.session_state.yasak_master is not None and
                'urun_kod' in st.session_state.yasak_master.columns and
                'magaza_kod' in st.session_state.yasak_master.columns):

                yasak = st.session_state.yasak_master.copy()
                yasak['urun_kod'] = yasak['urun_kod'].astype(str).str.strip()
                yasak['magaza_kod'] = yasak['magaza_kod'].astype(str).str.strip()

                # df'deki kodları da strip et (merge için gerekli)
                df['urun_kod'] = df['urun_kod'].astype(str).str.strip()
                df['magaza_kod'] = df['magaza_kod'].astype(str).str.strip()

                if 'yasak_durum' in yasak.columns:
                    df = df.merge(
                        yasak[['urun_kod', 'magaza_kod', 'yasak_durum']],
                        on=['urun_kod', 'magaza_kod'], how='left'
                    )
                    # Hem 1, 1.0, "1" hem "Yasak" değerini kabul et
                    df.loc[(df['yasak_durum'] == 1) | (df['yasak_durum'] == 1.0) | (df['yasak_durum'] == '1') | (df['yasak_durum'] == 'Yasak'), 'ihtiyac'] = 0
                    df.drop('yasak_durum', axis=1, inplace=True, errors='ignore')
            
            # ============================================
            # 9. DEPO STOK DAĞITIMI
            # ============================================
            update_progress(70, "Depo stok dağıtımı yapılıyor...", "Öncelik sıralaması uygulanıyor")

            # Sadece pozitif ihtiyaçları al
            result = df[df['ihtiyac'] > 0].copy()

            if len(result) == 0:
                st.warning("⚠️ Hiç pozitif ihtiyaç bulunamadı!")
                st.stop()
            
            # Öncelik sıralaması
            durum_priority = {'RPT': 1, 'Initial': 2, 'Min': 3}
            result['durum_oncelik'] = result['durum'].map(durum_priority).fillna(4)
            result = result.sort_values(['durum_oncelik', 'ihtiyac'], ascending=[True, False])
            result = result.reset_index(drop=True)
            
            # Depo stok dictionary oluştur
            depo_stok_dict = {}
            for _, row in depo_df.iterrows():
                key = (str(row['depo_kod']), str(row['urun_kod']))
                depo_stok_dict[key] = float(row['stok'])

            # NumPy array'lerle çalış
            depo_kodlar = result['depo_kod'].values.astype(str)
            urun_kodlar = result['urun_kod'].values.astype(str)
            ihtiyaclar = result['ihtiyac'].values.astype(float)
            # ⭐ KRİTİK: NaN ve 0 değerleri 1 olarak al (bölme hatası önleme)
            if 'paket_ici' in result.columns:
                paket_icileri = result['paket_ici'].fillna(1).values.astype(int)
                paket_icileri = np.where(paket_icileri < 1, 1, paket_icileri)
            else:
                paket_icileri = np.ones(len(result), dtype=int)
            # Şişme oranları için de NaN kontrolü
            if 'sisme' in result.columns:
                sisme_oranlari = result['sisme'].fillna(0.5).values.astype(float)
            else:
                sisme_oranlari = np.full(len(result), 0.5)
            
            sevkiyat_array = np.zeros(len(result), dtype=float)
            paket_sevk_flag = np.zeros(len(result), dtype=int)  # Paket sevkiyatı uygulandı mı
            
            # Tek döngü
            progress_bar = st.progress(0)
            total_rows = len(result)
            
            for idx in range(total_rows):
                key = (depo_kodlar[idx], urun_kodlar[idx])
                ihtiyac = ihtiyaclar[idx]
                paket_ici = paket_icileri[idx]
                sisme_orani = sisme_oranlari[idx]
                
                if key in depo_stok_dict and depo_stok_dict[key] > 0:
                    mevcut_stok = depo_stok_dict[key]

                    # ============================================
                    # PAKET SEVKİYATI MANTIĞI (BASİT)
                    # ============================================
                    # paket_ici güvenli değer (0 veya negatifse 1)
                    safe_paket = paket_ici if paket_ici > 0 else 1

                    if paket_sevk_aktif and safe_paket > 1:
                        # İhtiyacı paket katına yuvarla (yukarı)
                        paket_sayisi = int(np.ceil(ihtiyac / safe_paket))
                        istenen_sevk = paket_sayisi * safe_paket

                        # Stok yetiyorsa gönder, yetmiyorsa stokun izin verdiği kadar paket
                        if istenen_sevk <= mevcut_stok:
                            sevk = istenen_sevk
                        else:
                            max_paket = int(np.floor(mevcut_stok / safe_paket))
                            sevk = max_paket * safe_paket

                        paket_sevk_flag[idx] = 1 if sevk > 0 else 0
                    else:
                        # Normal sevkiyat (paket yok veya paket_ici=1)
                        sevk = min(ihtiyac, mevcut_stok)
                    
                    depo_stok_dict[key] -= sevk
                    sevkiyat_array[idx] = sevk
                
                # Progress güncelle (her 10K'da bir)
                if idx % 10000 == 0:
                    pct = 70 + int((idx / total_rows) * 15)  # 70-85% arası
                    update_progress(pct, "Depo stok dağıtımı yapılıyor...", f"{idx:,}/{total_rows:,} satır işlendi")

            result['sevkiyat_miktari'] = sevkiyat_array
            result['stok_yoklugu_satis_kaybi'] = result['ihtiyac'] - result['sevkiyat_miktari']

            if paket_sevk_aktif:
                result['paket_sevk_uygulandi'] = paket_sevk_flag

            # Temizlik
            result.drop('durum_oncelik', axis=1, inplace=True, errors='ignore')

            update_progress(85, "Sonuçlar hazırlanıyor...", "KPI bilgileri ekleniyor")
            
            # ============================================
            # 10. SONUÇ HAZIRLA - GENİŞLETİLMİŞ KOLONLAR
            # ============================================

            # Önce KPI'dan forward_cover, min, max değerlerini al
            # mg kolonu kontrolü
            if 'mg' not in result.columns:
                result['mg'] = '0'

            kpi_merged = False
            if not kpi_df.empty and 'mg_id' in kpi_df.columns:
                kpi_lookup_df = kpi_df.copy()
                kpi_lookup_df['mg_id'] = kpi_lookup_df['mg_id'].astype(str).str.replace(r'\.0$', '', regex=True)

                # Gerekli kolonları kontrol et ve eksik olanları ekle
                if 'min_deger' not in kpi_lookup_df.columns:
                    kpi_lookup_df['min_deger'] = 0
                if 'max_deger' not in kpi_lookup_df.columns:
                    kpi_lookup_df['max_deger'] = 999999
                if 'forward_cover' not in kpi_lookup_df.columns:
                    kpi_lookup_df['forward_cover'] = default_fc

                try:
                    result = result.merge(
                        kpi_lookup_df[['mg_id', 'min_deger', 'max_deger', 'forward_cover']].rename(
                            columns={'mg_id': 'mg', 'min_deger': 'kpi_min', 'max_deger': 'kpi_max', 'forward_cover': 'kpi_forward_cover'}
                        ),
                        on='mg', how='left'
                    )
                    kpi_merged = True
                except Exception:
                    kpi_merged = False

            if not kpi_merged:
                result['kpi_min'] = 0
                result['kpi_max'] = 999999
                result['kpi_forward_cover'] = default_fc

            # NaN değerleri doldur
            result['kpi_min'] = result['kpi_min'].fillna(0)
            result['kpi_max'] = result['kpi_max'].fillna(999999)
            result['kpi_forward_cover'] = result['kpi_forward_cover'].fillna(default_fc)
            
            # Depo stok bilgisini ekle
            depo_stok_merge = depo_df.groupby(['depo_kod', 'urun_kod'])['stok'].sum().reset_index()
            depo_stok_merge.columns = ['depo_kod', 'urun_kod', 'ilk_depo_stok']
            depo_stok_merge['depo_kod'] = depo_stok_merge['depo_kod'].astype(str).str.replace(r'\.0$', '', regex=True)
            depo_stok_merge['urun_kod'] = depo_stok_merge['urun_kod'].astype(str).str.replace(r'\.0$', '', regex=True)
            result = result.merge(depo_stok_merge, on=['depo_kod', 'urun_kod'], how='left')
            result['ilk_depo_stok'] = result['ilk_depo_stok'].fillna(0)
            
            # ============================================
            # PAKET BİLGİSİ EKLE (Ürün Master'dan)
            # ============================================
            # Önce varsa eski paket_ici kolonlarını temizle
            paket_cols_to_drop = [c for c in result.columns if 'paket_ici' in c.lower()]
            if paket_cols_to_drop:
                result = result.drop(columns=paket_cols_to_drop, errors='ignore')
            
            # Paket bilgisi eklemeyi dene
            try:
                urun_master = st.session_state.urun_master
                if urun_master is not None and 'paket_ici' in urun_master.columns:
                    paket_master = urun_master[['urun_kod', 'paket_ici']].drop_duplicates('urun_kod').copy()
                    paket_master['urun_kod'] = paket_master['urun_kod'].astype(str).str.replace(r'\.0$', '', regex=True)
                    paket_master['paket_ici'] = pd.to_numeric(paket_master['paket_ici'], errors='coerce').fillna(1).astype(int)
                    paket_master.loc[paket_master['paket_ici'] < 1, 'paket_ici'] = 1

                    result = result.merge(paket_master, on='urun_kod', how='left')
                    result['paket_ici'] = result['paket_ici'].fillna(1).astype(int)
                    result.loc[result['paket_ici'] < 1, 'paket_ici'] = 1
                else:
                    result['paket_ici'] = 1
            except Exception:
                result['paket_ici'] = 1

            # Sevkiyat paket adeti hesapla (0'a bölme hatası önleme)
            safe_paket_ici = result['paket_ici'].replace(0, 1)
            result['sevkiyat_paket_adet'] = np.ceil(result['sevkiyat_miktari'] / safe_paket_ici).fillna(0).astype(int)
            
            # ============================================
            # KPI DURUM KOLONLARI EKLE
            # ============================================
            
            # Aktif nokta (stok>0 OR satis>0 OR yol>0)
            result['aktif_nokta'] = np.where(
                (result['stok'] > 0) | (result['satis'] > 0) | (result['yol'] > 0),
                1, 0
            )
            
            # Hesaplanan kolonlar (cover için)
            result['ilk_nihai_cover'] = np.where(
                result['satis'] > 0,
                (result['stok'] + result['yol']) / result['satis'],
                0
            ).round(2)
            
            result['son_nihai_stok'] = result['stok'] + result['yol'] + result['sevkiyat_miktari']
            
            result['son_nihai_cover'] = np.where(
                result['satis'] > 0,
                result['son_nihai_stok'] / result['satis'],
                0
            ).round(2)
            
            # KPI Durum belirleme
            def belirle_kpi_durum(row):
                durumlar = []
                
                # Sadece aktif noktalar için kontrol
                if row['aktif_nokta'] == 0:
                    return 'Pasif'
                
                # Min altı kontrolü
                mevcut_stok = row['stok'] + row['yol']
                if mevcut_stok < row['kpi_min']:
                    durumlar.append('Min_Alti')
                
                # Max üstü kontrolü
                if mevcut_stok > row['kpi_max']:
                    durumlar.append('Max_Ustu')
                
                # Cover > 12 hafta
                if row['ilk_nihai_cover'] > 12:
                    durumlar.append('Cover>12')
                
                # Cover < 4 hafta (satış varsa)
                if row['satis'] > 0 and 0 < row['ilk_nihai_cover'] < 4:
                    durumlar.append('Cover<4')
                
                # İhtiyaç > 100 ama sevkiyat = 0
                if row.get('ihtiyac', 0) > 100 and row['sevkiyat_miktari'] == 0:
                    durumlar.append('Ihtiyac_Karsilanamadi')
                
                # BKM filtresi (eğer varsa)
                if row.get('brut_kar_filtreli', False):
                    durumlar.append('BKM_Filtre')
                
                if durumlar:
                    return '|'.join(durumlar)
                else:
                    return 'Normal'
            
            result['kpi_durum'] = result.apply(belirle_kpi_durum, axis=1)
            
            final_columns = [
                'magaza_kod', 'urun_kod', 'magaza_segment', 'urun_segment', 'durum',
                'stok', 'yol', 'satis', 'ilk_nihai_cover', 'ihtiyac', 'sevkiyat_miktari',
                'paket_ici', 'sevkiyat_paket_adet',
                'depo_kod', 'stok_yoklugu_satis_kaybi', 'kpi_min', 'kpi_max', 'kpi_forward_cover',
                'ilk_depo_stok', 'son_nihai_stok', 'son_nihai_cover',
                'aktif_nokta', 'kpi_durum'
            ]
            
            available_columns = [col for col in final_columns if col in result.columns]
            final = result[available_columns].copy()
            
            final = final.rename(columns={
                'ihtiyac': 'ihtiyac_miktari',
                'kpi_min': 'KPI_Min',
                'kpi_max': 'KPI_Max', 
                'kpi_forward_cover': 'KPI_Forward_Cover',
                'ilk_depo_stok': 'Ilk_Depo_Stok',
                'son_nihai_stok': 'Son_Nihai_Stok',
                'son_nihai_cover': 'Son_Nihai_Cover',
                'ilk_nihai_cover': 'Ilk_Nihai_Cover',
                'paket_ici': 'Paket_Ici',
                'sevkiyat_paket_adet': 'Sevkiyat_Paket_Adet',
                'aktif_nokta': 'Aktif_Nokta',
                'kpi_durum': 'KPI_Durum'
            })
            
            # Integer dönüşüm
            for col in ['stok', 'yol', 'satis', 'ihtiyac_miktari', 'sevkiyat_miktari', 'Paket_Ici', 'Sevkiyat_Paket_Adet', 'stok_yoklugu_satis_kaybi', 'KPI_Min', 'KPI_Max', 'Ilk_Depo_Stok', 'Son_Nihai_Stok', 'Aktif_Nokta']:
                if col in final.columns:
                    final[col] = final[col].round().fillna(0).astype(int)
            
            # Float kolonlar
            for col in ['Ilk_Nihai_Cover', 'Son_Nihai_Cover', 'KPI_Forward_Cover']:
                if col in final.columns:
                    final[col] = final[col].round(2).fillna(0)
            
            # Sıra numaraları
            final.insert(0, 'sira_no', range(1, len(final) + 1))
            final.insert(1, 'oncelik', range(1, len(final) + 1))

            # ============================================
            # SON YASAK KONTROLÜ - TÜM HESAPLAMALAR BİTTİKTEN SONRA
            # ============================================
            update_progress(95, "Son kontroller yapılıyor...", "Yasak kontrolü")

            yasak_master = st.session_state.get('yasak_master', None)

            if yasak_master is not None and len(yasak_master) > 0:

                yasak_df = yasak_master.copy()

                # Sütun isimlerini kontrol et ve düzelt
                yasak_df.columns = yasak_df.columns.str.strip().str.lower()

                if 'urun_kod' in yasak_df.columns and 'magaza_kod' in yasak_df.columns:
                    yasak_df['urun_kod'] = yasak_df['urun_kod'].astype(str).str.strip()
                    yasak_df['magaza_kod'] = yasak_df['magaza_kod'].astype(str).str.strip()

                    # Yasak durumu kontrolü - sütun varsa filtrele, yoksa tümünü al
                    if 'yasak_durum' in yasak_df.columns:
                        yasak_df['yasak_durum'] = pd.to_numeric(yasak_df['yasak_durum'], errors='coerce').fillna(0)
                        yasak_aktif = yasak_df[yasak_df['yasak_durum'] >= 1]
                    else:
                        yasak_aktif = yasak_df

                    if len(yasak_aktif) > 0:
                        yasak_set = set(zip(yasak_aktif['urun_kod'], yasak_aktif['magaza_kod']))
                        final['urun_kod'] = final['urun_kod'].astype(str).str.strip()
                        final['magaza_kod'] = final['magaza_kod'].astype(str).str.strip()

                        yasak_mask = final.apply(
                            lambda row: (str(row['urun_kod']).strip(), str(row['magaza_kod']).strip()) in yasak_set,
                            axis=1
                        )
                        yasak_sayisi = yasak_mask.sum()

                        if yasak_sayisi > 0:
                            final.loc[yasak_mask, 'sevkiyat_miktari'] = 0
                            if 'Sevkiyat_Paket_Adet' in final.columns:
                                final.loc[yasak_mask, 'Sevkiyat_Paket_Adet'] = 0

            # KAYDET
            st.session_state.sevkiyat_sonuc = final

            # Orijinal verileri de kaydet (özet metrikler için)
            st.session_state.hesaplama_anlik_df = st.session_state.anlik_stok_satis.copy()
            st.session_state.hesaplama_depo_df = st.session_state.depo_stok.copy()

            bitis_zamani = time.time()
            algoritma_suresi = bitis_zamani - baslaangic_zamani

            # Progress tamamla ve temizle
            progress_bar.progress(100 / 100)
            status_text.success(f"✅ Hesaplama tamamlandı! ({algoritma_suresi:.1f} sn)")
            detail_text.empty()
            st.markdown("---")
            
            # ============================================
            # 📊 ÖZET METRİKLER TABLOSU - ORİJİNAL VERİLERDEN
            # ============================================
            st.subheader("📊 Hesaplama Özet Metrikleri")
            
            # ORİJİNAL CSV'LERDEN HESAPLA (FİLTRESİZ)
            orijinal_anlik = st.session_state.anlik_stok_satis.copy()
            orijinal_depo = st.session_state.depo_stok.copy()
            
            toplam_magaza_stok = orijinal_anlik['stok'].sum()  # Anlık_stok_satış.csv - stok toplamı
            toplam_yol = orijinal_anlik['yol'].sum()  # Anlık_stok_satış.csv - yol toplamı
            toplam_depo_stok = orijinal_depo['stok'].sum()  # depo.csv - stok toplamı
            toplam_satis = orijinal_anlik['satis'].sum()  # Anlık_stok_satış.csv - satış toplamı
            
            toplam_ihtiyac = final['ihtiyac_miktari'].sum()
            toplam_sevkiyat = final['sevkiyat_miktari'].sum()
            performans = (toplam_sevkiyat / toplam_ihtiyac * 100) if toplam_ihtiyac > 0 else 0
            magaza_sayisi = orijinal_anlik['magaza_kod'].nunique()
            urun_sayisi = orijinal_anlik['urun_kod'].nunique()
            sevk_olan_urun_sayisi = final[final['sevkiyat_miktari'] > 0]['urun_kod'].nunique()
            
            # Özet tablosu oluştur
            
            ozet_data = {
                'Metrik': [
                    '📦 Toplam Mağaza Stok',
                    '🚚 Toplam Yol',
                    '🏭 Toplam Depo Stok',
                    '💰 Toplam Satış',
                    '✅ Toplam Sevkiyat',
                    '⏱️ Algoritma Süresi (sn)',
                    '🏪 Mağaza Sayısı',
                    '🏷️ Ürün Sayısı',
                    '📤 Sevk Olan Ürün Sayısı'
                ],
                'Değer': [
                    str(f"{toplam_magaza_stok:,.0f}"),
                    str(f"{toplam_yol:,.0f}"),
                    str(f"{toplam_depo_stok:,.0f}"),
                    str(f"{toplam_satis:,.0f}"),
                    str(f"{toplam_sevkiyat:,.0f}"),
                    str(f"{algoritma_suresi:.2f} saniye"),
                    str(f"{magaza_sayisi:,}"),
                    str(f"{urun_sayisi:,}"),
                    str(f"{sevk_olan_urun_sayisi:,}")
                ]
            }             
            ozet_df = pd.DataFrame(ozet_data)
            
            # Tabloyu göster
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.dataframe(
                    ozet_df,
                    width='stretch',
                    hide_index=True,
                    height=380
                )
            
            with col2:
                # Önemli metrikler
                st.metric(
                    "🎯 Genel Performans", 
                    f"{performans:.1f}%",
                    delta=f"{performans - 100:.1f}%" if performans < 100 else "Hedef Aşıldı!"
                )
                
                st.metric(
                    "⚡ İşlem Süresi", 
                    f"{algoritma_suresi:.2f} sn"
                )
                
                # Stok durumu özeti
                toplam_stok_sistemi = toplam_magaza_stok + toplam_yol + toplam_depo_stok
                st.metric(
                    "💼 Toplam Sistem Stok",
                    f"{toplam_stok_sistemi:,.0f}"
                )
            
            # ============================================
            # 🎯 KPI KONTROL TABLOSU
            # ============================================
            st.markdown("---")
            st.subheader("🎯 KPI Kontrol Tablosu")
            
            try:
                # KPI hesaplamaları için orijinal veriden hesapla
                orijinal_df = st.session_state.anlik_stok_satis.copy()
                orijinal_depo = st.session_state.depo_stok.copy()
                
                # SADECE AKTİF NOKTALAR (stok > 0 OR satış > 0 OR yol > 0)
                aktif_df = orijinal_df[(orijinal_df['stok'] > 0) | (orijinal_df['satis'] > 0) | (orijinal_df['yol'] > 0)].copy()
                
                # Depo stok > 100 olan ürünleri bul (anlamlı sevkiyat yapılabilir)
                depo_stok_urun = orijinal_depo.groupby('urun_kod')['stok'].sum().reset_index()
                depo_stok_urun['urun_kod'] = depo_stok_urun['urun_kod'].astype(str)
                depo_stoklu_urunler = depo_stok_urun[depo_stok_urun['stok'] > 100]['urun_kod'].unique()
                
                # Cover hesapla (aktif noktalar için)
                aktif_df['cover'] = np.where(
                    aktif_df['satis'] > 0,
                    (aktif_df['stok'] + aktif_df['yol']) / aktif_df['satis'],
                    0
                )
                
                # Toplam aktif nokta sayısı
                toplam_nokta_satisi = len(aktif_df)
                
                # Min/max kontrolü için KPI'dan değerleri al (ürün-mağaza bazında)
                # Basitleştirme: final df'den KPI_Min ve KPI_Max kullan
                if 'KPI_Min' in final.columns and 'KPI_Max' in final.columns:
                    # Final'den min/max ile birleştir
                    aktif_df['urun_kod'] = aktif_df['urun_kod'].astype(str)
                    aktif_df['magaza_kod'] = aktif_df['magaza_kod'].astype(str)
                    
                    kpi_lookup = final[['magaza_kod', 'urun_kod', 'KPI_Min', 'KPI_Max']].drop_duplicates()
                    kpi_lookup['magaza_kod'] = kpi_lookup['magaza_kod'].astype(str)
                    kpi_lookup['urun_kod'] = kpi_lookup['urun_kod'].astype(str)
                    
                    aktif_df = aktif_df.merge(kpi_lookup, on=['magaza_kod', 'urun_kod'], how='left')
                    aktif_df['KPI_Min'] = aktif_df['KPI_Min'].fillna(0)
                    aktif_df['KPI_Max'] = aktif_df['KPI_Max'].fillna(999999)
                    
                    # Min altı: (stok+yol) < KPI_Min VE depo stok > 0
                    aktif_df['depo_stoklu'] = aktif_df['urun_kod'].isin(depo_stoklu_urunler)
                    min_alti_stok = len(aktif_df[
                        ((aktif_df['stok'] + aktif_df['yol']) < aktif_df['KPI_Min']) & 
                        (aktif_df['depo_stoklu'] == True)
                    ])
                    
                    # Maks üstü: (stok+yol) > KPI_Max
                    maks_ustu_stok = len(aktif_df[(aktif_df['stok'] + aktif_df['yol']) > aktif_df['KPI_Max']])
                else:
                    # Fallback: ortalama min/max kullan
                    if st.session_state.kpi is not None and not st.session_state.kpi.empty:
                        avg_min = st.session_state.kpi['min_deger'].mean() if 'min_deger' in st.session_state.kpi.columns else 0
                        avg_max = st.session_state.kpi['max_deger'].mean() if 'max_deger' in st.session_state.kpi.columns else 999999
                    else:
                        avg_min = 0
                        avg_max = 999999
                    
                    aktif_df['urun_kod'] = aktif_df['urun_kod'].astype(str)
                    aktif_df['depo_stoklu'] = aktif_df['urun_kod'].isin(depo_stoklu_urunler)
                    
                    min_alti_stok = len(aktif_df[
                        ((aktif_df['stok'] + aktif_df['yol']) < avg_min) & 
                        (aktif_df['depo_stoklu'] == True)
                    ])
                    maks_ustu_stok = len(aktif_df[(aktif_df['stok'] + aktif_df['yol']) > avg_max])
                
                # Diğer metrikler
                cover_12_ustu = len(aktif_df[aktif_df['cover'] > 12])
                cover_4_alti = len(aktif_df[(aktif_df['cover'] < 4) & (aktif_df['cover'] > 0)])
                ihtiyac_100_sevk_0 = len(final[(final['ihtiyac_miktari'] > 100) & (final['sevkiyat_miktari'] == 0)])
                
                # BKM filtresi - sadece aktif noktalar için (Aktif_Nokta = 1)
                if brut_kar_aktif and 'Aktif_Nokta' in final.columns and 'KPI_Durum' in final.columns:
                    brut_marj_filtre = len(final[(final['Aktif_Nokta'] == 1) & (final['KPI_Durum'].str.contains('BKM_Filtre', na=False))])
                elif brut_kar_aktif:
                    brut_marj_filtre = brut_kar_filtre_sayisi
                else:
                    brut_marj_filtre = 0
                
                kpi_kontrol_data = {
                    'KPI Metriği': [
                        '📊 Toplam Aktif Nokta (stok/satış/yol > 0)',
                        '⚠️ Min Altında Stok (depo stok > 100)',
                        '🔴 Maks Üstü Stok Noktası',
                        '📈 Cover > 12 Hafta Nokta Sayısı',
                        '📉 Cover < 4 Hafta Nokta Sayısı',
                        '❌ İhtiyaç > 100 ama Sevkiyat = 0',
                        '💰 Brüt Marj Sınırına Takılan'
                    ],
                    'Değer': [
                        f"{toplam_nokta_satisi:,}",
                        f"{min_alti_stok:,}",
                        f"{maks_ustu_stok:,}",
                        f"{cover_12_ustu:,}",
                        f"{cover_4_alti:,}",
                        f"{ihtiyac_100_sevk_0:,}",
                        f"{brut_marj_filtre:,}"
                    ],
                    'Oran %': [
                        "100%",
                        f"{min_alti_stok/toplam_nokta_satisi*100:.1f}%" if toplam_nokta_satisi > 0 else "0%",
                        f"{maks_ustu_stok/toplam_nokta_satisi*100:.1f}%" if toplam_nokta_satisi > 0 else "0%",
                        f"{cover_12_ustu/toplam_nokta_satisi*100:.1f}%" if toplam_nokta_satisi > 0 else "0%",
                        f"{cover_4_alti/toplam_nokta_satisi*100:.1f}%" if toplam_nokta_satisi > 0 else "0%",
                        f"{ihtiyac_100_sevk_0/len(final)*100:.1f}%" if len(final) > 0 else "0%",
                        f"{brut_marj_filtre/toplam_nokta_satisi*100:.1f}%" if toplam_nokta_satisi > 0 else "0%"
                    ]
                }
                
                kpi_kontrol_df = pd.DataFrame(kpi_kontrol_data)
                st.dataframe(kpi_kontrol_df, width='stretch', hide_index=True, height=300)
            except Exception as kpi_err:
                st.warning(f"⚠️ KPI tablosu oluşturulamadı: {str(kpi_err)}")
            
            # Status'u güncelle
            status_text.success("✅ Hesaplama tamamlandı!")
            
            st.info("📊 Detaylı raporlar ve indirme seçenekleri için **Raporlar** menüsüne gidin.")
            
        except Exception as e:
            st.error(f"❌ Hesaplama hatası: {str(e)}")
            import traceback
            st.code(traceback.format_exc())


# ============================================
# 📈 RAPORLAR 
# ============================================
elif menu == "📈 Raporlar":
    st.title("📈 Raporlar ve Analizler")
    st.markdown("---")
    
    if st.session_state.sevkiyat_sonuc is None:
        st.error("⚠️ Henüz hesaplama yapılmadı!")
        st.info("Lütfen önce 'Hesaplama' menüsünden hesaplama yapın.")
        st.stop()
    
    # Veriyi session state'ten al (copy YOK - sadece okuma)
    result_df = st.session_state.sevkiyat_sonuc
    
    st.success(f"✅ Hesaplama sonucu: {len(result_df):,} satır")
    
    # Kolon isimlerini belirle
    sevkiyat_kolon = 'sevkiyat_miktari' if 'sevkiyat_miktari' in result_df.columns else 'sevkiyat_gercek'
    ihtiyac_kolon = 'ihtiyac_miktari' if 'ihtiyac_miktari' in result_df.columns else 'ihtiyac'
    kayip_kolon = 'stok_yoklugu_satis_kaybi' if 'stok_yoklugu_satis_kaybi' in result_df.columns else 'stok_yoklugu_kaybi'
    
    # TAB'LAR - Sadece seçilen tab yüklenir
    tab1, tab2, tab3, tab4 = st.tabs([
        "📦 Ürün Analizi",
        "🏪 Mağaza Analizi", 
        "🗺️ İl Bazında",
        "📥 Dışa Aktar"
    ])


    # ============================================
    # ÜRÜN ANALİZİ - SADELEŞTİRİLMİŞ VERSİYON
    # ============================================        
    with tab1:
        st.subheader("📦 Ürün Bazında Analiz")
        
        st.markdown("### 📊 Ürün Cover Grup (Segment) Bazında Özet")
        
        segment_ozet = result_df.groupby('urun_segment').agg({
            'urun_kod': 'nunique',
        ihtiyac_kolon: 'sum',
        sevkiyat_kolon: 'sum',
        kayip_kolon: 'sum'
    }).reset_index()
        
        segment_ozet.columns = ['Ürün Segmenti', 'Ürün Sayısı', 'Toplam İhtiyaç', 'Toplam Sevkiyat', 'Toplam Kayıp']
        
        segment_ozet['Karşılama %'] = np.where(
            segment_ozet['Toplam İhtiyaç'] > 0,
            (segment_ozet['Toplam Sevkiyat'] / segment_ozet['Toplam İhtiyaç'] * 100),
            0
        ).round(1)
        
        segment_ozet = segment_ozet.sort_values('Ürün Segmenti')
        
        st.dataframe(segment_ozet, width='stretch', hide_index=True, height=250)


        
       
    # ============================================
    # MAĞAZA ANALİZİ - SADELEŞTİRİLMİŞ VERSİYON
    # ============================================
    with tab2:
        st.subheader("🏪 Mağaza Bazında Analiz")
        
        sevkiyat_kolon = 'sevkiyat_miktari' if 'sevkiyat_miktari' in result_df.columns else 'sevkiyat_gercek'
        ihtiyac_kolon = 'ihtiyac_miktari' if 'ihtiyac_miktari' in result_df.columns else 'ihtiyac'
        kayip_kolon = 'stok_yoklugu_satis_kaybi' if 'stok_yoklugu_satis_kaybi' in result_df.columns else 'stok_yoklugu_kaybi'
        
        st.markdown("### 📊 Mağaza Cover Grup (Segment) Bazında Özet")
        
        magaza_segment_ozet = result_df.groupby('magaza_segment').agg({
            'magaza_kod': 'nunique',
            ihtiyac_kolon: 'sum',
            sevkiyat_kolon: 'sum',
            kayip_kolon: 'sum'
        }).reset_index()
        
        magaza_segment_ozet.columns = ['Mağaza Segmenti', 'Mağaza Sayısı', 'Toplam İhtiyaç', 'Toplam Sevkiyat', 'Toplam Kayıp']
        
        magaza_segment_ozet['Karşılama %'] = np.where(
            magaza_segment_ozet['Toplam İhtiyaç'] > 0,
            (magaza_segment_ozet['Toplam Sevkiyat'] / magaza_segment_ozet['Toplam İhtiyaç'] * 100),
            0
        ).round(1)
        
        magaza_segment_ozet['Sevkiyat/Mağaza'] = np.where(
            magaza_segment_ozet['Mağaza Sayısı'] > 0,
            (magaza_segment_ozet['Toplam Sevkiyat'] / magaza_segment_ozet['Mağaza Sayısı']),
            0
        ).round(0)
        
        magaza_segment_ozet = magaza_segment_ozet.sort_values('Mağaza Segmenti')
        
        st.dataframe(magaza_segment_ozet, width='stretch', hide_index=True, height=250)
    
    # ============================================
    # İL BAZINDA - SADELEŞTİRİLMİŞ
    # ============================================
    with tab3:
        st.subheader("🗺️ İl Bazında Sevkiyat")
        
        if st.session_state.magaza_master is None or 'il' not in st.session_state.magaza_master.columns:
            st.warning("⚠️ Mağaza Master'da il bilgisi yok!")
        else:
            # İl bazında verileri hazırla
            magaza_master_il = st.session_state.magaza_master[['magaza_kod', 'il']].copy()
            magaza_master_il['magaza_kod'] = magaza_master_il['magaza_kod'].astype(str)
            
            il_verileri = result_df.groupby('magaza_kod').agg({
                sevkiyat_kolon: 'sum',
                ihtiyac_kolon: 'sum'
            }).reset_index()
            il_verileri['magaza_kod'] = il_verileri['magaza_kod'].astype(str)
            
            il_verileri = il_verileri.merge(magaza_master_il, on='magaza_kod', how='left')
            
            # İl bazında toplamlar
            il_bazinda = il_verileri.groupby('il').agg({
                sevkiyat_kolon: 'sum',
                ihtiyac_kolon: 'sum',
                'magaza_kod': 'nunique'
            }).reset_index()
            
            il_bazinda.columns = ['İl', 'Toplam Sevkiyat', 'Toplam İhtiyaç', 'Mağaza Sayısı']
            il_bazinda['Sevkiyat/Mağaza'] = (il_bazinda['Toplam Sevkiyat'] / il_bazinda['Mağaza Sayısı']).round(0)
            il_bazinda['Karşılama %'] = np.where(
                il_bazinda['Toplam İhtiyaç'] > 0,
                (il_bazinda['Toplam Sevkiyat'] / il_bazinda['Toplam İhtiyaç'] * 100),
                0
            ).round(1)
            
            # Sıralı tablo göster
            il_siralama = il_bazinda.sort_values('Toplam Sevkiyat', ascending=False)
            st.dataframe(il_siralama, width='stretch', hide_index=True, height=400)
            
            # İl bazlı indirme
            from io import BytesIO
            il_buffer = BytesIO()
            il_siralama.to_excel(il_buffer, index=False, engine='openpyxl')
            il_buffer.seek(0)
            
            st.download_button(
                label="📥 İl Bazlı Rapor İndir",
                data=il_buffer.getvalue(),
                file_name="il_bazli_sevkiyat.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="il_rapor_indir"
            )
    
    # ============================================
    # 📥 DIŞA AKTAR TAB - CSV FORMATI
    # ============================================
    with tab4:
        st.subheader("📥 Sevkiyat Verilerini İndir")
        
        final = st.session_state.sevkiyat_sonuc
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📋 SAP Formatı")
            st.caption("Sadece pozitif sevkiyatlar (4 kolon)")
            
            sap_data = final[final['sevkiyat_miktari'] > 0][['magaza_kod', 'urun_kod', 'depo_kod', 'sevkiyat_miktari']]
            st.metric("Satır Sayısı", f"{len(sap_data):,}")
            
            sap_csv = sap_data.to_csv(index=False, encoding='utf-8-sig', sep=';')
            
            st.download_button(
                label="📥 SAP CSV İndir",
                data=sap_csv,
                file_name=f"sap_sevkiyat_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                key="sap_csv_indir"
            )
        
        with col2:
            st.markdown("### 📊 Tam Detay")
            st.caption("Tüm kolonlar dahil")
            
            st.metric("Satır Sayısı", f"{len(final):,}")
            
            full_csv = final.to_csv(index=False, encoding='utf-8-sig', sep=';')
            
            st.download_button(
                label="📥 Tam Detay CSV İndir",
                data=full_csv,
                file_name=f"sevkiyat_detay_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                key="full_csv_indir"
            )
        
        st.caption("💡 CSV dosyaları noktalı virgül (;) ile ayrılmıştır. Excel'de Veri > Metinden Al ile açabilirsiniz.")

# ============================================
# 💾 MASTER DATA OLUŞTURMA
# ============================================
elif menu == "💾 Master Data":
    st.title("💾 Master Data Oluşturma")
    st.markdown("---")
    
    st.warning("🚧 **Master Data modülü yakında yayında!** 🚧")
