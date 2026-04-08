import streamlit as st
import pandas as pd
import json
import re
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium

# Configuración de página
st.set_page_config(page_title="Geo-Analizador Híbrido", layout="wide")

st.title("📍 Visualizador de Rutas (Google + Manual)")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("1. Carga de Datos")
    archivo_json = st.file_uploader("Sube tu JSON de Google", type=['json'])
    archivo_csv = st.file_uploader("Sube tu CSV de Rutas Manuales", type=['csv'])
    
    st.header("2. Personalización")
    radio_calor = st.slider("Radio del Heatmap", 5, 30, 12)
    opacidad = st.slider("Opacidad", 0.1, 1.0, 0.6)

# --- FUNCIONES ---
def procesar_datos_google(datos_json):
    segments = datos_json.get('semanticSegments', [])
    puntos = []
    for s in segments:
        path = s.get('timelinePath', [])
        for entry in path:
            point_str = entry.get('point', "")
            if point_str:
                try:
                    # Limpieza rápida de la cadena
                    clean_str = point_str.replace('°', '').replace(' ', '')
                    lat, lon = map(float, clean_str.split(','))
                    puntos.append({'lat': lat, 'lon': lon, 'fuente': 'Google'})
                except: continue
    return puntos

# --- LÓGICA PRINCIPAL ---
puntos_totales = []

# Cargar desde Google JSON
if archivo_json:
    data_j = json.load(archivo_json)
    puntos_totales.extend(procesar_datos_google(data_j))

# Cargar desde tu CSV manual
if archivo_csv:
    try:
        df_manual = pd.read_csv(archivo_csv)
        # Asegurarnos de que tenga las columnas correctas
        if 'lat' in df_manual.columns and 'lon' in df_manual.columns:
            df_manual['fuente'] = 'Manual'
            puntos_totales.extend(df_manual[['lat', 'lon', 'fuente']].to_dict('records'))
        else:
            st.error("El CSV debe tener columnas llamadas 'lat' y 'lon'")
    except Exception as e:
        st.error(f"Error con el CSV: {e}")

# Visualización
if puntos_totales:
    df = pd.DataFrame(puntos_totales)
    
    # Métricas
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Puntos", len(df))
    c2.metric("Puntos Google", len(df[df['fuente'] == 'Google']))
    c3.metric("Puntos Manuales", len(df[df['fuente'] == 'Manual']))

    # Mapa
    m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=12)
    HeatMap(df[['lat', 'lon']].values.tolist(), radius=radio_calor, min_opacity=opacidad).add_to(m)
    st_folium(m, width=1200, height=600)
else:
    st.info("Sube al menos un archivo para empezar.")
