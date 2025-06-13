import streamlit as st
import pandas as pd
from pages.functions import *
import folium
from streamlit_folium import st_folium
from folium.features import GeoJsonTooltip
import plotly.express as px

st.set_page_config(
    page_title="Información de Pilotos",
    page_icon=":bust_in_silhouette:",
    layout="wide",
)

st.title(":bust_in_silhouette: Información de Pilotos")
st.text(
    "Aquí puedes consultar información detallada sobre los pilotos de Fórmula 1 que han competido en su historia."
)

with st.spinner(
    "Cargando información de pilotos... (Esto puede tardar un momento la primera vez)"
):
    results = pd.read_csv("database/f1db-races-race-results.csv", low_memory=False)
    drivers_info = pd.read_csv("database/f1db-seasons-drivers.csv")
    drivers = pd.read_csv("database/f1db-drivers.csv")
    entries_info = pd.read_csv("database/f1db-seasons-entrants-drivers.csv")
    standings = pd.read_csv("database/f1db-seasons-driver-standings.csv")
    races = pd.read_csv("database/f1db-races.csv")
    countries = pd.read_csv("database/f1db-countries.csv")
    gp = pd.read_csv("database/f1db-grands-prix.csv")

    gp_countries = pd.merge(
        gp, countries, left_on="countryId", right_on="id", how="left"
    )

    world_geo = load_world_geometry()

df_droped = results.sort_values(by="raceId").drop_duplicates(
    subset="driverId", keep="last"
)

driver_names = df_droped["full_name"].tolist()

selected_driver = st.selectbox(
    "Selecciona un piloto", options=driver_names, index=0
)

filtered_df = df_droped[df_droped["full_name"] == selected_driver]
full_name = filtered_df["full_name"].values[0]
selected_id = filtered_df["driverId"].values[0]

try:
    photo_url = load_driver_photo(full_name)

except Exception as e:
    st.warning(f"No se pudo obtener la foto del piloto: {e}")

st.markdown(f"### {filtered_df['full_name'].values[0]}")
col1, col2 = st.columns([2, 1])
with col1:
    selected_driver_name = filtered_df["full_name"].values[0]
    st.markdown(f"##### Ficha personal")
    st.markdown(f"- **Nombre completo**: {drivers.loc[drivers['id'] == selected_id, 'fullName'].values[0]}")
    st.markdown(f"- **Fecha de nacimiento**: {drivers.loc[drivers['id'] == selected_id, 'dateOfBirth'].values[0]}")
    countryBirth = drivers.loc[drivers["id"] == selected_id, "countryOfBirthCountryId"].values[0]
    st.markdown(f"- **Lugar de nacimiento**: {drivers.loc[drivers['id'] == selected_id, 'placeOfBirth'].values[0]} ({countries.loc[countries['id'] == countryBirth, 'name'].values[0]})")
    if pd.notna(drivers.loc[drivers['id'] == selected_id, 'dateOfDeath'].values[0]):
        st.markdown(f"- **Fecha de fallecimiento**: {drivers.loc[drivers['id'] == selected_id, 'dateOfDeath'].values[0]}")
    nationality = drivers.loc[drivers["id"] == selected_id, "nationalityCountryId"].values[0]
    st.markdown(f"- **Nacionalidad**: {countries.loc[countries["id"] == nationality, "name"].values[0]}")

    st.markdown(f"##### Estadísticas")
    dorsal = drivers.loc[drivers["id"] == selected_id, "permanentNumber"].values[0]
    if pd.notna(dorsal):
        st.markdown(f"- **Dorsal**: {int(dorsal)}")
    championships = standings[
        (standings["driverId"] == selected_id) & (standings["positionNumber"] == 1)
    ].shape[0]
    if championships:
        st.markdown(f"- **Campeonatos**: {championships}")
    total_wins = drivers_info.loc[
        drivers_info["driverId"] == selected_id, "totalRaceWins"
    ].sum()
    st.markdown(f"- **Victorias**: {total_wins}")
    total_podiums = drivers_info.loc[
        drivers_info["driverId"] == selected_id, "totalPodiums"
    ].sum()
    st.markdown(f"- **Podios**: {total_podiums}")
    total_poles = drivers_info.loc[
        drivers_info["driverId"] == selected_id, "totalPolePositions"
    ].sum()
    st.markdown(f"- **Pole Positions**: {total_poles}")
    total_races = drivers_info.loc[
        drivers_info["driverId"] == selected_id, "totalRaceStarts"
    ].sum()
    st.markdown(f"- **Carreras**: {total_races}")

