import streamlit as st

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="Retail Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Basit ve temiz
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
        color: #1f77b4;
    }
    .info-box {
        background-color: #f0f8ff;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Ana başlık
st.markdown('<div class="main-header">📊 Retail Analytics Sistemi</div>', unsafe_allow_html=True)
st.markdown("---")

# Giriş
st.markdown("""
## 👋 Hoşgeldiniz!

Bu sistem, retail operasyonlarınızı optimize etmek için geliştirilmiş modüler bir çözümdür.
""")

# Modül kartları
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 📤 Veri Yönetimi
    
    **Veri Yükleme Modülü**
    - CSV dosya yükleme
    - Veri doğrulama
    - Session yönetimi
    - Format kontrolleri
    
    👉 *Tüm modüller için veri girişi buradan yapılır*
    """)
    
    if st.button("📤 Veri Yükleme'ye Git", use_container_width=True):
        st.switch_page("pages/0_Veri_Yukleme.py")

with col2:
    st.markdown("""
    ### 💵 Alım Sipariş (PO)
    
    **Purchase Order Modülü**
    - Cover bazlı hesaplama
    - Kar marjı filtreleme
    - Koli yuvarlaması
    - Depo bazlı çıktılar
    
    👉 *Tedarikçi sipariş optimizasyonu*
    """)
    
    if st.button("💵 Alım Sipariş'e Git", use_container_width=True):
        st.switch_page("pages/4_PO.py")

st.markdown("---")

# Diğer modüller
st.markdown("### 📋 Diğer Modüller")

col1, col2, col3 = st.columns(3)

with col1:
    with st.container():
        st.markdown("#### 📉 Lost Sales")
        st.caption("Kayıp satış analizi")
        if st.button("🔍 Lost Sales", use_container_width=True, key="lost"):
            st.switch_page("pages/1_Lost_Sales.py")

with col2:
    with st.container():
        st.markdown("#### 🚚 Sevkiyat")
        st.caption("Mağaza sevkiyat optimizasyonu")
        if st.button("📦 Sevkiyat", use_container_width=True, key="sevk"):
            st.switch_page("pages/2_Sevkiyat.py")

with col3:
    with st.container():
        st.markdown("#### 📦 Prepack")
        st.caption("Prepack optimizasyonu")
        if st.button("🎁 Prepack", use_container_width=True, key="prepack"):
            st.switch_page("pages/3_Prepack_Optimization.py")

st.markdown("---")

# Footer
st.markdown("---")
st.caption("🚀 Retail Analytics v2.0 | Made with ❤️ using Streamlit")
