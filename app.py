import streamlit as st
import pandas as pd
import json
import random
import folium
from streamlit_folium import st_folium
import io
from pandas import ExcelWriter

st.set_page_config(page_title="Detección de Riesgo Agrícola", layout="wide")
st.title("🌾 Detección de Riesgo Agrícola - MVP")

# Variables de sesión para mantener los datos
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["zona", "lat", "lon", "cultivo"])

if "cultivos_disponibles" not in st.session_state:
    try:
        with open("cultivos.json", "r", encoding="utf-8") as f:
            config_cultivos = json.load(f)
            st.session_state.config_cultivos = config_cultivos
            st.session_state.cultivos_disponibles = list(config_cultivos.keys())
    except:
        st.session_state.config_cultivos = {}
        st.session_state.cultivos_disponibles = []

# Tabs principales
tabs = st.tabs(["📁 Subir archivo", "🚨 Evaluación de Riesgo", "🗺️ Mapa de Zonas"])

# TAB 1 - Subir archivo y añadir manualmente
def tab_subir_archivo():
    with tabs[0]:
        st.header("📁 Subir archivo con zonas agrícolas")

        st.markdown("### 🔧 Cultivos a mostrar")
        seleccion = st.multiselect("Selecciona los cultivos que deseas evaluar", options=list(st.session_state.config_cultivos.keys()), default=["maíz", "arroz"])
        st.session_state.cultivos_disponibles = seleccion

        archivo = st.file_uploader("Selecciona un archivo CSV con columnas: zona, lat, lon, cultivo", type="csv")

        if archivo is not None:
            df_cargado = pd.read_csv(archivo)
            columnas_esperadas = {"zona", "lat", "lon", "cultivo"}
            if not columnas_esperadas.issubset(df_cargado.columns):
                st.error("❌ El archivo debe tener las columnas: zona, lat, lon, cultivo")
            else:
                df_filtrado = df_cargado[df_cargado["cultivo"].isin(st.session_state.cultivos_disponibles)]
                st.session_state.df = df_filtrado
                st.success("✅ Archivo cargado correctamente")
                st.dataframe(st.session_state.df, use_container_width=True)

        st.markdown("---")
        st.subheader("📍 Añadir ubicación manual")

        col1, col2 = st.columns(2)
        with col1:
            nombre_manual = st.text_input("Nombre de la zona")
            cultivo_manual = st.selectbox("Cultivo", list(st.session_state.config_cultivos.keys()))
        with col2:
            lat_manual = st.number_input("Latitud", format="%.6f")
            lon_manual = st.number_input("Longitud", format="%.6f")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Añadir ubicación manual"):
            nueva_fila = pd.DataFrame([{
                "zona": nombre_manual,
                "lat": lat_manual,
                "lon": lon_manual,
                "cultivo": cultivo_manual
            }])
            st.session_state.df = pd.concat([st.session_state.df, nueva_fila], ignore_index=True)
            st.success("✅ Ubicación añadida")
            st.dataframe(st.session_state.df, use_container_width=True)

        st.markdown("### 💾 Descargar zonas actuales")
        csv_actualizado = st.session_state.df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Descargar CSV actualizado",
            data=csv_actualizado,
            file_name="zonas_actualizadas.csv",
            mime="text/csv"
        )

# TAB 2 - Evaluación de riesgo por zona
def tab_evaluacion_riesgo():
    with tabs[1]:
        st.header("🚨 Evaluación de riesgo por zona")

        config_cultivos = st.session_state.config_cultivos

        if st.session_state.df.empty:
            st.warning("⚠️ Primero carga datos en el tab 'Subir archivo'")
            return

        resultados = []
        for _, fila in st.session_state.df.iterrows():
            zona = fila["zona"]
            cultivo = fila["cultivo"].strip().lower()
            lat = fila["lat"]
            lon = fila["lon"]

            if cultivo not in config_cultivos:
                continue

            reglas = config_cultivos[cultivo]
            random.seed(f"{zona}{cultivo}{lat}{lon}")  # Semilla fija para evitar blinbineo
            ndvi = round(random.uniform(0.2, 0.8), 2)
            lluvia = round(random.uniform(0, 50), 1)
            temperatura = round(random.uniform(20, 40), 1)

            riesgo = "Bajo"
            recomendacion = reglas["recomendacion_baja"]

            if ndvi < reglas["ndvi_min"] or lluvia < reglas["lluvia_min"] or temperatura > reglas["temperatura_max"]:
                riesgo = "Medio"
                recomendacion = reglas["recomendacion_media"]

            if (ndvi < reglas["ndvi_min"] * 0.8) or (lluvia < reglas["lluvia_min"] * 0.5) or (temperatura > reglas["temperatura_max"] + 2):
                riesgo = "Alto"
                recomendacion = reglas["recomendacion_alta"]

            motivos = []
            if ndvi < reglas["ndvi_min"]:
                motivos.append("NDVI bajo")
            if lluvia < reglas["lluvia_min"]:
                motivos.append("lluvia insuficiente")
            if temperatura > reglas["temperatura_max"]:
                motivos.append("temperatura excesiva")
            if not motivos:
                motivos = ["Todos los parámetros dentro de rango"]

            resultados.append({
                "zona": zona,
                "cultivo": cultivo,
                "lat": lat,
                "lon": lon,
                "NDVI": ndvi,
                "lluvia (mm)": lluvia,
                "temperatura (°C)": temperatura,
                "riesgo": riesgo,
                "recomendación": recomendacion,
                "motivo_riesgo": ", ".join(motivos)
            })

        st.session_state.resultados = pd.DataFrame(resultados)
        st.dataframe(st.session_state.resultados, use_container_width=True)

        # NUEVO: Botón para descargar resultados de riesgo
