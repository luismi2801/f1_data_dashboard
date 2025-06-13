import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.features import GeoJsonTooltip
import plotly.express as px

# Asumiendo que estas funciones de carga existen en pages/functions.py
from pages.functions import (
    load_world_geometry,
    load_driver_photo, 
)

st.set_page_config(
    page_title="Información de Escuderías",
    page_icon="🏢",
    layout="wide",
)

# --- Carga de Datos ---
@st.cache_data
def load_all_team_data():
    results = pd.read_csv("database/f1db-races-race-results.csv", low_memory=False)
    teams_per_season = pd.read_csv("database/f1db-seasons-constructors.csv")
    constructors = pd.read_csv("database/f1db-constructors.csv")
    standings = pd.read_csv("database/f1db-seasons-constructor-standings.csv")
    races = pd.read_csv("database/f1db-races.csv")
    countries = pd.read_csv("database/f1db-countries.csv")
    gp = pd.read_csv("database/f1db-grands-prix.csv")
    world_geo = load_world_geometry()
    
    return results, teams_per_season, constructors, standings, races, countries, gp, world_geo

with st.spinner("Cargando información de escuderías..."):
    results, teams_per_season, constructors, standings, races, countries, gp, world_geo = load_all_team_data()

st.title("🏢 Información de Escuderías")
st.text("Aquí puedes consultar información detallada sobre las escuderías de Fórmula 1.")
# st.success("Información de escuderías cargada correctamente.")

df_droped = results.sort_values(by="raceId").drop_duplicates(subset="constructorId", keep="last")
team_names = sorted(df_droped["team_full_name"].dropna().unique())
selected_team_name = st.selectbox("Selecciona una escudería", options=team_names, index=team_names.index("Red Bull"))

filtered_df = df_droped[df_droped["team_full_name"] == selected_team_name]
selected_id = filtered_df["constructorId"].values[0]

try:
    photo_url = load_driver_photo(selected_team_name)
except Exception as e:
    st.warning(f"No se pudo obtener el logo de la escudería: {e}")

st.markdown(f"### {selected_team_name}")
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown(f"##### Ficha de la escudería")
    constructor_details = constructors.loc[constructors["id"] == selected_id].iloc[0]
    st.markdown(f"- **Nombre completo**: {constructor_details['fullName']}")
    team_country_id = constructor_details["countryId"]
    st.markdown(f"- **País de origen**: {countries.loc[countries['id'] == team_country_id, 'name'].values[0]}")
    
    st.markdown(f"##### Estadísticas")
    championships = standings[(standings["constructorId"] == selected_id) & (standings["positionNumber"] == 1)].shape[0]
    if championships > 0:
        st.markdown(f"- **Campeonatos**: {championships}")
    
    total_wins = constructor_details["totalRaceWins"]
    st.markdown(f"- **Victorias**: {int(total_wins)}")
    
    total_podiums = constructor_details["totalPodiums"]
    st.markdown(f"- **Podios**: {int(total_podiums)}")
    
    total_poles = constructor_details["totalPolePositions"]
    st.markdown(f"- **Pole Positions**: {int(total_poles)}")

    total_1_2_finishes = constructor_details["total1And2Finishes"]
    st.markdown(f"- **Dobletes (1-2)**: {int(total_1_2_finishes)}")
    
    total_races = constructor_details["totalRaceStarts"]
    st.markdown(f"- **Carreras**: {int(total_races)}")

with col2:
    if 'photo_url' in locals() and photo_url:
        st.image(photo_url, caption="", width=250)

st.markdown("---")

st.markdown("### Trayectoria de la Escudería por Temporada")
career_data = teams_per_season[teams_per_season['constructorId'] == selected_id].sort_values('year')

if not career_data.empty:
    metric_options = {
        "Puntos": "totalPoints",
        "Victorias": "totalRaceWins",
        "Podios": "totalPodiums",
        "Pole Positions": "totalPolePositions"
    }
    selected_metric_label = st.radio(
        "Selecciona una métrica para visualizar su evolución anual:",
        options=list(metric_options.keys()),
        horizontal=True,
    )
    selected_metric_col = metric_options[selected_metric_label]

    fig = px.bar(
        career_data,
        x='year',
        y=selected_metric_col,
        title=f"<b>Evolución de {selected_metric_label} por Temporada para {selected_team_name}</b>",
        labels={'year': 'Temporada', selected_metric_col: selected_metric_label},
        text_auto=True,
    )
    fig.update_layout(
        title={'x': 0.5, 'xanchor': 'center'},
        xaxis_title="Temporada",
        yaxis_title=f"Total de {selected_metric_label}",
    )
    fig.update_traces(marker_color='#007bff', textposition='outside')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No hay datos de rendimiento anual disponibles para esta escudería.")

st.markdown("---")

total_wins_career = int(constructor_details["totalRaceWins"])

if total_wins_career > 0 and world_geo is not None:
    wins_df = results[(results["constructorId"] == selected_id) & (results["positionNumber"] == 1)]
    wins_df = pd.merge(wins_df, races, on="raceId", how="left")
    
    world = world_geo.copy()
    
    wins_df = pd.merge(wins_df, gp[["id", "countryId"]], left_on="grandPrixId", right_on="id", how="left", suffixes=("", "_gp"))
    wins_df = pd.merge(wins_df, countries[["id", "name"]], left_on="countryId", right_on="id", how="left", suffixes=("", "_country"))
    wins_df["country"] = wins_df["name"]

    wins_by_country = wins_df[wins_df["country"].notna()].groupby("country").size().reset_index(name="victorias")
    
    world = world.merge(wins_by_country, left_on="NAME", right_on="country", how="left")
    world["victorias"] = world["victorias"].fillna(0)
    
    m = folium.Map(location=[20, 0], zoom_start=2)
    
    folium.GeoJson(
        world,
        style_function=lambda feature: {
            "fillColor": "#007bff" if feature["properties"]["victorias"] > 0 else "#cccccc",
            "color": "black",
            "weight": 0.5,
            "fillOpacity": 0.7 if feature["properties"]["victorias"] > 0 else 0.2,
        },
        tooltip=GeoJsonTooltip(
            fields=["NAME", "victorias"],
            aliases=["País", "Victorias"],
            localize=True,
            sticky=True,
            labels=True,
            style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 5px;"),
        ),
    ).add_to(m)
    
    st.markdown("#### Países donde ha conseguido victorias")
    st_folium(m, width=900, height=500)