import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
from datetime import datetime
from PIL import Image
from streamlit_js_eval import get_geolocation
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import io
import os

# Librerías para generación de PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# ----------------------------------------------------
# Configuración Inicial y Carpeta de Fotos
# ----------------------------------------------------
st.set_page_config(
    page_title="Vallenar Resuelve - Gestión Territorial y Atención Ciudadana",
    page_icon="🏙️",
    layout="wide"
)

# Crear la carpeta para guardar fotos reportadas si no existe
CARPETA_FOTOS = "fotos_reportes"
if not os.path.exists(CARPETA_FOTOS):
    os.makedirs(CARPETA_FOTOS)

# URL del logo de Vallenar
URL_LOGO_VALLENAR = "https://upload.wikimedia.org/wikipedia/commons/2/27/Escudo_de_Vallenar.svg"

# CSS Personalizado
st.markdown("""
    <style>
    .main-title { 
        font-size: 2.1rem; 
        font-weight: 800; 
        color: #1E3A8A; 
        margin: 0; 
        line-height: 1.2; 
    }
    .sub-title { 
        font-size: 1rem; 
        color: #4B5563; 
        margin-top: 4px; 
        font-weight: 500; 
    }
    .badge-vallenar { 
        background-color: #1E3A8A; 
        color: white; 
        padding: 4px 10px; 
        border-radius: 6px; 
        font-size: 0.8rem; 
        font-weight: 700; 
        display: inline-block; 
        margin-bottom: 6px;
        letter-spacing: 0.5px;
    }
    
    div[data-baseweb="select"] {
        border: 2px solid #1E3A8A !important;
        border-radius: 8px !important;
    }
    
    .footer-card {
        background: linear-gradient(135deg, #1E3A8A 0%, #1E40AF 50%, #0369A1 100%);
        color: white;
        padding: 30px 20px;
        border-radius: 16px;
        text-align: center;
        margin-top: 40px;
        box-shadow: 0 10px 25px -5px rgba(30, 58, 138, 0.3);
    }
    .footer-card h3 {
        color: #FACC15 !important;
        font-size: 1.4rem;
        font-weight: 800;
        margin-bottom: 8px;
    }
    .footer-card p {
        font-size: 0.95rem;
        color: #E0E7FF;
        margin-bottom: 16px;
    }
    .footer-badges {
        display: flex;
        justify-content: center;
        gap: 15px;
        flex-wrap: wrap;
        margin-top: 15px;
    }
    .footer-badge-item {
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(5px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

LAT_VALLENAR = -28.5750
LON_VALLENAR = -70.7580
CLAVE_ADMIN = "vallenar2026"
EXCEL_FILE = "reportes_vallenar.xlsx"

# ----------------------------------------------------
# Manejo de Persistencia en Excel
# ----------------------------------------------------
def cargar_datos_excel():
    if os.path.exists(EXCEL_FILE):
        try:
            df = pd.read_excel(EXCEL_FILE)
            if "obs_municipal" not in df.columns:
                df["obs_municipal"] = "En espera de revisión."
            if "foto_path" not in df.columns:
                df["foto_path"] = "Sin foto"
            return df
        except Exception:
            pass
    
    data_inicial = [
        {
            "id": 1,
            "fecha": "2026-09-01",
            "sector": "Torreblanca",
            "categoria": "Bache / Evento en Calzada",
            "lat": -28.5710,
            "lon": -70.7620,
            "estado": "Pendiente",
            "comentario": "Evento de gran profundidad cerca de la escuela.",
            "prioridad": "Alta",
            "contacto": "vecino.torreblanca@gmail.com",
            "obs_municipal": "Asignado a cuadrilla de obras.",
            "foto_path": "Sin foto"
        },
        {
            "id": 2,
            "fecha": "2026-09-02",
            "sector": "Centro",
            "categoria": "Luminaria Defectuosa",
            "lat": -28.5760,
            "lon": -70.7560,
            "estado": "En Proceso",
            "comentario": "Luminaria apagada en calle Prat.",
            "prioridad": "Media",
            "contacto": "comercio.centro@vallenar.cl",
            "obs_municipal": "Repuestos solicitados en bodega.",
            "foto_path": "Sin foto"
        }
    ]
    df = pd.DataFrame(data_inicial)
    try:
        df.to_excel(EXCEL_FILE, index=False)
    except Exception:
        pass
    return df

def guardar_datos_excel(df):
    try:
        df.to_excel(EXCEL_FILE, index=False)
    except Exception as e:
        st.error(f"Error al guardar datos en Excel: {e}")

if "incidencias" not in st.session_state:
    st.session_state.incidencias = cargar_datos_excel()

sectores_vallenar = ["Centro", "Torreblanca", "Hda ventanas", "Hda cavancha", "Las Pircas", "Hda buena esperanza", "Regidores", "Vista alegre", "Hda compañia", "Altos del valle", "San Ambrosio", "Baquedano", "Quinta Valle", "Ventanas", "O'Higgins", "Hermanos Carrera", "Otro Sector"]

# ----------------------------------------------------
# Módulo 1: Envío de Notificaciones por Correo
# ----------------------------------------------------
def enviar_correo_notificacion(destinatario, id_reporte, nuevo_estado, categoria, sector):
    if not destinatario or "@" not in destinatario or destinatario == "No especificado":
        return False, "No se registró un correo válido para este reporte."

    asunto = f"🔔 Actualización de Reporte #{id_reporte} - Ilustre Municipalidad de Vallenar"
    cuerpo = f"""
    Estimado/a vecino/a,

    Le informamos que su reporte ingresado en la plataforma 'Vallenar Resuelve' ha cambiado de estado:

      • Folio: #{id_reporte}
      • Tipo de Incidencia: {categoria}
      • Sector: {sector}
      • Nuevo Estado: {nuevo_estado.upper()}

    Agradecemos su valiosa colaboración para seguir construyendo una mejor comuna.

    Atentamente,
    Ilustre Municipalidad de Vallenar
    """

    msg = MIMEMultipart()
    msg['From'] = "contacto.vallenar.resuelve@gmail.com"
    msg['To'] = destinatario
    msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo, 'plain'))

    try:
        return True, "Simulación: correo preparado correctamente."
    except Exception as e:
        return False, str(e)

# ----------------------------------------------------
# Módulo 2: Generador de Informes PDF
# ----------------------------------------------------
def generar_pdf_gestion(df_data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()
    
    story.append(Paragraph("<b>ILUSTRE MUNICIPALIDAD DE VALLENAR</b>", styles['Heading1']))
    story.append(Paragraph("<b>INFORME DE GESTIÓN DE INCIDENCIAS URBANAS</b>", styles['Normal']))
    story.append(Paragraph(f"Fecha de emisión: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 15))

    table_data = [["Folio", "Fecha", "Sector", "Categoría", "Estado"]]
    for _, row in df_data.iterrows():
        table_data.append([f"#{row['id']}", str(row["fecha"]), str(row["sector"]), str(row["categoria"]), str(row["estado"])])

    t = Table(table_data, colWidths=[40, 70, 90, 190, 80])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
    ]))
    
    story.append(t)
    doc.build(story)
    buffer.seek(0)
    return buffer

# ----------------------------------------------------
# Encabezado Principal
# ----------------------------------------------------
col_logo, col_encabezado, col_menu = st.columns([0.4, 1.4, 1])

with col_logo:
    try:
        st.image(URL_LOGO_VALLENAR, width=90)
    except Exception:
        st.write("🏛️")

with col_encabezado:
    st.markdown("""
        <div>
            <span class="badge-vallenar">ILUSTRE MUNICIPALIDAD DE VALLENAR</span>
            <h1 class="main-title">🏙️ Vallenar Resuelve</h1>
            <p class="sub-title">Plataforma Digital de Gestión Territorial y Atención Ciudadana</p>
        </div>
    """, unsafe_allow_html=True)

with col_menu:
    opcion_menu = st.selectbox(
        "📌 Menú / Navegación:",
        ["📝 Crear Nuevo Reporte", "🗺️ Mapa y Reportes", "⚙️ Panel de Administración"],
        index=0
    )

st.markdown("---")

# ----------------------------------------------------
# VISTA 1: CREAR NUEVO REPORTE
# ----------------------------------------------------
if opcion_menu == "📝 Crear Nuevo Reporte":
    st.subheader("📝 Formulario de Reporte Ciudadano")
    
    sector_input = st.selectbox("Sector / Barrio:", sectores_vallenar)
    cat_input = st.selectbox(
        "Categoría del Problema:", 
        ["Bache / Evento en Calzada", "Luminaria Defectuosa", "Microbasural / Escombros", "Fuga de Agua / Alcantarillado", "Semáforo Defectuoso", "Señaletica Dañada", "Arbolado / Peligro de Caída"]
    )
    prioridad_input = st.select_slider("Urgencia Estimada:", options=["Baja", "Media", "Alta", "Crítica"])

    location = get_geolocation()
    if location and "coords" in location:
        lat_input = float(location["coords"]["latitude"])
        lon_input = float(location["coords"]["longitude"])
        st.success(f"📍 Coordenadas GPS Capturadas: {lat_input:.4f}, {lon_input:.4f}")
    else:
        lat_input, lon_input = LAT_VALLENAR, LON_VALLENAR
        st.info("📍 Usando ubicación central de Vallenar")

    comentario_input = st.text_area("Descripción detallada de la incidencia:")
    contacto_input = st.text_input("Correo electrónico del vecino:", placeholder="ejemplo@correo.cl")
    foto_input = st.file_uploader("Adjuntar Foto / Evidencia (JPG, PNG):", type=["jpg", "png", "jpeg"])

    if st.button("🚀 Enviar Reporte a la Municipalidad", use_container_width=True):
        if comentario_input.strip() == "":
            st.warning("Por favor agrega una breve descripción del problema.")
        else:
            # Generar un ID único autoincremental
            df_actual = st.session_state.incidencias
            nuevo_id = int(df_actual["id"].max() + 1) if len(df_actual) > 0 else 1
            
            # Guardar la foto físicamente si el usuario la subió
            foto_path_guardada = "Sin foto"
            if foto_input is not None:
                ext = foto_input.name.split(".")[-1]
                nombre_archivo = f"reporte_{nuevo_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
                foto_path_guardada = os.path.join(CARPETA_FOTOS, nombre_archivo)
                
                # Guardar imagen en disco
                img = Image.open(foto_input)
                img.save(foto_path_guardada)

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
                "contacto": contacto_input.strip() if contacto_input.strip() != "" else "No especificado",
                "obs_municipal": "En espera de revisión.",
                "foto_path": foto_path_guardada
            }])
            
            st.session_state.incidencias = pd.concat([st.session_state.incidencias, nueva_fila], ignore_index=True)
            guardar_datos_excel(st.session_state.incidencias)
            st.success(f"✅ ¡Reporte #{nuevo_id} ingresado y guardado exitosamente!")

# ----------------------------------------------------
# VISTA 2: MAPA Y REPORTES
# ----------------------------------------------------
elif opcion_menu == "🗺️ Mapa y Reportes":
    df = st.session_state.incidencias

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Incidentes", len(df))
    m2.metric("Pendientes", len(df[df["estado"] == "Pendiente"]))
    m3.metric("En Proceso", len(df[df["estado"] == "En Proceso"]))
    m4.metric("Resueltos", len(df[df["estado"] == "Resuelto"]))

    st.markdown("---")
    st.subheader("🔍 Filtros de Búsqueda")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filtro_sector = st.multiselect("Sector:", options=sectores_vallenar, default=[], placeholder="Seleccionar opciones...")
    with col_f2:
        filtro_estado = st.multiselect("Estado:", options=["Pendiente", "En Proceso", "Resuelto"], default=[], placeholder="Seleccionar opciones...")
    with col_f3:
        filtro_urgencia = st.multiselect("Urgencia:", options=["Baja", "Media", "Alta", "Crítica"], default=[], placeholder="Seleccionar opciones...")

    df_filtrado = df.copy()
    if filtro_sector: 
        df_filtrado = df_filtrado[df_filtrado["sector"].isin(filtro_sector)]
    if filtro_estado: 
        df_filtrado = df_filtrado[df_filtrado["estado"].isin(filtro_estado)]
    if filtro_urgencia: 
        df_filtrado = df_filtrado[df_filtrado["prioridad"].isin(filtro_urgencia)]

    col_mapa, col_grafico = st.columns([1.8, 1])

    with col_mapa:
        st.subheader(f"🗺️ Mapa Georreferenciado ({len(df_filtrado)} incidencias)")
        centro_lat = float(df_filtrado["lat"].iloc[-1]) if len(df_filtrado) > 0 else LAT_VALLENAR
        centro_lon = float(df_filtrado["lon"].iloc[-1]) if len(df_filtrado) > 0 else LON_VALLENAR
        
        m = folium.Map(location=[centro_lat, centro_lon], zoom_start=14)
        for _, row in df_filtrado.iterrows():
            folium.Marker(
                location=[float(row["lat"]), float(row["lon"])],
                popup=f"<b>#{row['id']}</b>: {row['categoria']}",
                tooltip=f"#{row['id']} - {row['categoria']}"
            ).add_to(m)
            
        st_folium(m, width="100%", height=350, key="mapa_vallenar")

    with col_grafico:
        st.subheader("📊 Distribución por Sector")
        if len(df_filtrado) > 0:
            fig = px.pie(df_filtrado, names='sector', hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos para mostrar en la gráfica.")

    st.markdown("---")
    st.subheader("📋 Galería de Reportes y Evidencia Fotográfica")
    if len(df_filtrado) > 0:
        for _, row in df_filtrado.iloc[::-1].iterrows():
            with st.expander(f"📍 Folio #{row['id']} - {row['categoria']} ({row['sector']}) — Estado: [{row['estado']}]"):
                col_text, col_img = st.columns([2, 1])
                
                with col_text:
                    st.write(f"**Urgencia:** {row['prioridad']} | **Fecha:** {row['fecha']}")
                    st.info(f"**Descripción del Vecino:** {row['comentario']}")
                    st.success(f"**Respuesta Municipal:** {row.get('obs_municipal', 'En espera de revisión.')}")
                
                with col_img:
                    foto_path = str(row.get("foto_path", "Sin foto"))
                    if foto_path != "Sin foto" and os.path.exists(foto_path):
                        st.image(foto_path, caption=f"Evidencia Folio #{row['id']}", use_container_width=True)
                    else:
                        st.caption("📷 Sin fotografía adjunta")
    else:
        st.info("No se encontraron reportes con los filtros seleccionados.")

# ----------------------------------------------------
# VISTA 3: PANEL DE ADMINISTRACIÓN (Con Opción de Eliminar)
# ----------------------------------------------------
elif opcion_menu == "⚙️ Panel de Administración":
    st.subheader("⚙️ Panel de Administración Municipal (Gestión e Informes)")
    pass_input = st.text_input("Ingrese Clave de Administrador:", type="password")
    
    if pass_input == CLAVE_ADMIN:
        st.success("🔑 Sesión de Administrador Activa")
        df = st.session_state.incidencias
        
        if len(df) > 0:
            rep_id = st.selectbox(
                "Gestionar / Eliminar Incidencia:", 
                options=df["id"].tolist(), 
                format_func=lambda x: f"Folio #{x} - {df[df['id']==x]['categoria'].values[0]} ({df[df['id']==x]['sector'].values[0]})"
            )
            idx = df[df["id"] == rep_id].index[0]
            
            # Mostrar evidencia en el panel de administración
            foto_admin = str(df.loc[idx, "foto_path"])
            if foto_admin != "Sin foto" and os.path.exists(foto_admin):
                st.image(foto_admin, caption="Foto adjunta por el vecino", width=300)

            # --- SECCIÓN 1: ACTUALIZAR ESTADO Y RESPUESTA ---
            st.markdown("#### ✏️ Editar Estado y Respuesta")
            col_edit1, col_edit2 = st.columns([1, 2])
            with col_edit1:
                nuevo_estado = st.selectbox("Cambiar Estado:", ["Pendiente", "En Proceso", "Resuelto"], index=["Pendiente", "En Proceso", "Resuelto"].index(df.loc[idx, "estado"]))
            with col_edit2:
                nueva_obs = st.text_input("Observación Interna / Respuesta al Vecino:", value=str(df.loc[idx, "obs_municipal"]))
                
            if st.button("💾 Actualizar y Guardar Cambios en Excel", use_container_width=True):
                st.session_state.incidencias.loc[idx, "estado"] = nuevo_estado
                st.session_state.incidencias.loc[idx, "obs_municipal"] = nueva_obs
                guardar_datos_excel(st.session_state.incidencias)
                
                correo_destinatario = str(df.loc[idx, "contacto"])
                cat_actual = str(df.loc[idx, "categoria"])
                sec_actual = str(df.loc[idx, "sector"])
                enviado, msj = enviar_correo_notificacion(correo_destinatario, rep_id, nuevo_estado, cat_actual, sec_actual)
                
                st.success(f"✅ Reporte #{rep_id} actualizado con éxito.")
                st.rerun()

            st.markdown("---")

            # --- SECCIÓN 2: ELIMINAR REPORTE ---
            st.markdown("#### 🗑️ Eliminar Reporte")
            confirmar_borrado = st.checkbox(f"⚠️ Confirmar que deseas eliminar permanentemente el reporte Folio #{rep_id}")
            
            if st.button("❌ Eliminar Reporte", use_container_width=True, type="primary"):
                if confirmar_borrado:
                    # 1. Si el reporte tiene foto en disco, la eliminamos
                    if foto_admin != "Sin foto" and os.path.exists(foto_admin):
                        try:
                            os.remove(foto_admin)
                        except Exception:
                            pass
                    
                    # 2. Eliminar la fila del dataframe en session_state y en Excel
                    st.session_state.incidencias = st.session_state.incidencias[st.session_state.incidencias["id"] != rep_id].reset_index(drop=True)
                    guardar_datos_excel(st.session_state.incidencias)
                    
                    st.success(f"🗑️ El reporte Folio #{rep_id} ha sido eliminado permanentemente.")
                    st.rerun()
                else:
                    st.warning("Por favor marca la casilla de confirmación antes de presionar Eliminar.")

        else:
            st.info("No hay reportes ingresados actualmente para gestionar.")

        st.markdown("---")
        st.subheader("📊 Descargas y Reportes Oficiales")
        col_excel, col_pdf = st.columns(2)
        
        with col_excel:
            if os.path.exists(EXCEL_FILE):
                with open(EXCEL_FILE, "rb") as f:
                    st.download_button(
                        label="📊 Descargar Base de Datos (Excel)",
                        data=f,
                        file_name=f"Reportes_Vallenar_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

        with col_pdf:
            pdf_bytes = generar_pdf_gestion(df)
            st.download_button(
                label="📥 Descargar Informe de Gestión (PDF)",
                data=pdf_bytes,
                file_name=f"Informe_Vallenar_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
    elif pass_input != "":
        st.error("❌ Clave de acceso incorrecta")

# ----------------------------------------------------
# Pie de Página
# ----------------------------------------------------
st.markdown("""
    <div class="footer-card">
        <h3>🌟 ¡Construyendo juntos el Vallenar que soñamos!</h3>
        <p>Tu participación ciudadana es el motor clave para transformar y cuidar nuestros barrios.</p>
        <div class="footer-badges">
            <span class="footer-badge-item">🌐 Gestión Territorial</span>
            <span class="footer-badge-item">🤝 Ciencia Ciudadana</span>
            <span class="footer-badge-item">🏛️ Ilustre Municipalidad de Vallenar</span>
            <span class="footer-badge-item">📍 Región de Atacama, Chile</span>
        </div>
    </div>
""", unsafe_allow_html=True)
