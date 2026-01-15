import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io

st.set_page_config(
    page_title="Mağaza Transfer",
    page_icon="🔄",
    layout="wide"
)

# CSS - Yazı Tiplerini Küçült
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

# ============================================
# VERİ KONTROL
# ============================================
st.title("🔄 Otomatik Transfer")
st.markdown("---")

required_data = {
    'urun_master': 'Ürün Master',
    'magaza_master': 'Mağaza Master',
    'depo_stok': 'Depo Stok',
    'anlik_stok_satis': 'Anlık Stok/Satış',
    'kpi': 'KPI'
}

missing_data = []
for key, name in required_data.items():
    if st.session_state.get(key) is None:
        missing_data.append(name)

if missing_data:
    st.error(f"❌ **Eksik Veri:** {', '.join(missing_data)}")
    st.info("👉 Lütfen önce **Veri Yükleme** sayfasından gerekli dosyaları yükleyin.")
    if st.button("📤 Veri Yükleme Sayfasına Git"):
        st.switch_page("pages/0_Veri_Yukleme.py")
    st.stop()

# Verileri yükle
urun_master = st.session_state.urun_master.copy()
magaza_master = st.session_state.magaza_master.copy()
depo_stok = st.session_state.depo_stok.copy()
anlik_stok_satis = st.session_state.anlik_stok_satis.copy()
kpi = st.session_state.kpi.copy()

st.success("✅ Tüm veriler yüklendi!")

# ============================================
# FİLTRELEME PARAMETRELERİ
# ============================================
st.markdown("#### 🗺️ Bölge/İl Seçimi")

col1, col2 = st.columns([1, 2])

with col1:
    transfer_mode = st.selectbox(
        "Transfer Kapsamı:",
        options=['Bölge İçi', 'İl İçi', 'TR Geneli'],
        help="Hangi mağazalar arası transfer yapılacağını belirler"
    )

with col2:
    if transfer_mode == 'Bölge İçi':
        bolgeler = sorted(magaza_master['bolge'].unique())
        selected_bolge = st.selectbox("Bölge seçin:", bolgeler)
        st.info(f"🔍 Sadece **{selected_bolge}** bölgesindeki mağazalar arası transfer yapılacak")

    elif transfer_mode == 'İl İçi':
        iller = sorted(magaza_master['il'].unique())
        selected_iller = st.multiselect(
            "İl(ler) seçin:",
            iller,
            help="Birden fazla il seçebilirsiniz"
        )
        if not selected_iller:
            st.warning("⚠️ En az bir il seçmelisiniz")
        else:
            st.info(f"🔍 Seçilen iller: {', '.join(selected_iller)}")

    else:  # TR Geneli
        st.info("🌍 Tüm Türkiye genelinde transfer değerlendirmesi yapılacak")

st.markdown("---")

# Parametreler - Expander içinde
with st.expander("⚙️ Transfer Parametreleri", expanded=True):

    # Depo Stok Limiti
    st.markdown("**📦 Depo Stok Limiti**")
    col1, col2 = st.columns([1, 2])
    with col1:
        depo_limit_enabled = st.checkbox("Depo stok limiti uygula", value=False)
    with col2:
        if depo_limit_enabled:
            depo_limit = st.number_input(
                "Maksimum depo stok:",
                min_value=0,
                value=100,
                step=10,
                help="Bu değerin ALTINDA depo stoku olan ürünler transfer edilir"
            )
        else:
            depo_limit = 999999999
            st.caption("💡 Tüm ürünler değerlendirilecek")

    st.markdown("---")

    # Transfer Kuralları - 6 kolon kompakt
    st.markdown("**📏 Transfer Kuralları**")
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        min_transfer_per_pair = st.number_input(
            "Min transfer/çift:",
            min_value=1,
            value=50,
            step=10,
            help="Mağaza çifti bazında min transfer"
        )

    with col2:
        max_transfer_per_pair = st.number_input(
            "Max transfer/çift:",
            min_value=100,
            value=1000,
            step=100,
            help="Mağaza çifti bazında max transfer"
        )

    with col3:
        min_transfer_per_product = st.number_input(
            "Min ürün transferi:",
            min_value=1,
            value=2,
            step=1,
            help="Her ürün için min transfer adedi"
        )

    with col4:
        veren_min_kalan = st.number_input(
            "Verende min kalan:",
            min_value=0,
            value=2,
            step=1,
            help="Transfer sonrası veren mağazada kalacak min adet"
        )

    with col5:
        max_alan_per_veren = st.number_input(
            "Veren→Max alan:",
            min_value=1,
            value=10,
            step=1,
            help="Bir veren max kaç alana verir"
        )

    with col6:
        max_veren_per_alan = st.number_input(
            "Alan→Max veren:",
            min_value=1,
            value=10,
            step=1,
            help="Bir alan max kaç verenden alır"
        )

    st.markdown("---")

    # Cover Kuralları - 2 kolon
    st.markdown("**📊 Cover Kuralları**")
    col1, col2 = st.columns(2)

    with col1:
        alan_cover_max = st.number_input(
            "Alan Cover < (hafta):",
            min_value=1.0,
            max_value=20.0,
            value=8.0,
            step=0.5,
            help="Alan mağazalar için maksimum cover"
        )

    with col2:
        veren_cover_min = st.number_input(
            "Veren Cover ≥ (hafta):",
            min_value=4.0,
            max_value=52.0,
            value=15.0,
            step=1.0,
            help="Veren mağazalar için minimum cover"
        )

