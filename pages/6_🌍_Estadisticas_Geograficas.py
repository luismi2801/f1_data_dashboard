import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import geopandas as gpd
from pages.functions import load_world_geometry, fuzzy_match_countries

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Estadísticas Geográficas",
    page_icon="🌍",
    layout="wide",
)

st.title("🌍 Estadísticas Geográficas de la F1")
st.markdown("Visualiza la distribución mundial de talento y éxito en la Fórmula 1.")

@st.cache_data
def load_data():
    drivers = pd.read_csv("database/f1db-drivers.csv")
    constructors = pd.read_csv("database/f1db-constructors.csv")
    countries = pd.read_csv("database/f1db-countries.csv")
    
    drivers = drivers.merge(countries[['id', 'name']], left_on='nationalityCountryId', right_on='id', how='left')
    drivers.rename(columns={'name_y': 'countryName'}, inplace=True)
    
    constructors = constructors.merge(countries[['id', 'name']], left_on='countryId', right_on='id', how='left')
    constructors.rename(columns={'name_y': 'countryName'}, inplace=True)

    world_geo = load_world_geometry()
    
    return drivers, constructors, world_geo

with st.spinner("Cargando datos y geometría..."):
    drivers_df, constructors_df, world_geo = load_data()
    

if world_geo is None:
    st.error("No se pudo cargar la geometría del mapa. La visualización no es posible.")
else:
    st.sidebar.header("Filtros del Mapa")
    entity_type = st.sidebar.radio(
        "Analizar por:",
        ("Pilotos", "Escuderías")
    )

    if entity_type == "Pilotos":
        metric_options = {
            "Campeonatos del Mundo": "totalChampionshipWins",
            "Victorias Totales": "totalRaceWins",
            "Pole Positions Totales": "totalPolePositions",
            "Podios Totales": "totalPodiums",
            "Número de Pilotos": "id"
        }
    else: # Escuderías
        metric_options = {
            "Campeonatos del Mundo": "totalChampionshipWins",
            "Victorias Totales": "totalRaceWins",
            "Pole Positions Totales": "totalPolePositions",
            "Podios Totales": "totalPodiums",
            "Número de Escuderías": "id"
        }
        
    selected_metric_name = st.sidebar.selectbox(
        "Selecciona la métrica a visualizar:",
        options=list(metric_options.keys())
    )
    selected_metric_col = metric_options[selected_metric_name]

    st.header(f"Mapa de Coropletas: {selected_metric_name} por {entity_type}")

    if entity_type == "Pilotos":
        if selected_metric_col == "id": 
            data_agg = drivers_df.groupby('countryName').size().reset_index(name=selected_metric_col)
        else:
            data_agg = drivers_df.groupby('countryName')[selected_metric_col].sum().reset_index()
    else: # Escuderías
        if selected_metric_col == "id": 
            data_agg = constructors_df.groupby('countryName').size().reset_index(name=selected_metric_col)
        else:
            data_agg = constructors_df.groupby('countryName')[selected_metric_col].sum().reset_index()

    world_map_data = world_geo.merge(data_agg, left_on="NAME", right_on="countryName", how="left")
    world_map_data[selected_metric_col] = world_map_data[selected_metric_col].fillna(0)

    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB positron")

    choropleth = folium.Choropleth(
        geo_data=world_map_data,
        data=world_map_data,
        columns=['NAME', selected_metric_col],
        key_on='feature.properties.NAME',
        fill_color='YlOrRd', 
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name=f"{selected_metric_name} por País",
        highlight=True
    ).add_to(m)

    folium.GeoJsonTooltip(
        fields=['NAME', selected_metric_col],
        aliases=['País:', f'{selected_metric_name}:'],
        style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;")
    ).add_to(choropleth.geojson)
    
    st_folium(m, width=1200, height=600)