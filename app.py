import streamlit as st
import pandas as pd
import json
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium

# 1. Configuración básica
st.set_page_config(page_title="Geo-Analizador Híbrido", layout="wide")

# Inicializar sesión para el CSV
if 'puntos_manuales' not in st.session_state:
    st.session_state['puntos_manuales'] = []

# 2. Funciones de limpieza
def procesar_datos_google(datos_json):
    puntos = []
    try:
        segments = datos_json.get('semanticSegments', [])
        for s in segments:
            path = s.get('timelinePath', [])
            for entry in path:
                point_str = entry.get('point', "")
                if point_str and isinstance(point_str, str):
                    try:
                        # Limpiar coordenadas
                        clean_str = point_str.replace('°', '').replace(' ', '')
                        lat, lon = map(float, clean_str.split(','))
                        puntos.append({'lat': lat, 'lon': lon, 'fuente': 'Google'})
                    except:
                        continue
    except Exception as e:
        st.warning(f"Aviso en JSON: {e}")
    return puntos

def procesar_csv(file_csv):
    try:
        df = pd.read_csv(file_csv)
        # Limpiar nombres de columnas
        df.columns = [c.lower().strip() for c in df.columns]
        if 'lat' in df.columns and 'lon' in df.columns:
            # Eliminar filas con coordenadas vacías
            df = df.dropna(subset=['lat', 'lon'])
            df['fuente'] = 'Manual'
            return df[['lat', 'lon', 'fuente']].to_dict('records')
    except Exception as e:
        st.error(f"Error procesando CSV: {e}")
    return None

# 3. Interfaz de usuario
st.title("📍 Visualizador de Rutas")

with st.sidebar:
    st.header("1. Carga de Archivos")
    arc_json = st.file_uploader("Sube tu JSON de Google", type=['json'])
    arc_csv = st.file_uploader("Sube tu CSV Manual", type=['csv'])
    
    if arc_csv:
        res = procesar_csv(arc_csv)
        if res:
            st.session_state['puntos_manuales'] = res
            st.success("✅ CSV cargado")

    if st.button("Limpiar Memoria CSV"):
        st.session_state['puntos_manuales'] = []
        st.rerun()

    st.header("2. Ajustes")
    radio_calor = st.slider("Radio", 5, 30, 15)

# 4. Lógica de unión de datos
puntos_finales = []

if arc_json:
    try:
        datos_dict = json.load(arc_json)
        puntos_finales.extend(procesar_datos_google(datos_dict))
    except:
        st.error("El archivo JSON no tiene un formato válido.")

if st.session_state['puntos_manuales']:
    puntos_finales.extend(st.session_state['puntos_manuales'])

# 5. Renderizado del Mapa
if puntos_finales:
    df_final = pd.DataFrame(puntos_finales)
    
    # Métricas rápidas
    col1, col2 = st.columns(2)
    col1.metric("Total Puntos", len(df_final))
    col2.metric("Manuales en Memoria", len(st.session_state['puntos_manuales']))

    try:
        # Calcular centro (con fallback por si acaso)
        lat_center = df_final['lat'].median()
        lon_center = df_final['lon'].median()
        
        m = folium.Map(location=[lat_center, lon_center], zoom_start=12)
        
        # Añadir Heatmap
        HeatMap(df_final[['lat', 'lon']].values.tolist(), radius=radio_calor).add_to(m)
        
        # Mostrar mapa (usamos parámetros más compatibles para la nube)
        st_folium(m, width=1100, height=600, returned_objects=[])
        
    except Exception as e:
        st.error(f"Error al generar el mapa: {e}")
        st.write("Datos procesados:", df_final.head())
else:
    st.info("Sube un archivo para empezar a visualizar.")