st.markdown("---")

# ============================================
# ÜRÜN HİYERARŞİSİ FİLTRELEME
# ============================================
st.subheader("🎯 Ürün Hiyerarşisi Filtreleme")

hierarchy_cols = ['umg', 'mg', 'marka_kod', 'kategori_kod', 'klasman_kod']
available_hierarchies = [col for col in hierarchy_cols if col in urun_master.columns]

if available_hierarchies:
    col1, col2, col3 = st.columns(3)

    filters = {}

    with col1:
        if 'umg' in available_hierarchies:
            umg_list = sorted(urun_master['umg'].dropna().unique())
            selected_umg = st.multiselect("UMG:", umg_list, help="Ürün Müdür Grubu")
            if selected_umg:
                filters['umg'] = selected_umg

        if 'marka_kod' in available_hierarchies:
            marka_list = sorted(urun_master['marka_kod'].dropna().unique())
            selected_marka = st.multiselect("Marka:", marka_list)
            if selected_marka:
                filters['marka_kod'] = selected_marka

    with col2:
        if 'mg' in available_hierarchies:
            mg_list = sorted(urun_master['mg'].dropna().unique())
            selected_mg = st.multiselect("MG:", mg_list, help="Müdür Grubu")
            if selected_mg:
                filters['mg'] = selected_mg

        if 'kategori_kod' in available_hierarchies:
            kategori_list = sorted(urun_master['kategori_kod'].dropna().unique())
            selected_kategori = st.multiselect("Kategori:", kategori_list)
            if selected_kategori:
                filters['kategori_kod'] = selected_kategori

    with col3:
        if 'klasman_kod' in available_hierarchies:
            klasman_list = sorted(urun_master['klasman_kod'].dropna().unique())
            selected_klasman = st.multiselect("Klasman:", klasman_list)
            if selected_klasman:
                filters['klasman_kod'] = selected_klasman

    # Filtreleri uygula
    filtered_urun = urun_master.copy()
    for col, values in filters.items():
        filtered_urun = filtered_urun[filtered_urun[col].isin(values)]

    if filters:
        st.info(f"🔍 Filtre sonrası ürün sayısı: **{len(filtered_urun):,}** / {len(urun_master):,}")
    else:
        st.info("💡 Filtre seçilmedi, tüm ürünler değerlendirilecek")
else:
    filtered_urun = urun_master.copy()
    st.warning("⚠️ Ürün hiyerarşisi kolonları bulunamadı")

st.markdown("---")

