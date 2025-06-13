import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import geopandas as gpd
from shapely.geometry import Point
import requests
import io

st.set_page_config(
    page_title="Información de Grandes Premios",
    page_icon="🏆",
    layout="wide",
)

@st.cache_data
def load_gadm_data(country_code):
    url = f"https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_{country_code}_shp.zip"
    try:
        response = requests.get(url)
        response.raise_for_status()
        zipfile_in_memory = io.BytesIO(response.content)
        gdf = gpd.read_file(zipfile_in_memory)
        return gdf
    except requests.exceptions.HTTPError:
        return None
    except Exception:
        return None

def get_region_name(properties):
    if 'NAME_2' in properties and pd.notna(properties['NAME_2']):
        return properties['NAME_2']
    if 'NAME_1' in properties and pd.notna(properties['NAME_1']):
        return properties['NAME_1']
    if 'COUNTRY' in properties and pd.notna(properties['COUNTRY']):
        return properties['COUNTRY']
    return None

with st.spinner("Cargando información..."):
    races = pd.read_csv("database/f1db-races.csv")
    results = pd.read_csv("database/f1db-races-race-results.csv", low_memory=False)
    circuits = pd.read_csv("database/f1db-circuits.csv")
    grands_prix = pd.read_csv("database/f1db-grands-prix.csv")
    drivers = pd.read_csv("database/f1db-drivers.csv")
    countries = pd.read_csv("database/f1db-countries.csv")
    results = results.merge(drivers[['id', 'nationalityCountryId']], left_on='driverId', right_on='id', how='left')

st.title("🏆 Información de Grandes Premios")
st.text("Explora las estadísticas y la historia de cada Gran Premio de Fórmula 1.")

gp_names = sorted(grands_prix['fullName'].dropna().unique())
default_gp = "Monaco Grand Prix"
default_index = 0
if default_gp in gp_names:
    default_index = gp_names.index(default_gp)

selected_gp_name = st.selectbox(
    "Selecciona un Gran Premio",
    options=gp_names,
    index=default_index
)

selected_gp_id = grands_prix[grands_prix['fullName'] == selected_gp_name]['id'].iloc[0]
races_in_gp = races[races['grandPrixId'] == selected_gp_id]
race_ids_in_gp = races_in_gp['raceId'].unique()
results_in_gp = results[results['raceId'].isin(race_ids_in_gp)]
wins_in_gp = results_in_gp[results_in_gp['positionNumber'] == 1]

st.header(f"Estadísticas de {selected_gp_name}")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Veces Disputado", len(race_ids_in_gp))
with col2:
    if not wins_in_gp.empty:
        top_driver = wins_in_gp['full_name'].mode()[0]
        top_driver_wins = wins_in_gp['full_name'].value_counts().max()
        st.metric("Piloto con más victorias", top_driver, f"{top_driver_wins} victorias")
    else:
        st.metric("Piloto con más victorias", "N/A")
with col3:
    if not wins_in_gp.empty:
        top_team = wins_in_gp['team_full_name'].mode()[0]
        top_team_wins = wins_in_gp['team_full_name'].value_counts().max()
        st.metric("Escudería con más victorias", top_team, f"{top_team_wins} victorias")
    else:
        st.metric("Escudería con más victorias", "N/A")

st.markdown("---")

tab1, tab2 = st.tabs(["🗺️ Circuitos y Regiones", "🌍 Nacionalidad de los Pilotos"])

