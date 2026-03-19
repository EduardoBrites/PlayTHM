import pandas as pd
import folium
import geopandas as gpd
import streamlit as st
from streamlit_folium import st_folium
import streamlit.components.v1 as components

st.set_page_config(page_title="PlayTennis - THM", page_icon="🎾")

st.title("Estudo de Mercado")

st.divider()

with open("mapa.html", "r", encoding="utf-8") as f:
    html_code = f.read()

components.html(html_code, height=600)
