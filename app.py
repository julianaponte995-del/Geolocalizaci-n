import streamlit as st
import pandas as pd
import json
import re
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from pandas import json_normalize

# Configuración de página
st.set_page_config(page_title="Geo-Analizador de Rutas", layout="wide")

st.title("📍 Visualizador de Historial de Ubicación")
st.markdown("Sube tu archivo `Rutas.json` de Google Takeout para visualizar tu mapa de calor.")

# --- BARRA LATERAL (CARGA DE DATOS) ---
with st.sidebar:
    st.header("Configuración")
    archivo_subido = st.file_uploader("Sube tu JSON de Google", type=['json'])
    radio_calor = st.slider("Radio del Heatmap", 5, 30, 12)
    opacidad = st.slider("Opacidad", 0.1, 1.0, 0.6)

# --- FUNCIONES DE LIMPIEZA ---
def limpiar_coordenadas(texto):
    if not isinstance(texto, str): return None, None
    numeros = re.findall(r"[-+]?\d*\.\d+|\d+", texto)
    if len(numeros) >= 2:
        return float(numeros[0]), float(numeros[1])
    return None, None

def procesar_datos(datos_json):
    segments = datos_json.get('semanticSegments', [])
    
    # Extraer puntos de trayectoria (Timeline Path)
    puntos_ruta = []
    for s in segments:
        path = s.get('timelinePath', [])
        for entry in path:
            point_str = entry.get('point', "")
            if point_str:
                clean_str = point_str.replace('°', '').replace(' ', '')
                try:
                    lat, lon = map(float, clean_str.split(','))
                    puntos_ruta.append([lat, lon])
                except: continue
    return puntos_ruta

# --- LÓGICA PRINCIPAL ---
if archivo_subido is not None:
    try:
        data = json.load(archivo_subido)
        puntos = procesar_datos(data)

        if puntos:
            df = pd.DataFrame(puntos, columns=['lat', 'lon'])
            
            # Métricas rápidas
            col1, col2 = st.columns(2)
            col1.metric("Puntos detectados", len(df))
            col2.metric("Área de cobertura", f"{df['lat'].nunique()} zonas")

            # Creación del Mapa
            st.subheader("🗺️ Mapa de Calor de Exploración")
            m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=12)
            
            HeatMap(puntos, 
                    radius=radio_calor, 
                    blur=8, 
                    min_opacity=opacidad,
                    gradient={0.2: 'blue', 0.4: 'cyan', 0.6: 'lime', 0.8: 'yellow', 1: 'red'}
            ).add_to(m)

            # Renderizar mapa en Streamlit
            st_folium(m, width=1200, height=600)
            
            # Opción de ver datos crudos
            if st.checkbox("Mostrar tabla de coordenadas"):
                st.dataframe(df.head(100))
        else:
            st.warning("No se encontraron puntos de trayectoria en este archivo.")

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info("Esperando archivo JSON...")
    # Imagen ilustrativa de cómo funciona el flujo
    #