with tab1:
    st.subheader(f"Ubicación de los Circuitos del {selected_gp_name}")
    circuits_used_ids = races_in_gp['circuitId'].unique()
    circuits_used_df = circuits[circuits['id'].isin(circuits_used_ids)]
    
    if circuits_used_df.empty:
        st.info("No hay información de circuitos para este Gran Premio.")
    else:
        unique_country_ids = circuits_used_df['countryId'].unique()
        gadm_gdf = None
        
        if len(unique_country_ids) == 1:
            country_id = unique_country_ids[0]
            country_info = countries[countries['id'] == country_id]
            if not country_info.empty:
                country_code = country_info['alpha3Code'].iloc[0]
                with st.spinner(f"Cargando mapa regional para {country_code}..."):
                    gadm_gdf = load_gadm_data(country_code)

        map_center_lat = circuits_used_df['latitude'].mean()
        map_center_lon = circuits_used_df['longitude'].mean()
        m1 = folium.Map(location=[map_center_lat, map_center_lon], zoom_start=5, tiles="CartoDB positron")

        if gadm_gdf is not None:
            active_regions = set()
            for idx, circuit_row in circuits_used_df.iterrows():
                point = Point(circuit_row['longitude'], circuit_row['latitude'])
                containing_region_gdf = gadm_gdf[gadm_gdf.contains(point)]
                if not containing_region_gdf.empty:
                    region_properties = containing_region_gdf.iloc[0]
                    region_name = get_region_name(region_properties)
                    if region_name:
                        active_regions.add(region_name)

            def style_function(feature):
                region_name = get_region_name(feature['properties'])
                is_active = region_name is not None and region_name in active_regions
                return {
                    'fillColor': '#3186cc' if is_active else '#cccccc',
                    'color': 'black',
                    'weight': 1,
                    'fillOpacity': 0.7 if is_active else 0.2,
                }
            
            desired_fields = ['COUNTRY', 'NAME_1', 'NAME_2']
            available_fields = [field for field in desired_fields if field in gadm_gdf.columns]
            
            aliases_map = {'COUNTRY': 'País:', 'NAME_1': 'Región 1:', 'NAME_2': 'Región 2:'}
            available_aliases = [aliases_map[field] for field in available_fields]

            folium.GeoJson(
                gadm_gdf,
                style_function=style_function,
                tooltip=folium.features.GeoJsonTooltip(
                    fields=available_fields,
                    aliases=available_aliases
                )
            ).add_to(m1)
        
        else:
            if len(circuits_used_df) > 1:
                sw = circuits_used_df[['latitude', 'longitude']].min().values.tolist()
                ne = circuits_used_df[['latitude', 'longitude']].max().values.tolist()
                m1.fit_bounds([sw, ne], padding=(30, 30))

        for idx, row in circuits_used_df.iterrows():
            popup_html = f"<b>{row['fullName']}</b><br>Lugar: {row['placeName']}"
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=row['name'],
                icon=folium.Icon(color='red', icon='flag-checkered', prefix='fa')
            ).add_to(m1)
        
        st_folium(m1, width=1200, height=500)

with tab2:
    st.subheader(f"Estadísticas por nacionalidad de piloto en el {selected_gp_name}")

    if not results_in_gp.empty:
        metric_options = {
            "Victorias": "victories",
            "Podios": "podiums",
            "Pole Positions": "poles",
            "Puntos Totales": "points"
        }
        selected_metric_label = st.radio(
            "Selecciona una métrica para visualizar:",
            options=list(metric_options.keys()),
            horizontal=True,
            label_visibility="collapsed"
        )
        selected_metric_key = metric_options[selected_metric_label]

        results_with_nationality = results_in_gp.merge(countries[['id', 'name', 'alpha3Code']], left_on='nationalityCountryId', right_on='id', how='left')
        
        data_for_map = None
        
        if selected_metric_key == "victories":
            filtered_data = results_with_nationality[results_with_nationality['positionNumber'] == 1]
            if not filtered_data.empty:
                data_for_map = filtered_data['name'].value_counts().reset_index()
                data_for_map.columns = ['country', 'value']

        elif selected_metric_key == "podiums":
            filtered_data = results_with_nationality[results_with_nationality['positionNumber'].isin([1, 2, 3])]
            if not filtered_data.empty:
                data_for_map = filtered_data['name'].value_counts().reset_index()
                data_for_map.columns = ['country', 'value']

        elif selected_metric_key == "poles":
            filtered_data = results_with_nationality[results_with_nationality['gridPositionNumber'] == 1]
            if not filtered_data.empty:
                data_for_map = filtered_data['name'].value_counts().reset_index()
                data_for_map.columns = ['country', 'value']
        
        elif selected_metric_key == "points":
            results_with_nationality['points'] = pd.to_numeric(results_with_nationality['points'], errors='coerce').fillna(0)
            points_by_country = results_with_nationality.groupby('name')['points'].sum().reset_index()
            points_by_country = points_by_country[points_by_country['points'] > 0]
            if not points_by_country.empty:
                data_for_map = points_by_country
                data_for_map.columns = ['country', 'value']

        if data_for_map is not None and not data_for_map.empty:
            plot_data = data_for_map.merge(countries[['name', 'alpha3Code']], left_on='country', right_on='name', how='left')

            fig = px.choropleth(
                plot_data,
                locations="alpha3Code",
                color="value",
                hover_name="country",
                hover_data={"value": True, "alpha3Code": False},
                color_continuous_scale=px.colors.sequential.Plasma,
                projection="natural earth",
            )
            
            fig.update_layout(
                coloraxis_colorbar_title=selected_metric_label,
                margin={"r":0,"t":40,"l":0,"b":0}
            )
            fig.update_traces(
                hovertemplate='<b>%{hovertext}</b><br>%{customdata[0]} ' + selected_metric_label.lower() + '<extra></extra>'
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"No hay datos de '{selected_metric_label}' para este Gran Premio.")

    else:
        st.info("No hay datos de resultados para este Gran Premio.")