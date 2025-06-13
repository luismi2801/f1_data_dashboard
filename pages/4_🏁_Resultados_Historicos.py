import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(
    page_title="Resultados Históricos",
    page_icon="🏁",
    layout="wide",
)

@st.cache_data
def load_historical_data():
    try:
        data = {
            "Carrera": pd.read_csv("database/f1db-races-race-results.csv", low_memory=False),
            "Clasificación": pd.read_csv("database/f1db-races-qualifying-results.csv", low_memory=False),
            "Carrera Sprint": pd.read_csv("database/f1db-races-sprint-race-results.csv", low_memory=False),
            "Clasificación Sprint": pd.read_csv("database/f1db-races-sprint-qualifying-results.csv", low_memory=False),
            "Libres 1": pd.read_csv("database/f1db-races-free-practice-1-results.csv", low_memory=False),
            "Libres 2": pd.read_csv("database/f1db-races-free-practice-2-results.csv", low_memory=False),
            "Libres 3": pd.read_csv("database/f1db-races-free-practice-3-results.csv", low_memory=False),
        }

        races = pd.read_csv("database/f1db-races.csv")
        grands_prix = pd.read_csv("database/f1db-grands-prix.csv")
        pit_stops = pd.read_csv("database/f1db-races-pit-stops.csv")

        drivers = pd.read_csv("database/f1db-drivers.csv")[['id', 'name']].rename(columns={'name': 'full_name'})
        constructors = pd.read_csv("database/f1db-constructors.csv")[['id', 'fullName']].rename(columns={'fullName': 'team_full_name'})

        for key, df in data.items():
            if 'full_name' not in df.columns and 'driverId' in df.columns:
                df = df.merge(drivers, left_on='driverId', right_on='id', how='left')
                df = df.merge(constructors, left_on='constructorId', right_on='id', how='left')
                data[key] = df
        
        pit_stops['durationSeconds'] = pd.to_numeric(pit_stops['time'], errors='coerce')
        pit_stops = pit_stops.merge(drivers, left_on='driverId', right_on='id', how='left')
        pit_stops.rename(columns={'full_name': 'Piloto'}, inplace=True)

        return data, races, grands_prix, pit_stops
    except FileNotFoundError as e:
        st.error(f"Error: No se encontró el archivo {e.filename}.")
        return None, None, None, None

data_sessions, races, grands_prix, pit_stops = load_historical_data()

st.title("🏁 Resultados Históricos")
st.text("Busca y visualiza los resultados de cualquier sesión en la historia de la Fórmula 1.")

if data_sessions:
    col1, col2, col3 = st.columns(3)

    with col1:
        years = sorted(races['year'].unique(), reverse=True)
        selected_year = st.selectbox("Selecciona el Año", options=years)

    with col2:
        races_in_year = races[races['year'] == selected_year]
        gp_in_year = grands_prix[grands_prix['id'].isin(races_in_year['grandPrixId'])]
        gp_names = sorted(gp_in_year['fullName'].unique()) if not gp_in_year.empty else []
        selected_gp_name = st.selectbox("Selecciona el Gran Premio", options=gp_names)

    with col3:
        if selected_gp_name:
            gp_id = grands_prix[grands_prix['fullName'] == selected_gp_name]['id'].iloc[0]
            race_info_row = races_in_year[races_in_year['grandPrixId'] == gp_id]
            if not race_info_row.empty:
                race_id = race_info_row.iloc[0]['raceId']

                available_sessions = []
                for session_name, df in data_sessions.items():
                    if not df.empty and 'raceId' in df.columns and race_id in df['raceId'].unique():
                        available_sessions.append(session_name)

                selected_session = st.selectbox("Selecciona la Sesión", options=available_sessions) if available_sessions else None
            else:
                race_id, selected_session = None, None
        else:
            race_id, selected_session = None, None

    if race_id and selected_session:
        st.subheader(f"Resultados de {selected_session} - {selected_gp_name} {selected_year}")

        session_df = data_sessions[selected_session]
        results_df = session_df[session_df['raceId'] == race_id].copy()

        if all(col in results_df.columns for col in ['positionNumber', 'time', 'gap']):
            results_df['time_or_gap'] = np.where(
                results_df['positionNumber'] == 1,
                results_df['time'],
                results_df['gap']
            )
        elif 'time' in results_df.columns:
            results_df['time_or_gap'] = results_df['time']

        columns_to_show = {
            'positionText': 'Pos.',
            'driverNumber': 'Nº',
            'full_name': 'Piloto',
            'team_full_name': 'Escudería',
            'time_or_gap': 'Tiempo/Gap',
            'laps': 'Vueltas',
            'points': 'Puntos'
        }

        display_columns_map = {original: new for original, new in columns_to_show.items() if original in results_df.columns}

        st.dataframe(results_df[list(display_columns_map.keys())].rename(columns=display_columns_map), use_container_width=True, hide_index=True)

        st.markdown("---")
        
        pit_stops_in_race = pit_stops[pit_stops['raceId'] == race_id]
        if not pit_stops_in_race.empty and 'durationSeconds' in pit_stops_in_race.columns:
            st.subheader("Análisis de Paradas en Boxes (Pit Stops)")

            pit_stop_summary = pit_stops_in_race.groupby('Piloto').agg(
                avg_duration=('durationSeconds', 'mean'),
                num_stops=('stop', 'max')
            ).reset_index().sort_values('avg_duration')

            fig = px.bar(
                pit_stop_summary,
                x='Piloto',
                y='avg_duration',
                title=f"Tiempo Medio de Parada en Boxes en {selected_gp_name} {selected_year}",
                labels={'Piloto': 'Piloto', 'avg_duration': 'Duración Media (s)'},
                hover_data={'num_stops': True},
                text_auto='.2f'
            )
            fig.update_layout(
                xaxis_title='Piloto',
                yaxis_title='Duración Media (s)',
                title={'text': f"Tiempo Medio de Parada en Boxes en {selected_gp_name} {selected_year}", 'x':0.5, 'xanchor': 'center'},
                margin=dict(l=40, r=40, t=60, b=40)
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(
                xaxis={'categoryorder':'total descending'},
                title_x=0.5,
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=12
                )
            )
            fig.update_traces(hovertemplate='<b>%{x}</b><br>Tiempo Medio: %{y:.2f}s<br>Paradas: %{customdata[0]}<extra></extra>')

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos detallados sobre paradas en boxes para esta carrera.")

    elif not selected_gp_name:
        st.info("Por favor, selecciona un Gran Premio.")
    else:
        st.info("No hay sesiones disponibles para este Gran Premio o año.")