with col2:
    if 'photo_url' in locals() and photo_url:
        st.image(photo_url, caption="", width=250)

with st.expander("Ver análisis de fiabilidad"):
    driver_results = results[results['driverId'] == selected_id]
    
    if not driver_results.empty:
        is_finished_numeric = pd.to_numeric(driver_results['positionText'], errors='coerce').notna()
        
        finished_count = is_finished_numeric.sum()
        dnf_count = len(driver_results) - finished_count

        reliability_data = pd.DataFrame({
            "Estado": ["Carreras Finalizadas", "Abandonos / No Finalizadas"],
            "Cantidad": [finished_count, dnf_count]
        })

        fig_pie = px.pie(
            reliability_data,
            names='Estado',
            values='Cantidad',
            title=f"<b>Resumen de Fiabilidad para {selected_driver_name}</b>",
            color_discrete_sequence=['#007bff', '#ff4d4d']
        )
        fig_pie.update_layout(
            title={
            'text': f"<b>Resumen de Fiabilidad para {selected_driver_name}</b>",
            'x': 0.5,
            'xanchor': 'center'
            },
            legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.35,  # Más alejada de la tarta
            xanchor="center",
            x=0.5
            )
        )
        fig_pie.update_traces(hole=0, textposition='inside', textinfo='percent')
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No hay datos de resultados de carrera para calcular la fiabilidad.")

st.markdown("---")

st.markdown("### Trayectoria del Piloto por Temporada")
career_data = drivers_info[drivers_info['driverId'] == selected_id].sort_values('year')

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
        title=f"<b>Evolución de {selected_metric_label} por Temporada para {selected_driver_name}</b>",
        labels={'year': 'Temporada', selected_metric_col: selected_metric_label},
        text_auto=True
    )
    fig.update_layout(
        title={
            'text': f"<b>Evolución de {selected_metric_label} por Temporada para {selected_driver_name}</b>",
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="Temporada",
        yaxis_title=f"Total de {selected_metric_label}",
        title_x=0.5
    )
    fig.update_traces(marker_color='#ff4d4d', textposition='outside')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No hay datos de rendimiento anual disponibles para este piloto.")

st.markdown("---")

if total_wins > 0 and world_geo is not None:
    wins_df = results[
        (results["driverId"] == selected_id) & (results["positionNumber"] == 1)
    ]
    wins_df = pd.merge(wins_df, races, on="raceId", how="left")
    world = world_geo.copy()
    wins_df = pd.merge(wins_df, gp[["id", "countryId"]], left_on="grandPrixId", right_on="id", how="left", suffixes=("", "_gp"))
    wins_df = pd.merge(wins_df, countries[["id", "name"]], left_on="countryId", right_on="id", how="left", suffixes=("", "_country"))
    wins_df["country"] = wins_df["name"]
    unmapped = wins_df[wins_df["country"].isna()]["grandPrixId"].unique()
    wins_by_country = (
        wins_df[wins_df["country"].notna()]
        .groupby("country")
        .size()
        .reset_index(name="victorias")
    )
    world = world.merge(
        wins_by_country, left_on="NAME", right_on="country", how="left"
    )
    world["victorias"] = world["victorias"].fillna(0)
    m = folium.Map(location=[20, 0], zoom_start=2)
    folium.GeoJson(
        world,
        style_function=lambda feature: {
            "fillColor": (
                "#ff4d4d" if feature["properties"]["victorias"] > 0 else "#cccccc"
            ),
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
            style=(
                "background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 5px;"
            ),
        ),
    ).add_to(m)
    st.markdown("#### Países donde ha conseguido victorias")
    st_folium(m, width=900, height=500, returned_objects=[])