# ============================================
# TRANSFER HESAPLAMA BUTONU
# ============================================
if st.button("🚀 Transfer Önerilerini Hesapla", type="primary", use_container_width=True):

    with st.spinner("🔄 Transfer önerileri hesaplanıyor..."):

        try:
            st.write("🔄 [DEBUG] Transfer hesaplama başlıyor...")
            st.write(f"   magaza_master sütunları: {list(magaza_master.columns)}")
            st.write(f"   depo_stok sütunları: {list(depo_stok.columns)}")
        except Exception as e:
            st.error(f"❌ Debug hatası: {e}")

        # 1. Mağaza filtresi uygula
        if transfer_mode == 'Bölge İçi':
            filtered_magaza = magaza_master[magaza_master['bolge'] == selected_bolge].copy()
        elif transfer_mode == 'İl İçi':
            if not selected_iller:
                st.error("❌ Lütfen en az bir il seçin!")
                st.stop()
            filtered_magaza = magaza_master[magaza_master['il'].isin(selected_iller)].copy()
        else:  # TR Geneli
            filtered_magaza = magaza_master.copy()

        # 2. Depo stok filtresi (ALTINDAKI ürünler)
        if depo_limit_enabled:
            valid_urunler = depo_stok[depo_stok['stok'] <= depo_limit]['urun_kod'].unique()
            filtered_urun = filtered_urun[filtered_urun['urun_kod'].isin(valid_urunler)]
            st.info(f"📦 Depo stok limiti ({depo_limit:,} altındakiler) sonrası ürün sayısı: **{len(filtered_urun):,}**")

        # 3. Ana veriyi hazırla - KPI ile birleştir
        # Önce ürün master ile merge et (mg bilgisi için)
        df = anlik_stok_satis.merge(
            filtered_urun[['urun_kod', 'mg']],
            on='urun_kod',
            how='inner'
        ).merge(
            filtered_magaza[['magaza_kod', 'il', 'bolge', 'tip']],
            on='magaza_kod',
            how='inner'
        )

        # KPI ile merge (mg_id = mg)
        df = df.merge(
            kpi.rename(columns={'mg_id': 'mg'}),
            on='mg',
            how='left'
        )

        # KPI eksik olanlar için default değerler
        df['min_deger'] = df['min_deger'].fillna(100)
        df['max_deger'] = df['max_deger'].fillna(500)
        df['forward_cover'] = df['forward_cover'].fillna(2.0)

        if len(df) == 0:
            st.error("❌ Seçilen kriterlere uygun veri bulunamadı!")
            st.stop()

        # 4. ÖNCE MAĞAZA BAZINDA COVER HESAPLA VE MAĞAZALARI BELİRLE
        st.info("🏪 Mağazalar belirleniyor (ALAN/VEREN ayrımı)...")

        # Mağaza bazında toplam stok ve satış
        magaza_cover = df.groupby('magaza_kod').agg({
            'stok': 'sum',
            'yol': 'sum',
            'satis': 'sum'
        }).reset_index()

        magaza_cover['magaza_net_stok'] = magaza_cover['stok'] + magaza_cover['yol']
        magaza_cover['magaza_cover'] = np.where(
            magaza_cover['satis'] > 0,
            magaza_cover['magaza_net_stok'] / magaza_cover['satis'],
            999
        )

        # ALAN ve VEREN mağazaları BELİRLE (mağaza bazında)
        alan_magazalar = set(magaza_cover[magaza_cover['magaza_cover'] < alan_cover_max]['magaza_kod'])
        veren_magazalar = set(magaza_cover[magaza_cover['magaza_cover'] >= veren_cover_min]['magaza_kod'])

        st.write(f"📊 **Mağaza Bazında:** {len(alan_magazalar):,} ALAN, {len(veren_magazalar):,} VEREN mağaza belirlendi")

        # İkisi de olanları çıkar (bir mağaza ya alan ya veren)
        ortak = alan_magazalar & veren_magazalar
        if len(ortak) > 0:
            st.info(f"ℹ️ {len(ortak):,} mağaza hem alan hem veren kriterine uyuyor, bunlar çıkarılıyor")
            alan_magazalar = alan_magazalar - ortak
            veren_magazalar = veren_magazalar - ortak

        # DataFrame'e mağaza cover ekle
        df = df.merge(
            magaza_cover[['magaza_kod', 'magaza_cover']],
            on='magaza_kod',
            how='left'
        )

        # Ürün bazında cover hesapla
        df['net_stok'] = df['stok'] + df['yol']
        df['urun_cover'] = np.where(df['satis'] > 0, df['net_stok'] / df['satis'], 999)

        # 5. İhtiyaç hesapla (Sevkiyattaki gibi - RPT, Min, Initial'ın MAX'ı)

        # RPT ihtiyacı = forward_cover * satış - (stok + yol)
        # Hedef stok önce hesapla
        df['hedef_stok_raw'] = df['forward_cover'] * df['satis']
        # Max değeri aşmamalı
        df['hedef_stok'] = df[['hedef_stok_raw', 'max_deger']].min(axis=1)
        # RPT ihtiyacı
        df['rpt_ihtiyac'] = (df['hedef_stok'] - df['net_stok']).clip(lower=0)

        # Min ihtiyacı = min_deger - (stok + yol)
        df['min_ihtiyac'] = (df['min_deger'] - df['net_stok']).clip(lower=0)

        # Initial ihtiyacı (depo stoku yeterli VE mağaza stoku yoksa)
        # Basitleştirilmiş: stok+yol = 0 ise min_deger kadar ver
        df['initial_ihtiyac'] = np.where(
            df['net_stok'] <= 0,
            df['min_deger'],
            0
        )

        # Üç ihtiyacın MAX'ını al (Sevkiyattaki gibi)
        df['ihtiyac'] = df[['rpt_ihtiyac', 'min_ihtiyac', 'initial_ihtiyac']].max(axis=1)

        # Hangi ihtiyaç türü olduğunu belirle
        def ihtiyac_turu(row):
            if row['ihtiyac'] == 0:
                return 'Yok'
            elif row['ihtiyac'] == row['rpt_ihtiyac']:
                return 'RPT'
            elif row['ihtiyac'] == row['initial_ihtiyac'] and row['initial_ihtiyac'] > 0:
                return 'Initial'
            elif row['ihtiyac'] == row['min_ihtiyac']:
                return 'Min'
            else:
                return 'RPT'

        df['ihtiyac_turu'] = df.apply(ihtiyac_turu, axis=1)

        # 6. ÜRÜN BAZINDA Veren ve Alan pozisyonları belirle
        st.info("🎯 Ürün bazında ALAN/VEREN pozisyonları belirleniyor...")

        # Sadece belirlenen ALAN mağazalardan ve ürün cover kontrolü
        df['alan_mi'] = (
            df['magaza_kod'].isin(alan_magazalar) &  # Mağaza ALAN olmalı
            (df['urun_cover'] < alan_cover_max) &    # Ürün cover da düşük olmalı
            (df['ihtiyac'] > 0)                       # İhtiyaç olmalı
        )

        # Sadece belirlenen VEREN mağazalardan ve ürün cover kontrolü
        df['veren_mi'] = (
            df['magaza_kod'].isin(veren_magazalar) &  # Mağaza VEREN olmalı
            (df['urun_cover'] >= veren_cover_min) &   # Ürün cover da yüksek olmalı
            (df['yol'] <= df['satis'] * 0.5)          # Yol yok/az
        )

        veren_df = df[df['veren_mi']].copy()
        alan_df = df[df['alan_mi']].copy()

        st.success(f"✅ **Ürün Bazında:** {len(veren_df):,} veren, {len(alan_df):,} alan pozisyon tespit edildi")

        if len(veren_df) == 0 or len(alan_df) == 0:
            st.warning("⚠️ Yeterli veren veya alan mağaza bulunamadı!")
            st.info(f"💡 Cover kuralları: Veren Cover ≥ {veren_cover_min} hafta (yavaş dönenler), Alan Cover < {alan_cover_max} hafta (hızlı dönenler)")
            st.stop()

        # Debug bilgileri
        with st.expander("🔍 Debug Bilgileri", expanded=True):
            st.write("**Mağaza Ayrımı:**")
            st.write(f"- ALAN mağaza sayısı: {len(alan_magazalar):,}")
            st.write(f"- VEREN mağaza sayısı: {len(veren_magazalar):,}")

            st.write("\n**Ürün-Mağaza Pozisyonları:**")
            st.write(f"- Veren benzersiz ürün: {veren_df['urun_kod'].nunique():,}")
            st.write(f"- Veren benzersiz mağaza: {veren_df['magaza_kod'].nunique():,}")
            st.write(f"- Alan benzersiz ürün: {alan_df['urun_kod'].nunique():,}")
            st.write(f"- Alan benzersiz mağaza: {alan_df['magaza_kod'].nunique():,}")
            ortak_urunler = set(veren_df['urun_kod']) & set(alan_df['urun_kod'])
            st.write(f"- Ortak ürün sayısı: {len(ortak_urunler):,}")

            # İhtiyaç türü dağılımı
            st.write("\n**Alan İhtiyaç Türü Dağılımı:**")
            ihtiyac_dagilim = alan_df['ihtiyac_turu'].value_counts()
            for tur, count in ihtiyac_dagilim.items():
                st.write(f"- {tur}: {count:,}")

            # RPT ihtiyaç detayları
            st.write("\n**RPT İhtiyaç Detayları:**")
            rpt_count = (alan_df['rpt_ihtiyac'] > 0).sum()
            rpt_zero = (alan_df['rpt_ihtiyac'] == 0).sum()
            st.write(f"- RPT > 0: {rpt_count:,}")
            st.write(f"- RPT = 0: {rpt_zero:,}")
            if rpt_count > 0:
                st.write(f"- Ortalama RPT ihtiyaç: {alan_df[alan_df['rpt_ihtiyac'] > 0]['rpt_ihtiyac'].mean():.2f}")

            if len(ortak_urunler) > 0:
                st.write("\n**Örnek ortak ürün analizi (3 örnek):**")
                for i, sample_urun in enumerate(list(ortak_urunler)[:3]):
                    sample_veren = veren_df[veren_df['urun_kod'] == sample_urun].iloc[0]
                    sample_alan = alan_df[alan_df['urun_kod'] == sample_urun].iloc[0]

                    veren_fazla = sample_veren['net_stok']  # Tüm stok transfer edilebilir
                    alan_kapasite = max(0, sample_alan['max_deger'] - sample_alan['net_stok'])
                    alan_ihtiyac = min(sample_alan['ihtiyac'], alan_kapasite)
                    transfer = min(veren_fazla, alan_ihtiyac)

                    st.write(f"\n**Örnek {i+1}: {sample_urun}**")
                    st.write(f"- **VEREN Mağaza:** {sample_veren['magaza_kod']}, Mağaza Cover={sample_veren['magaza_cover']:.2f}")
                    st.write(f"- **VEREN Ürün:** net_stok={sample_veren['net_stok']:.0f}, ürün_cover={sample_veren['urun_cover']:.2f} → Fazla: {veren_fazla:.0f}")
                    st.write(f"- **ALAN Mağaza:** {sample_alan['magaza_kod']}, Mağaza Cover={sample_alan['magaza_cover']:.2f}")
                    st.write(f"- **ALAN Ürün:** stok={sample_alan['stok']:.0f}, yol={sample_alan['yol']:.0f}, satış={sample_alan['satis']:.0f}, ürün_cover={sample_alan['urun_cover']:.2f}, FC={sample_alan['forward_cover']:.2f}")
                    st.write(f"- **ALAN Hedef Stok:** FC×satış = {sample_alan['forward_cover']:.2f} × {sample_alan['satis']:.0f} = {sample_alan['hedef_stok_raw']:.0f} (max: {sample_alan['max_deger']:.0f}) → {sample_alan['hedef_stok']:.0f}")
                    st.write(f"- **ALAN RPT:** {sample_alan['hedef_stok']:.0f} - {sample_alan['net_stok']:.0f} = {sample_alan['rpt_ihtiyac']:.0f}")
                    st.write(f"- **ALAN Min:** {sample_alan['min_deger']:.0f} - {sample_alan['net_stok']:.0f} = {sample_alan['min_ihtiyac']:.0f}")
                    st.write(f"- **ALAN Initial:** {sample_alan['initial_ihtiyac']:.0f}")
                    st.write(f"- **ALAN Final ({sample_alan['ihtiyac_turu']}):** {sample_alan['ihtiyac']:.0f}, Kapasite: {alan_kapasite:.0f}")
                    st.write(f"- **Transfer:** min({veren_fazla:.0f}, {alan_ihtiyac:.0f}) = {transfer:.0f}")

        # 7. Transfer eşleştirme - VEREN OPTİMİZASYONU (Veren döngüsü)
        st.info("🔄 Transfer eşleştirmeleri yapılıyor (Veren optimizasyonu)...")

        transfer_list = []

        # Veren mağaza başına transfer yapılacak alan mağaza sayısını takip et
        veren_alan_counter = {}  # veren_magaza -> set(alan_magaza)

        # VEREN döngüsü (her veren için en iyi alanları bul)
        for _, veren_row in veren_df.iterrows():
            veren_magaza = veren_row['magaza_kod']
            urun = veren_row['urun_kod']
            veren_il = veren_row['il']
            veren_bolge = veren_row['bolge']

            # Veren tarafta: tüm net_stok transfer edilebilir
            veren_fazla = veren_row['net_stok']

            if veren_fazla <= 0:
                continue

            # Aynı ürün için alan mağazaları bul
            potential_alans = alan_df[alan_df['urun_kod'] == urun].copy()

            if len(potential_alans) == 0:
                continue

            # Bölge/İl kuralına göre filtrele
            if transfer_mode == 'Bölge İçi':
                potential_alans = potential_alans[potential_alans['bolge'] == veren_bolge]
            elif transfer_mode == 'İl İçi':
                potential_alans = potential_alans[potential_alans['il'].isin(selected_iller)]

            if len(potential_alans) == 0:
                continue

            # Kendisi olamaz
            potential_alans = potential_alans[potential_alans['magaza_kod'] != veren_magaza]

            if len(potential_alans) == 0:
                continue

            # Brüt kar potansiyeline göre sırala (en yüksek brüt kar potansiyeli)
            potential_alans['brut_kar_potansiyel'] = (
                potential_alans['ciro'] / potential_alans['satis'].replace(0, 1)
            ) * potential_alans['ihtiyac']
            potential_alans = potential_alans.sort_values('brut_kar_potansiyel', ascending=False)

            # Bu veren için transfer yap
            kalan_veren_stok = veren_fazla

            for _, alan_row in potential_alans.iterrows():
                if kalan_veren_stok <= 0:
                    break

                alan_magaza = alan_row['magaza_kod']
                alan_ihtiyac = alan_row['ihtiyac']

                # Alan tarafta: max_deger'e kadar alabilir
                alan_kapasite = max(0, alan_row['max_deger'] - alan_row['net_stok'])

                # İhtiyaç ile de sınırla
                alan_ihtiyac_final = min(alan_ihtiyac, alan_kapasite)

                # Transfer miktarı hesapla
                transfer_miktar = min(kalan_veren_stok, alan_ihtiyac_final)

                # Min ürün transferi kontrolü
                if transfer_miktar < min_transfer_per_product:
                    continue  # Bu ürün için transfer yapma

                # Veren mağazada kalacak stok kontrolü
                # Eğer transfer sonrası kalan < veren_min_kalan ise, tamamını gönder
                kalan_sonrasi = kalan_veren_stok - transfer_miktar
                if 0 < kalan_sonrasi < veren_min_kalan:
                    transfer_miktar = kalan_veren_stok  # Tamamını gönder

                if transfer_miktar > 0:
                    # Brüt kar tutarı hesapla
                    birim_fiyat = alan_row['ciro'] / alan_row['satis'] if alan_row['satis'] > 0 else 0
                    brut_kar_tutar = birim_fiyat * transfer_miktar

                    transfer_list.append({
                        'urun_kod': urun,
                        'veren_magaza': veren_magaza,
                        'veren_il': veren_il,
                        'veren_bolge': veren_bolge,
                        'veren_magaza_cover': round(veren_row['magaza_cover'], 2),
                        'veren_urun_cover': round(veren_row['urun_cover'], 2),
                        'veren_stok': veren_row['stok'],
                        'veren_yol': veren_row['yol'],
                        'veren_satis': veren_row['satis'],
                        'veren_forward_cover': veren_row['forward_cover'],
                        'alan_magaza': alan_magaza,
                        'alan_il': alan_row['il'],
                        'alan_bolge': alan_row['bolge'],
                        'alan_magaza_cover': round(alan_row['magaza_cover'], 2),
                        'alan_urun_cover': round(alan_row['urun_cover'], 2),
                        'alan_stok': alan_row['stok'],
                        'alan_yol': alan_row['yol'],
                        'alan_satis': alan_row['satis'],
                        'alan_forward_cover': alan_row['forward_cover'],
                        'alan_ihtiyac_turu': alan_row['ihtiyac_turu'],
                        'alan_rpt_ihtiyac': round(alan_row['rpt_ihtiyac'], 0),
                        'alan_min_ihtiyac': round(alan_row['min_ihtiyac'], 0),
                        'alan_initial_ihtiyac': round(alan_row['initial_ihtiyac'], 0),
                        'transfer_miktar': round(transfer_miktar, 0),
                        'alan_ihtiyac': round(alan_ihtiyac, 0),
                        'brut_kar_tutar': round(brut_kar_tutar, 2),
                        'min_deger': veren_row['min_deger'],
                        'max_deger': alan_row['max_deger']
                    })

                    # Veren stoktan düş
                    kalan_veren_stok -= transfer_miktar

                    # Veren-alan ilişkisini kaydet
                    if veren_magaza not in veren_alan_counter:
                        veren_alan_counter[veren_magaza] = set()
                    veren_alan_counter[veren_magaza].add(alan_magaza)

        # Veren mağaza başına kaç alan mağazaya transfer yapıldığını göster
        if len(veren_alan_counter) > 0:
            avg_alan_per_veren = sum(len(alans) for alans in veren_alan_counter.values()) / len(veren_alan_counter)
            max_alan_for_veren = max(len(alans) for alans in veren_alan_counter.values())
            st.success(f"✅ Veren başına ortalama {avg_alan_per_veren:.1f} alan mağaza, maksimum {max_alan_for_veren} alan mağaza")

        # Debug sonuçları
        st.info(f"📊 Potansiyel transfer (ürün bazlı): {len(transfer_list):,}")

        if len(transfer_list) == 0:
            st.warning("⚠️ Transfer önerisi bulunamadı!")
            st.info("💡 Filtre kriterlerinizi kontrol edin (Cover, bölge/il seçimi, vb.)")
            st.stop()

        # 8. DataFrame'e çevir
        transfer_df = pd.DataFrame(transfer_list)

        # 8.5. Mağaza çifti bazında MIN kontrolü
        st.info(f"🔍 Mağaza çifti bazında min {min_transfer_per_pair:,} adet kontrolü yapılıyor...")

        try:
            # Mağaza çifti bazında toplam hesapla
            magaza_cift_toplam = transfer_df.groupby(['veren_magaza', 'alan_magaza'])['transfer_miktar'].sum().reset_index()
            magaza_cift_toplam.columns = ['veren_magaza', 'alan_magaza', 'toplam_transfer']

            # Min'den fazla olanları al
            valid_pairs = magaza_cift_toplam[magaza_cift_toplam['toplam_transfer'] >= min_transfer_per_pair][['veren_magaza', 'alan_magaza']]

            # Sadece valid çiftleri tut
            transfer_df = transfer_df.merge(valid_pairs, on=['veren_magaza', 'alan_magaza'], how='inner')

            removed_count = len(transfer_list) - len(transfer_df)
            st.info(f"✂️ {removed_count:,} ürün-mağaza eşleşmesi (min {min_transfer_per_pair:,} adet altındaki mağaza çiftleri) çıkarıldı")
        except Exception as e:
            st.error(f"❌ Min kontrol hatası: {str(e)}")
            st.error(f"transfer_df sütunları: {list(transfer_df.columns)}")
            st.stop()

        if len(transfer_df) == 0:
            st.warning("⚠️ Min limit kontrolü sonrası transfer kalmadı!")
            st.info(f"💡 Tüm mağaza çiftlerinin toplam transferi {min_transfer_per_pair:,} adet altında. Min limiti azaltıp tekrar deneyin.")
            st.stop()

        # Depo stok bilgisini ekle (eğer depo_kod sütunu varsa)
        st.write(f"🔄 [DEBUG] Depo kod kontrolü: magaza_master={('depo_kod' in magaza_master.columns)}, depo_stok={('depo_kod' in depo_stok.columns)}")

        try:
            if 'depo_kod' in magaza_master.columns and 'depo_kod' in depo_stok.columns:
                st.write("🔄 [DEBUG] Depo bilgisi ekleniyor...")
                # Veren mağazanın depo kodunu al
                veren_depo = magaza_master[['magaza_kod', 'depo_kod']].rename(columns={'magaza_kod': 'veren_magaza', 'depo_kod': 'veren_depo_kod'})
                transfer_df = transfer_df.merge(veren_depo, on='veren_magaza', how='left')
                st.write("🔄 [DEBUG] Veren depo eklendi")

                # Alan mağazanın depo kodunu al
                alan_depo = magaza_master[['magaza_kod', 'depo_kod']].rename(columns={'magaza_kod': 'alan_magaza', 'depo_kod': 'alan_depo_kod'})
                transfer_df = transfer_df.merge(alan_depo, on='alan_magaza', how='left')
                st.write("🔄 [DEBUG] Alan depo eklendi")

                # Depo stok miktarlarını ekle
                depo_stok_veren = depo_stok.rename(columns={'depo_kod': 'veren_depo_kod', 'stok': 'veren_depo_stok'})
                transfer_df = transfer_df.merge(
                    depo_stok_veren[['veren_depo_kod', 'urun_kod', 'veren_depo_stok']],
                    on=['veren_depo_kod', 'urun_kod'],
                    how='left'
                )
                st.write("🔄 [DEBUG] Veren depo stok eklendi")

                depo_stok_alan = depo_stok.rename(columns={'depo_kod': 'alan_depo_kod', 'stok': 'alan_depo_stok'})
                transfer_df = transfer_df.merge(
                    depo_stok_alan[['alan_depo_kod', 'urun_kod', 'alan_depo_stok']],
                    on=['alan_depo_kod', 'urun_kod'],
                    how='left'
                )
                st.write("🔄 [DEBUG] Alan depo stok eklendi")

                # Depo stok boş olanları 0 yap
                transfer_df['veren_depo_stok'] = transfer_df['veren_depo_stok'].fillna(0)
                transfer_df['alan_depo_stok'] = transfer_df['alan_depo_stok'].fillna(0)
            else:
                # Depo bilgisi yoksa boş sütunlar ekle
                transfer_df['veren_depo_kod'] = None
                transfer_df['alan_depo_kod'] = None
                transfer_df['veren_depo_stok'] = 0
                transfer_df['alan_depo_stok'] = 0
                st.warning("⚠️ Mağaza Master'da 'depo_kod' sütunu bulunamadı, depo stok bilgisi eklenmedi.")
        except Exception as e:
            st.error(f"❌ Depo stok hatası: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            st.stop()

        # 9. Mağaza bazında gruplama ve limitler
        st.info(f"📊 Mağaza çifti limitleri uygulanıyor (Max {max_transfer_per_pair:,} adet/çift, Max {max_alan_per_veren} alan/veren, Max {max_veren_per_alan} veren/alan)...")

        # Önce mağaza çifti bazında topla ve brüt kara göre sırala
        magaza_cift_summary = transfer_df.groupby(['veren_magaza', 'alan_magaza']).agg({
            'transfer_miktar': 'sum',
            'brut_kar_tutar': 'sum'
        }).reset_index()
        magaza_cift_summary.columns = ['veren_magaza', 'alan_magaza', 'total_miktar', 'total_brut_kar']

        # Brüt kara göre sırala (yüksekten düşüğe)
        magaza_cift_summary = magaza_cift_summary.sort_values('total_brut_kar', ascending=False)

        # Her veren ve alan için counter
        veren_counter = {}  # veren_magaza -> alan mağaza sayısı
        alan_counter = {}   # alan_magaza -> veren mağaza sayısı

        selected_pairs = []

        for _, row in magaza_cift_summary.iterrows():
            veren = row['veren_magaza']
            alan = row['alan_magaza']

            # Limit kontrolü
            veren_count = veren_counter.get(veren, 0)
            alan_count = alan_counter.get(alan, 0)

            if veren_count >= max_alan_per_veren:
                continue  # Bu veren mağaza limitini doldurdu

            if alan_count >= max_veren_per_alan:
                continue  # Bu alan mağaza limitini doldurdu

            # Bu çifti seç
            selected_pairs.append((veren, alan))
            veren_counter[veren] = veren_count + 1
            alan_counter[alan] = alan_count + 1

        # Seçilen çiftleri filtrele
        transfer_df['pair_key'] = list(zip(transfer_df['veren_magaza'], transfer_df['alan_magaza']))
        transfer_df = transfer_df[transfer_df['pair_key'].isin(selected_pairs)]
        transfer_df = transfer_df.drop('pair_key', axis=1)

        removed_by_store_limit = len(magaza_cift_summary) - len(selected_pairs)
        st.info(f"🏪 {removed_by_store_limit} mağaza çifti (mağaza sayısı limiti) çıkarıldı")

        if len(transfer_df) == 0:
            st.warning("⚠️ Mağaza sayısı limiti sonrası transfer kalmadı!")
            st.stop()

        # 9.5. Mağaza çifti başına max adet limiti uygula
        final_transfers = []

        for (veren, alan), group in transfer_df.groupby(['veren_magaza', 'alan_magaza']):
            toplam_miktar = group['transfer_miktar'].sum()

            if toplam_miktar > max_transfer_per_pair:
                # Brüt kar tutarına göre sırala (yüksekten düşüğe)
                group = group.sort_values('brut_kar_tutar', ascending=False)

                # Max adede ulaşana kadar al
                kumulatif = 0
                for idx, row in group.iterrows():
                    if kumulatif >= max_transfer_per_pair:
                        break

                    kalan_kapasite = max_transfer_per_pair - kumulatif
                    if row['transfer_miktar'] <= kalan_kapasite:
                        final_transfers.append(row.to_dict())
                        kumulatif += row['transfer_miktar']
                    else:
                        # Son ürünü parçalı al
                        if kalan_kapasite >= min_transfer_per_product:  # Min adet kontrolü
                            row_dict = row.to_dict()
                            row_dict['transfer_miktar'] = kalan_kapasite
                            row_dict['brut_kar_tutar'] = row_dict['brut_kar_tutar'] * (kalan_kapasite / row['transfer_miktar'])
                            final_transfers.append(row_dict)
                            kumulatif += kalan_kapasite
            else:
                # Max altında, tümünü al
                final_transfers.extend(group.to_dict('records'))

        transfer_df = pd.DataFrame(final_transfers)

        if len(transfer_df) == 0:
            st.warning(f"⚠️ {max_transfer_per_pair:,} adet limiti uygulandıktan sonra transfer kalmadı!")
            st.stop()

        # Ürün detayları ekle
        if 'marka_kod' in urun_master.columns:
            transfer_df = transfer_df.merge(
                urun_master[['urun_kod', 'marka_kod', 'kategori_kod']],
                on='urun_kod',
                how='left'
            )

        # 10. Sonuçları göster
        st.markdown("---")
        st.subheader("📊 Transfer Önerileri")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Toplam Transfer Önerisi", f"{len(transfer_df):,}")
        with col2:
            st.metric("Toplam Ürün Adedi", f"{transfer_df['transfer_miktar'].sum():,.0f}")
        with col3:
            st.metric("Benzersiz Ürün", f"{transfer_df['urun_kod'].nunique():,}")
        with col4:
            st.metric("Toplam Brüt Kar", f"{transfer_df['brut_kar_tutar'].sum():,.0f} ₺")

        st.markdown("---")

        # 11. Detaylı tablo
        st.dataframe(
            transfer_df,
            use_container_width=True,
            height=400,
            hide_index=True
        )

        # 12. Özet istatistikler
        st.markdown("---")
        st.subheader("📈 Özet İstatistikler")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Veren Mağaza Dağılımı (İl)**")
            veren_il_dist = transfer_df.groupby('veren_il').agg({
                'transfer_miktar': 'sum',
                'brut_kar_tutar': 'sum',
                'urun_kod': 'count'
            }).reset_index()
            veren_il_dist.columns = ['İl', 'Toplam Miktar', 'Brüt Kar (₺)', 'Transfer Sayısı']
            st.dataframe(veren_il_dist, use_container_width=True, hide_index=True)

        with col2:
            st.markdown("**Alan Mağaza Dağılımı (İl)**")
            alan_il_dist = transfer_df.groupby('alan_il').agg({
                'transfer_miktar': 'sum',
                'brut_kar_tutar': 'sum',
                'urun_kod': 'count'
            }).reset_index()
            alan_il_dist.columns = ['İl', 'Toplam Miktar', 'Brüt Kar (₺)', 'Transfer Sayısı']
            st.dataframe(alan_il_dist, use_container_width=True, hide_index=True)

        # Mağaza çifti özeti
        st.markdown("**Mağaza Çifti Özeti (En Yüksek 20)**")
        magaza_cift = transfer_df.groupby(['veren_magaza', 'alan_magaza']).agg({
            'transfer_miktar': 'sum',
            'brut_kar_tutar': 'sum',
            'urun_kod': 'count'
        }).reset_index().nlargest(20, 'transfer_miktar')
        magaza_cift.columns = ['Veren Mağaza', 'Alan Mağaza', 'Toplam Miktar', 'Brüt Kar (₺)', 'Ürün Sayısı']
        st.dataframe(magaza_cift, use_container_width=True, hide_index=True)

        # 13. Excel Export
        st.markdown("---")
        st.subheader("📥 Excel Export")

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            transfer_df.to_excel(writer, sheet_name='Transfer Önerileri', index=False)
            veren_il_dist.to_excel(writer, sheet_name='Veren İl Dağılımı', index=False)
            alan_il_dist.to_excel(writer, sheet_name='Alan İl Dağılımı', index=False)
            magaza_cift.to_excel(writer, sheet_name='Mağaza Çifti Özeti', index=False)

        output.seek(0)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"transfer_onerileri_{timestamp}.xlsx"

        st.download_button(
            label="📥 Excel İndir",
            data=output,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        st.success("✅ Transfer analizi tamamlandı!")

st.markdown("---")
st.caption("🔄 Mağazalar Arası Transfer Modülü v2.0")
