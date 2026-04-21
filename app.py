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
 
 
# --- FUNCIONES CON CACHÉ ---
 
@st.cache_data  # ✅ Ahora el JSON solo se procesa una vez aunque se muevan los sliders
def procesar_datos_google(datos_json):
    segments = datos_json.get('semanticSegments', [])
    puntos = []
    for s in segments:
        path = s.get('timelinePath', [])
        for entry in path:
            point_str = entry.get('point', "")
            if point_str:
                try:
                    clean_str = point_str.replace('°', '').replace(' ', '')
                    lat, lon = map(float, clean_str.split(','))
                    puntos.append({'lat': lat, 'lon': lon, 'fuente': 'Google'})
                except:
                    continue
    return puntos
 
 
@st.cache_data  # ✅ El CSV tampoco se re-lee con cada interacción
def procesar_csv(contenido_csv):
    df_manual = pd.read_csv(contenido_csv)
    if 'lat' in df_manual.columns and 'lon' in df_manual.columns:
        df_manual['fuente'] = 'Manual'
        return df_manual[['lat', 'lon', 'fuente']].to_dict('records')
    else:
        return None  # Señal de que faltan columnas
 
 
# --- LÓGICA PRINCIPAL ---
puntos_totales = []
 
# Cargar desde Google JSON
if archivo_json:
    data_j = json.load(archivo_json)
    puntos_totales.extend(procesar_datos_google(data_j))
 
# Cargar desde CSV manual
if archivo_csv:
    try:
        resultado = procesar_csv(archivo_csv)
        if resultado is None:
            st.error("El CSV debe tener columnas llamadas 'lat' y 'lon'")
        else:
            puntos_totales.extend(resultado)
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
 
    # Mapa — este sí se recalcula con cada slider porque depende de radio_calor y opacidad
    m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=12)
    HeatMap(df[['lat', 'lon']].values.tolist(), radius=radio_calor, min_opacity=opacidad).add_to(m)
    st_folium(m, width=1200, height=600)
 
else:
    st.info("Sube al menos un archivo para empezar.")
 
