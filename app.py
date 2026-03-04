import streamlit as st
import yt_dlp
import os
import tempfile

st.set_page_config(page_title="Streamlit Downloader", page_icon="🚀")

st.title("🚀 YouTube Downloader con Progreso")

url = st.text_input("Enlace de YouTube:", placeholder="https://...")
opcion = st.radio("Formato:", ("Video", "Audio"), horizontal=True)

# Barra de progreso inicializada
progress_bar = st.progress(0)
status_text = st.empty()

def progress_hook(d):
    if d['status'] == 'downloading':
        # Extraer el porcentaje del string (ej: ' 45.2%')
        p = d.get('_percent_str', '0%').replace('%','')
        try:
            val = float(p) / 100
            progress_bar.progress(val)
            status_text.text(f"Descargando: {p}% | Velocidad: {d.get('_speed_str')}")
        except:
            pass
    elif d['status'] == 'finished':
        progress_bar.progress(1.0)
        status_text.text("¡Descarga completa! Procesando...")

if url:
    try:
        with tempfile.TemporaryDirectory() as tmpdirname:
            ydl_opts = {
                'outtmpl': os.path.join(tmpdirname, '%(title)s.%(ext)s'),
                'progress_hooks': [progress_hook],
                'quiet': True,
            }

            if opcion == "Audio":
                ydl_opts['format'] = 'bestaudio/best'
            else:
                ydl_opts['format'] = 'best'

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            with open(filename, "rb") as f:
                st.download_button(
                    label="📥 Descargar Archivo Final",
                    data=f,
                    file_name=os.path.basename(filename),
                    mime="audio/mp4" if opcion == "Audio" else "video/mp4"
                )
                st.success("¡Listo! Haz clic arriba para guardar en tu dispositivo.")

    except Exception as e:
        st.error(f"Error: {e}")