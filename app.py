import streamlit as st
import pandas as pd
import json
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Geo-Analizador Híbrido", layout="wide")
st.title("📍 Visualizador de Rutas (Google + Manual)")

# --- INICIALIZACIÓN DE ESTADO (PERSISTENCIA) ---
# Esto permite que el CSV se quede guardado aunque el uploader se limpie
if 'puntos_manuales' not in st.session_state:
    st.session_state['puntos_manuales'] = []

# --- FUNCIONES CON CACHÉ ---
@st.cache_data
def procesar_datos_google(datos_json):
    segments = datos_json.get('semanticSegments', [])
    puntos = []
    for s in segments:
        path = s.get('timelinePath', [])
        for entry in path:
            point_str = entry.get('point', "")
            if point_str:
                try:
                    # Limpieza de caracteres y conversión
                    clean_str = point_str.replace('°', '').replace(' ', '')
                    lat, lon = map(float, clean_str.split(','))
                    puntos.append({'lat': lat, 'lon': lon, 'fuente': 'Google'})
                except:
                    continue
    return puntos

@st.cache_data
def procesar_csv(file_csv):
    try:
        df_manual = pd.read_csv(file_csv)
        # Normalizamos nombres de columnas a minúsculas para evitar errores (Lat vs lat)
        df_manual.columns = [c.lower().strip() for c in df_manual.columns]
        
        if 'lat' in df_manual.columns and 'lon' in df_manual.columns:
            df_manual['fuente'] = 'Manual'
            return df_manual[['lat', 'lon', 'fuente']].to_dict('records')
        else:
            return None
    except Exception as e:
        return f"Error: {e}"

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("1. Carga de Datos")
    
    # Google JSON (Carga temporal)
    archivo_json = st.file_uploader("Sube tu JSON de Google", type=['json'])
    
    st.divider()
    
    # CSV Manual (Carga persistente)
    nuevo_csv = st.file_uploader("Sube tu CSV de Rutas Manuales", type=['csv'])
    
    if nuevo_csv:
        resultado = procesar_csv(nuevo_csv)
        if isinstance(resultado, list):
            st.session_state['puntos_manuales'] = resultado
            st.success("✅ CSV cargado en memoria")
        else:
            st.error(resultado if resultado else "El CSV debe tener columnas 'lat' y 'lon'")

    if st.button("Limpiar datos del CSV"):
        st.session_state['puntos_manuales'] = []
        st.rerun()

    st.header("2. Personalización")
    radio_calor = st.slider("Radio del Heatmap", 5, 30, 12)
    opacidad = st.slider("Opacidad", 0.1, 1.0, 0.6)

# --- LÓGICA PRINCIPAL DE UNIFICACIÓN ---
puntos_totales = []

# 1. Añadir puntos de Google si existe el archivo
if archivo_json:
    try:
        data_j = json.load(archivo_json)
        puntos_totales.extend(procesar_datos_google(data_j))
    except Exception as e:
        st.error(f"Error al leer el JSON: {e}")

# 2. Añadir puntos del CSV desde el estado de sesión (persistencia)
if st.session_state['puntos_manuales']:
    puntos_totales.extend(st.session_state['puntos_manuales'])

# --- VISUALIZACIÓN ---
if puntos_totales:
    df = pd.DataFrame(puntos_totales)

    # Métricas informativas
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Puntos", len(df))
    c2.metric("Puntos Google", len(df[df['fuente'] == 'Google']))
    c3.metric("Puntos Manuales", len(df[df['fuente'] == 'Manual']))

    # Mapa
    # Usamos la media para centrar, pero Folium es robusto
    centro_lat = df['lat'].mean()
    centro_lon = df['lon'].mean()
    
    m = folium.Map(location=[centro_lat, centro_lon], zoom_start=12, control_scale=True)
    
    # Capa de Calor
    HeatMap(
        data=df[['lat', 'lon']].values.tolist(), 
        radius=radio_calor, 
        min_opacity=opacidad
    ).add_to(m)
    
    st_folium(m, width="100%", height=600)

else:
    st.info("👋 ¡Bienvenido! Sube un archivo JSON de Google o un CSV para empezar a visualizar.")
    st.markdown("""
    **Formato del CSV esperado:**
    - Debe contener al menos dos columnas: `lat` y `lon`.
    - Ejemplo:
    ```csv
    lat,lon
    19.4326,-99.1332
    19.4335,-99.1340
    ```
    """)