st.markdown("### 📥 Descargar resultados de riesgo")

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        st.session_state.resultados.to_excel(writer, index=False, sheet_name="Riesgo")

    st.download_button(
        label="📄 Descargar resultados como Excel",
        data=buffer.getvalue(),
        file_name="evaluacion_riesgo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# TAB 3 - Mapa con riesgos
def tab_mapa():
    with tabs[2]:
        st.header("🗺️ Mapa de zonas con nivel de riesgo")

        # Si no hay resultados, pero sí hay datos, se calcula el riesgo
        if ("resultados" not in st.session_state or st.session_state.resultados.empty) and not st.session_state.df.empty:
            config_cultivos = st.session_state.config_cultivos
            resultados = []
            for _, fila in st.session_state.df.iterrows():
                zona = fila["zona"]
                cultivo = fila["cultivo"].strip().lower()
                lat = fila["lat"]
                lon = fila["lon"]

                if cultivo not in config_cultivos:
                    continue

                reglas = config_cultivos[cultivo]
                random.seed(f"{zona}{cultivo}{lat}{lon}")
                ndvi = round(random.uniform(0.2, 0.8), 2)
                lluvia = round(random.uniform(0, 50), 1)
                temperatura = round(random.uniform(20, 40), 1)

                riesgo = "Bajo"
                recomendacion = reglas["recomendacion_baja"]

                if ndvi < reglas["ndvi_min"] or lluvia < reglas["lluvia_min"] or temperatura > reglas["temperatura_max"]:
                    riesgo = "Medio"
                    recomendacion = reglas["recomendacion_media"]

                if (ndvi < reglas["ndvi_min"] * 0.8) or (lluvia < reglas["lluvia_min"] * 0.5) or (temperatura > reglas["temperatura_max"] + 2):
                    riesgo = "Alto"
                    recomendacion = reglas["recomendacion_alta"]

                motivos = []
                if ndvi < reglas["ndvi_min"]:
                    motivos.append("NDVI bajo")
                if lluvia < reglas["lluvia_min"]:
                    motivos.append("lluvia insuficiente")
                if temperatura > reglas["temperatura_max"]:
                    motivos.append("temperatura excesiva")
                if not motivos:
                    motivos = ["Todos los parámetros dentro de rango"]

                resultados.append({
                    "zona": zona,
                    "cultivo": cultivo,
                    "lat": lat,
                    "lon": lon,
                    "NDVI": ndvi,
                    "lluvia (mm)": lluvia,
                    "temperatura (°C)": temperatura,
                    "riesgo": riesgo,
                    "recomendación": recomendacion,
                    "motivo_riesgo": ", ".join(motivos)
                })

            st.session_state.resultados = pd.DataFrame(resultados)

        if "resultados" not in st.session_state or st.session_state.resultados.empty:
            st.warning("⚠️ Aún no se han evaluado zonas. Ve al tab 'Subir archivo'.")
            return

        # Mostrar el mapa
        m = folium.Map(location=[-1.8, -79.0], zoom_start=7)

        def color_por_riesgo(nivel):
            if nivel == "Alto":
                return "red"
            elif nivel == "Medio":
                return "orange"
            else:
                return "green"

        for _, fila in st.session_state.resultados.iterrows():
            popup = (f"{fila['zona']} ({fila['riesgo']})"
                     f"<br><b>Recomendación:</b> {fila['recomendación']}"
                     f"<br><b>Motivo:</b> {fila['motivo_riesgo']}")

            folium.CircleMarker(
                location=[fila["lat"], fila["lon"]],
                radius=8,
                color=color_por_riesgo(fila["riesgo"]),
                fill=True,
                fill_opacity=0.7,
                popup=popup
            ).add_to(m)

        st_folium(m, width=900, height=700)

# Ejecutar tabs
tab_subir_archivo()
tab_evaluacion_riesgo()
tab_mapa()
