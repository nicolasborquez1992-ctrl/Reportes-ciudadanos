import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
from datetime import datetime
from PIL import Image

# ----------------------------------------------------
# Configuración Inicial de la Aplicación
# ----------------------------------------------------
st.set_page_config(
    page_title="Vallenar Resuelve - Reportes Urbanos",
    page_icon="🏙️",
    layout="wide"
)
# Estilo personalizado para insignias y fuentes
st.markdown("""
    <style>
    .main-header {
        background-color: #F3F4F6;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 6px solid #1E3A8A;
        margin-bottom: 1.5rem;
    }
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E3A8A;
        margin: 0;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4B5563;
        margin-top: 5px;
    }
    .badge-vallenar {
        background-color: #1E3A8A;
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# Encabezado Principal con Logo Institucional
# ----------------------------------------------------
col_logo, col_texto = st.columns([1, 5])

with col_logo:
    st.image(
        "https://raw.githubusercontent.com/nicolasborquez1992-ctrl/Reportes-ciudadanos/main/escudo.png"

with col_texto:
    st.markdown("""
        <div>
            <span class="badge-vallenar">ILUSTRE MUNICIPALIDAD DE VALLENAR</span>
            <h1 class="main-title">🏙️ Vallenar Resuelve</h1>
            <p class="sub-title"><b>Plataforma Digital de Gestión Territorial y Ciencia Ciudadana</b> — Registra, georreferencia y monitorea el estado de las incidencias en la comuna (Región de Atacama).</p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Coordenadas Base de Vallenar
LAT_VALLENAR = -28.5750
LON_VALLENAR = -70.7580

# ----------------------------------------------------
# Base de Datos Simulada en Sesión
# ----------------------------------------------------
if "incidencias" not in st.session_state:
    st.session_state.incidencias = pd.DataFrame([
        {
            "id": 1,
            "fecha": "2026-09-01",
            "sector": "Torreblanca",
            "categoria": "Bache / Evento en Calzada",
            "lat": -28.5710,
            "lon": -70.7620,
            "estado": "Pendiente",
            "comentario": "Evento de gran profundidad en avenida principal. Riesgo para vehículos pequeños.",
            "prioridad": "Alta",
            "imagen": None
        },
        {
            "id": 2,
            "fecha": "2026-09-02",
            "sector": "Centro",
            "categoria": "Luminaria Defectuosa",
            "lat": -28.5760,
            "lon": -70.7560,
            "estado": "En Proceso",
            "comentario": "Luminaria parpadea continuamente durante la noche frente a zona comercial.",
            "prioridad": "Media",
            "imagen": None
        },
        {
            "id": 3,
            "fecha": "2026-09-03",
            "sector": "Baquedano",
            "categoria": "Microbasural / Escombros",
            "lat": -28.5800,
            "lon": -70.7500,
            "estado": "Resuelto",
            "comentario": "Acumulación de escombros y voluminosos despejada por cuadrilla municipal.",
            "prioridad": "Baja",
            "imagen": None
        }
    ])

# ----------------------------------------------------
# Formulario Lateral: Nuevo Reporte Ciudadano
# ----------------------------------------------------
st.sidebar.header("📝 Nuevo Reporte Ciudadano")
st.sidebar.caption("Ingresa los datos del problema detectado en la vía pública.")

sectores_vallenar = ["Centro", "Torreblanca", "Baquedano", "Quinta Maza", "Ventanas", "O'Higgins", "Hermanos Carrera", "Otro Sector"]
sector_input = st.sidebar.selectbox("Sector de Vallenar:", sectores_vallenar)

cat_input = st.sidebar.selectbox(
    "Categoría de la Incidencia:", 
    [
        "Bache / Evento en Calzada", 
        "Luminaria Defectuosa", 
        "Microbasural / Escombros", 
        "Fuga de Agua / Alcantarillado", 
        "Semáforo Defectuoso",
        "Señaletica Dañada",
        "Arbolado / Peligro de Caída"
    ]
)

prioridad_input = st.sidebar.select_slider(
    "Nivel de Urgencia Estimado:",
    options=["Baja", "Media", "Alta", "Crítica"]
)

# Ubicación y Coordenadas
st.sidebar.subheader("📍 Ubicación Exacta")
lat_input = st.sidebar.number_input("Latitud GPS:", value=LAT_VALLENAR, format="%.5f")
lon_input = st.sidebar.number_input("Longitud GPS:", value=LON_VALLENAR, format="%.5f")

# Comentario y Foto
st.sidebar.subheader("📷 Evidencia y Detalles")
comentario_input = st.sidebar.text_area("Comentario / Descripción detallada:", placeholder="Ej: Esquina frente al almacén, la fuga comenzó hoy en la mañana...")
foto_input = st.sidebar.file_uploader("Adjuntar Fotografía de Evidencia:", type=["jpg", "png", "jpeg"])

if st.sidebar.button("🚀 Registrar Incidencia", use_container_width=True):
    if comentario_input.strip() == "":
        st.sidebar.warning("Por favor agrega un breve comentario detallando la situación.")
    else:
        # Procesar imagen si fue subida
        imagen_guardada = None
        if foto_input is not None:
            imagen_guardada = Image.open(foto_input)

        nuevo_id = len(st.session_state.incidencias) + 1
        nueva_fila = pd.DataFrame([{
            "id": nuevo_id,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "sector": sector_input,
            "categoria": cat_input,
            "lat": lat_input,
            "lon": lon_input,
            "estado": "Pendiente",
            "comentario": comentario_input,
            "prioridad": prioridad_input,
            "imagen": imagen_guardada
        }])
        
        st.session_state.incidencias = pd.concat([st.session_state.incidencias, nueva_fila], ignore_index=True)
        st.sidebar.success(f"¡Reporte #{nuevo_id} ingresado exitosamente!")

# ----------------------------------------------------
# Panel Principal: Métricas Generales
# ----------------------------------------------------
df = st.session_state.incidencias

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Incidentes Registrados", len(df))
m2.metric("Pendientes de Atención", len(df[df["estado"] == "Pendiente"]))
m3.metric("En Intervención / Proceso", len(df[df["estado"] == "En Proceso"]))
m4.metric("Incidentes Resueltos", len(df[df["estado"] == "Resuelto"]))

st.markdown("---")

# ----------------------------------------------------
# Módulo de Mapa Interactivo y Gráficos
# ----------------------------------------------------
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("🗺️ Mapa Georreferenciado de Vallenar")
    
    # Crear Mapa base
    m = folium.Map(location=[LAT_VALLENAR, LON_VALLENAR], zoom_start=14)
    
    colores_categoria = {
        "Bache / Evento en Calzada": "red",
        "Luminaria Defectuosa": "orange",
        "Microbasural / Escombros": "blue",
        "Fuga de Agua / Alcantarillado": "cadetblue",
        "Semáforo Defectuoso": "purple",
        "Señaletica Dañada": "darkgreen",
        "Arbolado / Peligro de Caída": "green"
    }
    
    for _, row in df.iterrows():
        popup_html = f"""
        <div style="font-family: Arial; width: 200px;">
            <h4>Reporte #{row['id']}</h4>
            <b>Sector:</b> {row['sector']}<br>
            <b>Tipo:</b> {row['categoria']}<br>
            <b>Prioridad:</b> {row['prioridad']}<br>
            <b>Estado:</b> {row['estado']}<br>
            <hr>
            <b>Comentario:</b><br>{row['comentario']}
        </div>
        """
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"#{row['id']} - {row['categoria']} ({row['sector']})",
            icon=folium.Icon(color=colores_categoria.get(row["categoria"], "gray"), icon="exclamation-sign")
        ).add_to(m)
        
    st_folium(m, width=800, height=480)

