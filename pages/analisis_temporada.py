import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Análisis de Temporada",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Análisis Histórico por Temporada")
st.markdown("Compara el rendimiento de pilotos y escuderías a lo largo de la historia de la F1.")

@st.cache_data
def load_data():
    try:
        driver_standings = pd.read_csv("database/f1db-seasons-driver-standings.csv")
        drivers = pd.read_csv("database/f1db-drivers.csv")[['id', 'name']]
        race_results = pd.read_csv("database/f1db-races-race-results.csv", low_memory=False)
        
        # ### CORRECCIÓN 2: Añadir la información del Gran Premio que faltaba
        races = pd.read_csv("database/f1db-races.csv")[['raceId', 'grandPrixId']]
        grands_prix = pd.read_csv("database/f1db-grands-prix.csv")[['id', 'name']]
        
        race_results = race_results.merge(races, on='raceId', how='left')
        race_results = race_results.merge(grands_prix, left_on='grandPrixId', right_on='id', how='left')
        race_results.rename(columns={'name': 'grandPrixName'}, inplace=True)

        # name_corrections = {"Fernando Alonso Díaz": "Fernando Alonso"}
        drivers['fullName'] = drivers['name']
        race_results['full_name'] = race_results['full_name']

        driver_standings = driver_standings.merge(drivers, left_on='driverId', right_on='id', how='left')
        race_results.rename(columns={'full_name': 'fullName'}, inplace=True)
        
        return driver_standings, race_results, drivers
    except FileNotFoundError as e:
        st.error(f"Error cargando los datos: no se encontró el archivo {e.filename}. Asegúrate de que los archivos CSV están en la carpeta 'database'.")
        return None, None, None

driver_standings, race_results, drivers = load_data()

if driver_standings is not None:
    st.sidebar.header("Filtros de Análisis")
    all_years = sorted(driver_standings['year'].unique())
    selected_years = st.sidebar.slider(
        "Selecciona un rango de años:",
        min_value=int(min(all_years)),
        max_value=int(max(all_years)),
        value=(2010, int(max(all_years))) 
    )

    driver_standings_filtered = driver_standings[
        (driver_standings['year'] >= selected_years[0]) & (driver_standings['year'] <= selected_years[1])
    ]

    all_drivers_in_range = sorted(driver_standings_filtered['fullName'].dropna().unique())
    
    default_drivers_list = ["Michael Schumacher", "Lewis Hamilton", "Max Verstappen", "Fernando Alonso", "Sebastian Vettel"]
    valid_defaults = [driver for driver in default_drivers_list if driver in all_drivers_in_range]
    
    selected_drivers = st.sidebar.multiselect(
        "Selecciona pilotos para comparar:",
        options=all_drivers_in_range,
        default=valid_defaults
    )

    if not selected_drivers:
        st.warning("Por favor, selecciona al menos un piloto en la barra lateral para ver las gráficas.")
    else:
        plot_data = driver_standings_filtered[driver_standings_filtered['fullName'].isin(selected_drivers)]
        
        st.subheader("Evolución de Puntos en el Campeonato")
        fig1 = px.line(
            plot_data.sort_values(by='year'),
            x='year',
            y='points',
            color='fullName',
            title="Puntos por temporada",
            labels={'year': 'Año', 'points': 'Puntos', 'fullName': 'Piloto'},
            markers=True
        )
        st.plotly_chart(fig1, use_container_width=True)

        st.subheader("Total de Victorias en el Periodo Seleccionado")
        wins_data = race_results[
            (race_results['year'] >= selected_years[0]) & (race_results['year'] <= selected_years[1]) &
            (race_results['positionNumber'] == 1) &
            (race_results['fullName'].isin(selected_drivers)) 
        ]
        
        if not wins_data.empty:
            wins_count = wins_data.groupby('fullName').size().reset_index(name='victorias').sort_values(by='victorias', ascending=False) # Usamos fullName
            fig2 = px.bar(
                wins_count,
                x='fullName', 
                y='victorias',
                color='fullName', 
                title=f"Victorias Totales entre {selected_years[0]} y {selected_years[1]}",
                labels={'fullName': 'Piloto', 'victorias': 'Número de Victorias'}
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Ninguno de los pilotos seleccionados consiguió victorias en el periodo especificado.")

        st.subheader("Posición de Salida vs. Posición Final")
        col1, col2 = st.columns(2)
        with col1:
            single_driver_select = st.selectbox("Selecciona un piloto:", options=selected_drivers)
        
        available_years_for_driver = sorted(plot_data[plot_data['fullName'] == single_driver_select]['year'].unique(), reverse=True)
        
        with col2:
            if available_years_for_driver:
                single_year_select = st.selectbox("Selecciona un año:", options=available_years_for_driver)
            else:
                single_year_select = None

        if single_year_select:
            scatter_data = race_results[
                (race_results['year'] == single_year_select) &
                (race_results['fullName'] == single_driver_select) & 
                (race_results['gridPositionNumber'] > 0)
            ].dropna(subset=['gridPositionNumber', 'positionNumber'])
            
            if not scatter_data.empty:
                fig3 = px.scatter(
                    scatter_data,
                    x='gridPositionNumber',
                    y='positionNumber',
                    title=f"Salida vs. Llegada para {single_driver_select} en {single_year_select}",
                    labels={'gridPositionNumber': 'Posición de Salida', 'positionNumber': 'Posición Final'},
                    hover_data=['grandPrixName'] 
                )
                max_pos = max(scatter_data['gridPositionNumber'].max(), scatter_data['positionNumber'].max()) + 1
                fig3.add_shape(type='line', x0=0, y0=0, x1=max_pos, y1=max_pos, line=dict(color='Gray', dash='dash'))
                fig3.update_yaxes(autorange="reversed")
                st.plotly_chart(fig3, use_container_width=True)
                st.caption("La línea discontinua representa mantener la misma posición. Puntos por debajo significan mejora, puntos por encima significan pérdida de posiciones.")
            else:
                st.info(f"No hay datos de carrera para {single_driver_select} en el año {single_year_select}.")