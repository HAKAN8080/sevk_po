import streamlit as st
import pandas as pd
import numpy as np



# Sayfa konfigürasyonu
st.set_page_config(
    page_title="Prepack Optimization",
    page_icon="📦",
    layout="wide"
)


st.info("🚧 **Yapım Aşamasında**")
st.write("Bu sayfa şu anda geliştirme aşamasındadır. Yakında kullanıma sunulacaktır.")

# Boşluk için
for _ in range(8):
    st.write("")