with col_right:
    st.subheader("📊 Métricas de Gestión")
    
    # Gráfico 1: Distribución por Sector
    fig_sector = px.pie(df, names="sector", title="Incidencias por Sector", hole=0.35)
    st.plotly_chart(fig_sector, use_container_width=True)
    
    # Gráfico 2: Distribución por Categoría
    fig_cat = px.bar(df, x="categoria", title="Tipos de Incidencias", color="categoria")
    fig_cat.update_layout(showlegend=False)
    st.plotly_chart(fig_cat, use_container_width=True)

# ----------------------------------------------------
# Registro Detallado y Visor de Evidencias Fotográficas
# ----------------------------------------------------
st.markdown("---")
st.subheader("📋 Galería de Reportes y Evidencia Fotográfica")

if len(df) > 0:
    for _, row in df.iloc[::-1].iterrows(): # Mostrar más recientes primero
        with st.expander(f"📍 Reporte #{row['id']} - {row['categoria']} en Sector {row['sector']} ({row['estado']})"):
            c_info, c_img = st.columns([2, 1])
            
            with c_info:
                st.write(f"*Fecha de Registro:* {row['fecha']}")
                st.write(f"*Ubicación GPS:* Lat {row['lat']} | Lon {row['lon']}")
                st.write(f"*Nivel de Urgencia:* {row['prioridad']}")
                st.write(f"*Estado Actual:* {row['estado']}")
                st.write(f"*Comentario Ciudadano:*")
                st.info(row["comentario"])
                
            with c_img:
                if row["imagen"] is not None:
                    st.image(row["imagen"], caption=f"Evidencia Reporte #{row['id']}", use_column_width=True)
                else:
                    st.caption("📷 Sin fotografía adjunta para este reporte.")

# ----------------------------------------------------
# Pie de Página (Footer) Institucional
# ----------------------------------------------------
st.markdown("---")

footer_col1, footer_col2, footer_col3 = st.columns([1, 2, 1])

with footer_col2:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Escudo_de_Vallenar.svg/1200px-Escudo_de_Vallenar.svg.png", 
        width=90
    )
    st.markdown(
        """
        <div style="text-align: center; color: #374151; font-family: sans-serif;">
            <h3 style="margin-bottom: 2px; color: #1E3A8A;">Ilustre Municipalidad de Vallenar</h3>
            <p style="font-size: 0.95rem; margin-bottom: 4px;"><b>Plataforma Digital de Gestión Territorial y Participación Ciudadana</b></p>
            <p style="font-size: 0.85rem; color: #6B7280;">Provincia de Huasco — Región de Atacama, Chile</p>
            <hr style="margin: 10px 0;">
            <p style="font-size: 0.8rem; color: #9CA3AF;">© 2026 Vallenar Resuelve. Sistema optimizado para monitoreo y solución de incidentes en la vía pública.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
