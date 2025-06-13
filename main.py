import streamlit as st
import pandas as pd
import numpy as np
import json
import random

st.set_page_config(
    page_title="F1 Stats Dashboard",
    page_icon="🏎️",
    layout="wide"
)

@st.cache_data
def load_main_stats():
    try:
        drivers = pd.read_csv("database/f1db-drivers.csv")
        races = pd.read_csv("database/f1db-races.csv")
        constructors = pd.read_csv("database/f1db-constructors.csv")
        return len(drivers), len(races), len(constructors)
    except FileNotFoundError:
        return 0, 0, 0

total_drivers, total_races, total_constructors = load_main_stats()

st.title("🏎️ F1 Stats Dashboard 🏎️")
st.markdown("### Bienvenido al centro de análisis definitivo para los aficionados de la Fórmula 1")

with open("images.json", "r", encoding="utf-8") as f:
    images = json.load(f)
random_image = random.choice(images)
st.markdown(
    f"<div style='display: flex; justify-content: center;'><img src='{random_image['url']}' width='900'></div>",
    unsafe_allow_html=True
)

st.markdown("---")

col1, col2, col3 = st.columns(3)
col1.metric("Pilotos Históricos", f"{total_drivers}", "en la base de datos")
col2.metric("Carreras Disputadas", f"{total_races}", "registradas")
col3.metric("Escuderías Únicas", f"{total_constructors}", "a lo largo de la historia")

st.markdown("---")

st.header("Todas las funciones")
st.write("Usa los siguientes enlaces para navegar a las diferentes secciones de análisis.")

c1, c2 = st.columns(2)

with c1:
    with st.container(border=True):
        st.subheader("👤 Análisis de Pilotos")
        st.write("Investiga la carrera, estadísticas y victorias de cada piloto.")
        if st.button("Ir a Información de Pilotos", key="pilotos", use_container_width=True):
            st.switch_page("pages/informacion_pilotos.py")

    with st.container(border=True):
        st.subheader("📅 Información de Grandes Premios")
        st.write("Descubre qué pilotos y equipos dominan en cada circuito.")
        if st.button("Ir a Información de GP", key="gp", use_container_width=True):
            st.switch_page("pages/informacion_gp.py")

    with st.container(border=True):
        st.subheader("🌍 Estadísticas Geográficas")
        st.write("Visualiza la distribución mundial de campeones y victorias.")
        if st.button("Ir a Estadísticas Geográficas", key="geo", use_container_width=True):
            st.switch_page("pages/estadisticas_geograficas.py")

with c2:
    with st.container(border=True):
        st.subheader("🏢 Análisis de Escuderías")
        st.write("Compara el rendimiento y la trayectoria histórica de los equipos.")
        if st.button("Ir a Información sobre Escuderías", key="escuderias", use_container_width=True):
            st.switch_page("pages/informacion_escuderias.py")

    with st.container(border=True):
        st.subheader("🏁 Resultados Históricos")
        st.write("Busca los resultados detallados de cualquier sesión de F1.")
        if st.button("Ir a Resultados Históricos", key="resultados", use_container_width=True):
            st.switch_page("pages/resultados_historicos.py")

    with st.container(border=True):
        st.subheader("📊 Comparativa por Temporada")
        st.write("Compara cara a cara a los pilotos a lo largo de los años.")
        if st.button("Ir a Análisis de Temporada", key="analisis", use_container_width=True):
            st.switch_page("pages/analisis_temporada.py")

st.markdown("---")