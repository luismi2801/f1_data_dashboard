import requests
import pandas as pd
import streamlit as st
import time
from bs4 import BeautifulSoup
import urllib.parse
import pycountry
from difflib import get_close_matches
import geopandas as gpd
import io


@st.cache_data
def fuzzy_match_countries(grand_prix_id, world_countries):
    """Mapea grandPrixId a nombres de países usando pycountry"""
    # Diccionario para casos especiales
    special_cases = {
        'united-states': 'United States',
        'europe': 'Germany',  # GP de Europa se celebraba en Alemania
        'miami': 'United States',  # Miami está en Estados Unidos
        'san-marino': 'San Marino',
        'las-vegas': 'United States',  # Las Vegas está en Estados Unidos
        'great-britain': 'United Kingdom',  # Gran Bretaña se refiere al Reino Unido
        'abu-dhabi': 'United Arab Emirates',  # Abu Dhabi es un emirato de los EAU
        'tuscany': 'Italy',  # GP de la Toscana se celebraba en Italia
        'eifel': 'Germany',  # GP de Eifel se celebraba en Alemania
        'emilia-romagna': 'Italy',  # GP de Emilia-Romaña se celebraba en Italia
        'sao-paulo': 'Brazil',  # GP de Sao Paulo se celebraba en Brasil
        'portimao': 'Portugal',  # GP de Portimao se celebraba en Portugal
    }
    
    if grand_prix_id in special_cases:
        country_name = special_cases[grand_prix_id]
    else:
        # Convertir grandPrixId a formato de país
        country_name = grand_prix_id.replace('-', ' ').title()
    
    # Buscar en pycountry
    try:
        country = pycountry.countries.lookup(country_name)
        return country.name
    except LookupError:
        # Si no se encuentra, intentar búsqueda difusa
        all_countries = [c.name for c in pycountry.countries]
        matches = get_close_matches(country_name, all_countries, n=1, cutoff=0.6)
        return matches[0] if matches else None

@st.cache_data
def load_world_geometry():
    """Carga la geometría mundial una sola vez y la cachea"""
    try:
        world = gpd.read_file("data/ne_110m_admin_0_countries.zip")
        return world
    except Exception as e:
        st.error(f"Error cargando geometría mundial: {e}")
        return None

@st.cache_data
def load_driver_photo(driver):
    search_url = f"https://en.wikipedia.org/w/index.php?search={urllib.parse.quote(driver)}"
    search_response = requests.get(search_url, timeout=5)
    if search_response.status_code == 200:
        search_soup = BeautifulSoup(search_response.content, 'html.parser')
        # Buscar el primer resultado relevante
        first_link = search_soup.find('a', {'class': 'mw-search-result-heading'})
        if first_link and first_link.get('href'):
            wiki_url = "https://en.wikipedia.org" + first_link['href']
        else:
            # Si no hay resultados, intentar ir directamente a la página
            wiki_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(driver.replace(' ', '_'))}"
        response = requests.get(wiki_url, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            infobox = soup.find('table', {'class': 'infobox'})
            if infobox:
                img = infobox.find('img')
                if img and img.get('src'):
                    photo_url = img['src']
                    if photo_url.startswith('//'):
                        photo_url = 'https:' + photo_url
    
                    return photo_url
    return None

@st.cache_data
def load_gadm_data(country_code):
    """
    Descarga los datos de GADM desde la URL, los descomprime en memoria y los lee con Geopandas.
    """
    url = f"https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_{country_code}_shp.zip"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Lanza un error si la descarga falla (ej. 404)

        zipfile_in_memory = io.BytesIO(response.content)
        gdf = gpd.read_file(zipfile_in_memory)
        return gdf
    except requests.exceptions.HTTPError:
        st.warning(f"No se pudo descargar el mapa para {country_code}. El GP podría no tener mapa regional.")
        return None
    except Exception as e:
        st.error(f"Ocurrió un error al procesar el mapa para {country_code}: {e}")
        return None
