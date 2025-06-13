# 🏎️ F1 Stats Dashboard 🏎️

An interactive web application built with Python and Streamlit for visualizing historical Formula 1 data. This dashboard provides a comprehensive tool for F1 enthusiasts to explore statistics on drivers, constructors, races, and seasons through dynamic charts and maps.

---

## ✨ Live Demo

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://f1statsdashboard.streamlit.app)

---

## 🚀 Features

This dashboard is organized into multiple analytical sections:

*   **👤 In-depth Driver Analysis:** View detailed stats, career trajectory, and a world map of victories for any driver in history.
*   **🏢 Team/Constructor Insights:** Analyze constructor performance over the years, including championships, wins, and podiums.
*   **📊 Head-to-Head Season Comparison:** Compare the performance of multiple drivers across a selected range of seasons with interactive line and bar charts.
*   **🏁 Historical Race Results:** Look up detailed results from any session (Race, Qualifying, Sprint, etc.) for any Grand Prix in history.
*   **🏆 Grand Prix Deep Dive:** Explore statistics for specific Grand Prix events, including the most successful drivers/teams and the circuits used.
*   **🌍 Geographic Stats:** Visualize the global distribution of F1 success with choropleth maps showing championships, wins, and poles by country for both drivers and constructors.

---

## 🛠️ Tech Stack

This project is built with a powerful stack of data science and web development libraries:

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)
![Folium](https://img.shields.io/badge/Folium-2E743A?style=for-the-badge&logo=leaflet&logoColor=white)
![GeoPandas](https://img.shields.io/badge/GeoPandas-1393d3?style=for-the-badge)

---


## ⚙️ Setup and Installation

To run this project locally, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/tu-usuario/tu-repositorio.git
    cd tu-repositorio
    ```

2.  **Create and activate a virtual environment:**
    *   **On macOS/Linux:**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
    *   **On Windows:**
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Data:**
    Ensure the CSV data files are located in the `database/` directory. The data used in this project can be sourced from Kaggle or similar platforms providing F1 historical data.

5.  **Run the Streamlit app:**
    ```bash
    streamlit run main.py
    ```
    The application will open in your default web browser.

---

## 📂 Project Structure

```
F1-Dashboard/
├── database/
│   ├── f1db-drivers.csv
│   └── ... (all other .csv files)
├── pages/
│   ├── analisis_temporada.py
│   ├── estadisticas_geograficas.py
│   ├── functions.py
│   ├── informacion_escuderias.py
│   ├── informacion_gp.py
│   ├── informacion_pilotos.py
│   └── resultados_historicos.py
├── .gitignore
├── main.py
├── requirements.txt
└── README.md
```

---

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

---

## 🙏 Acknowledgements

*   **Data Source:** The historical data used in this project is sourced from the **f1db** GitHub repository. This incredible open-source project provides structured and up-to-date F1 data in CSV format. You can find the repository here: [**f1db/f1db**](https://github.com/f1db/f1db). A massive thank you to the maintainers for their invaluable work.
*   **Inspiration:** A big thank you to the Formula 1 community for their passion and the data analysts who make amazing projects like this possible.
