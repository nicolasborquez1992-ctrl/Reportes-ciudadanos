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

# Librerías para generación de PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ----------------------------------------------------
# Configuración Inicial de la Aplicación
# ----------------------------------------------------
st.set_page_config(
    page_title="Vallenar Resuelve - Reportes Urbanos",
    page_icon="🏙️",
    layout="wide"
)

# Estilos CSS Personalizados (Traduce y oculta elementos en inglés de la interfaz)
st.markdown("""
    <style>
    .main-title { font-size: 2.2rem; font-weight: 800; color: #1E3A8A; margin: 0; }
    .sub-title { font-size: 1.05rem; color: #4B5563; margin-top: 5px; }
    .badge-vallenar { background-color: #1E3A8A; color: white; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600; }
    
    /* Ocultar el botón superior 'Share' de Streamlit */
    header[data-testid="stHeader"] {
        visibility: hidden;
    }
    </style>
""", unsafe_allow_html=True)

# Coordenadas predeterminadas del centro de Vallenar
LAT_VALLENAR = -28.5750
LON_VALLENAR = -70.7580

# ----------------------------------------------------
# Módulo 1: Envío de Notificaciones por Correo
# ----------------------------------------------------
def enviar_correo_notificacion(destinatario, id_reporte, nuevo_estado, categoria, sector):
    """
    Envía un correo automático al vecino notificando el cambio de estado de su reporte.
    """
    if not destinatario or "@" not in destinatario or destinatario == "No especificado":
        return False, "No se registró un correo válido para este reporte."

    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SENDER_EMAIL = "contacto.vallenar.resuelve@gmail.com"
    SENDER_PASSWORD = "xxxx xxxx xxxx xxxx"

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
    msg['From'] = SENDER_EMAIL
    msg['To'] = destinatario
    msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo, 'plain'))

    try:
        # Servidor SMTP (descomentar en producción):
        # server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        # server.starttls()
        # server.login(SENDER_EMAIL, SENDER_PASSWORD)
        # server.sendmail(SENDER_EMAIL, destinatario, msg.as_string())
        # server.quit()
        return True, "Correo enviado correctamente."
    except Exception as e:
        return False, str(e)

# ----------------------------------------------------
# Módulo 2: Generador de Informes PDF para Autoridades
# ----------------------------------------------------
def generar_pdf_gestion(df_data):
    """
    Genera un archivo PDF institucional con métricas e inventario consolidado.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter, 
        rightMargin=36, 
        leftMargin=36, 
        topMargin=36, 
        bottomMargin=36
    )
    story = []
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Heading1'],
        fontSize=15,
        textColor=colors.HexColor("#1E3A8A"),
        alignment=1,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'HeaderSubTitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor("#4B5563"),
        alignment=1,
        spaceAfter=15
    )

    # Encabezado institucional
    story.append(Paragraph("ILUSTRE MUNICIPALIDAD DE VALLENAR", title_style))
    story.append(Paragraph("<b>INFORME DE GESTIÓN DE INCIDENCIAS URBANAS</b>", subtitle_style))
    story.append(Paragraph(f"<b>Fecha de Emisión:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 10))

    # Resumen Ejecutivo
    total = len(df_data)
    pendientes = len(df_data[df_data["estado"] == "Pendiente"])
    proceso = len(df_data[df_data["estado"] == "En Proceso"])
    resueltos = len(df_data[df_data["estado"] == "Resuelto"])

    resumen_text = f"""
    <b>Resumen Estadístico del Periodo:</b><br/>
    • Total de incidencias registradas: <b>{total}</b><br/>
    • Casos pendientes: <b>{pendientes}</b> ({round((pendientes/total)*100, 1) if total>0 else 0}%)<br/>
    • Casos en proceso de solución: <b>{proceso}</b> ({round((proceso/total)*100, 1) if total>0 else 0}%)<br/>
    • Casos resueltos exitosamente: <b>{resueltos}</b> ({round((resueltos/total)*100, 1) if total>0 else 0}%)
    """
    story.append(Paragraph(resumen_text, styles['Normal']))
    story.append(Spacer(1, 15))

    # Tabla Consolidada
    story.append(Paragraph("<b>Detalle General de Reportes:</b>", styles['Normal']))
    story.append(Spacer(1, 8))

    table_data = [["Folio", "Fecha", "Sector", "Categoría", "Urgencia", "Estado"]]
    for _, row in df_data.iterrows():
        table_data.append([
            f"#{row['id']}",
            str(row["fecha"]),
            str(row["sector"]),
            str(row["categoria"]),
            str(row["prioridad"]),
            str(row["estado"])
        ])

    t = Table(table_data, colWidths=[40, 70, 85, 180, 65, 80])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
    ]))
    
    story.append(t)
    doc.build(story)
    buffer.seek(0)
    return buffer

# ----------------------------------------------------
# Encabezado Web
# ----------------------------------------------------
col_logo, col_texto = st.columns([1, 5])
with col_logo:
    try:
        st.image("escudo.png", width=95)
    except:
        st.write("🏛️")

with col_texto:
    st.markdown("""
        <div>
            <span class="badge-vallenar">ILUSTRE MUNICIPALIDAD DE VALLENAR</span>
            <h1 class="main-title">🏙️ Vallenar Resuelve</h1>
            <p class="sub-title">Plataforma Digital de Gestión Territorial y Atención Ciudadana</p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ----------------------------------------------------
# Inicialización de Datos Local
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
            "comentario": "Evento de gran profundidad cerca de la escuela.",
            "prioridad": "Alta",
            "contacto": "vecino.torreblanca@gmail.com",
            "obs_municipal": "Asignado a cuadrilla de obras.",
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
            "comentario": "Luminaria apagada en calle Prat.",
            "prioridad": "Media",
            "contacto": "comercio.centro@vallenar.cl",
            "obs_municipal": "Repuestos solicitados en bodega.",
            "imagen": None
        }
    ])

# ----------------------------------------------------
# Formulario Lateral de Registro
# ----------------------------------------------------
st.sidebar.header("📝 Nuevo Reporte Ciudadano")
sectores_vallenar = ["Centro", "Torreblanca", "Baquedano", "Quinta Valle", "Ventanas", "O'Higgins", "Hermanos Carrera", "Otro Sector"]

sector_input = st.sidebar.selectbox("Sector:", sectores_vallenar)

cat_input = st.sidebar.selectbox(
    "Categoría del Problema:", 
    ["Bache / Evento en Calzada", "Luminaria Defectuosa", "Microbasural / Escombros", "Fuga de Agua / Alcantarillado", "Semáforo Defectuoso", "Señaletica Dañada", "Arbolado / Peligro de Caída"]
)

prioridad_input = st.sidebar.select_slider("Urgencia Estimada:", options=["Baja", "Media", "Alta", "Crítica"])

# Captura de geolocalización GPS
location = get_geolocation()

if location and "coords" in location:
    lat_input = float(location["coords"]["latitude"])
    lon_input = float(location["coords"]["longitude"])
    st.sidebar.success(f"📍 GPS Detectado: {lat_input:.4f}, {lon_input:.4f}")
else:
    lat_input, lon_input = LAT_VALLENAR, LON_VALLENAR
    st.sidebar.info("📍 Usando ubicación central de Vallenar")

st.sidebar.subheader("📷 Detalles y Notificación")
comentario_input = st.sidebar.text_area("Descripción detallada:")
contacto_input = st.sidebar.text_input("Correo electrónico del vecino:", placeholder="ejemplo@correo.cl")
foto_input = st.sidebar.file_uploader("Adjuntar Foto:", type=["jpg", "png", "jpeg"])

if st.sidebar.button("🚀 Ingresar Reporte", use_container_width=True):
    if comentario_input.strip() == "":
        st.sidebar.warning("Por favor agrega una pequeña descripción del problema.")
    else:
        imagen_guardada = Image.open(foto_input) if foto_input is not None else None
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
            "contacto": contacto_input.strip() if contacto_input.strip() != "" else "No especificado",
            "obs_municipal": "En espera de revisión por el departamento correspondiente.",
            "imagen": imagen_guardada
        }])
        
        st.session_state.incidencias = pd.concat([st.session_state.incidencias, nueva_fila], ignore_index=True)
        st.sidebar.success(f"¡Reporte #{nuevo_id} ingresado y georreferenciado!")
        st.rerun()

# ----------------------------------------------------
# Panel Principal: Métricas y Filtros
# ----------------------------------------------------
df = st.session_state.incidencias

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Incidentes", len(df))
m2.metric("Pendientes", len(df[df["estado"] == "Pendiente"]))
m3.metric("En Proceso", len(df[df["estado"] == "En Proceso"]))
m4.metric("Resueltos", len(df[df["estado"] == "Resuelto"]))

st.markdown("---")

st.subheader("🔍 Filtros de Búsqueda")
f_col1, f_col2, f_col3 = st.columns(3)

with f_col1:
    filtro_sector = st.multiselect(
        "Sector:", 
        options=sectores_vallenar, 
        default=[],
        placeholder="Seleccionar opciones..."
    )

with f_col2:
    filtro_estado = st.multiselect(
        "Estado:", 
        options=["Pendiente", "En Proceso", "Resuelto"], 
        default=[],
        placeholder="Seleccionar opciones..."
    )

with f_col3:
    filtro_prioridad = st.multiselect(
        "Urgencia:", 
        options=["Baja", "Media", "Alta", "Crítica"], 
        default=[],
        placeholder="Seleccionar opciones..."
    )

df_filtrado = df.copy()
if filtro_sector: df_filtrado = df_filtrado[df_filtrado["sector"].isin(filtro_sector)]
if filtro_estado: df_filtrado = df_filtrado[df_filtrado["estado"].isin(filtro_estado)]
if filtro_prioridad: df_filtrado = df_filtrado[df_filtrado["prioridad"].isin(filtro_prioridad)]

# ----------------------------------------------------
# Visualización: Mapa Interactivo Georreferenciado
# ----------------------------------------------------
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader(f"🗺️ Mapa Georreferenciado ({len(df_filtrado)} incidencias)")
    
    centro_lat = float(df_filtrado["lat"].iloc[-1]) if len(df_filtrado) > 0 else LAT_VALLENAR
    centro_lon = float(df_filtrado["lon"].iloc[-1]) if len(df_filtrado) > 0 else LON_VALLENAR
    
    m = folium.Map(location=[centro_lat, centro_lon], zoom_start=14)
    
    for _, row in df_filtrado.iterrows():
        popup_html = f"""
        <b>Reporte #{row['id']}</b><br>
        <b>Categoría:</b> {row['categoria']}<br>
        <b>Sector:</b> {row['sector']}<br>
        <b>Estado:</b> {row['estado']}
        """
        folium.Marker(
            location=[float(row["lat"]), float(row["lon"])],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"#{row['id']} - {row['categoria']}"
        ).add_to(m)
        
    st_folium(m, width=800, height=450, key="mapa_vallenar")

with col_right:
    st.subheader("📊 Distribución por Sector")
    if len(df_filtrado) > 0:
        fig_sector = px.pie(df_filtrado, names="sector", hole=0.35)
        st.plotly_chart(fig_sector, use_container_width=True)

st.markdown("---")

# ----------------------------------------------------
# Panel de Administración Municipal
# ----------------------------------------------------
with st.expander("🛠️ Panel de Administración Municipal (Gestión e Informes)"):
    st.write("Gestiona el estado de las incidencias, envía notificaciones automáticas y descarga reportes en PDF.")
    
    if len(df) > 0:
        rep_id = st.selectbox(
            "Seleccionar Reporte a gestionar:", 
            options=df["id"].tolist(), 
            format_func=lambda x: f"Folio #{x} - {df[df['id']==x]['categoria'].values[0]} ({df[df['id']==x]['sector'].values[0]})"
        )
        idx = df[df["id"] == rep_id].index[0]
        
        c_est, c_obs = st.columns([1, 2])
        with c_est:
            nuevo_estado = st.selectbox("Cambiar Estado:", ["Pendiente", "En Proceso", "Resuelto"], index=["Pendiente", "En Proceso", "Resuelto"].index(df.loc[idx, "estado"]))
        with c_obs:
            obs_actual = str(df.loc[idx, "obs_municipal"]) if pd.notna(df.loc[idx, "obs_municipal"]) else ""
            nueva_obs = st.text_input("Observación Interna / Avance:", value=obs_actual)
            
        if st.button("💾 Actualizar Estado y Notificar al Vecino", use_container_width=True):
            st.session_state.incidencias.loc[idx, "estado"] = nuevo_estado
            st.session_state.incidencias.loc[idx, "obs_municipal"] = nueva_obs
            
            correo_vecino = df.loc[idx, "contacto"]
            if nuevo_estado in ["En Proceso", "Resuelto"] and correo_vecino != "No especificado":
                exito, msg = enviar_correo_notificacion(
                    destinatario=correo_vecino,
                    id_reporte=rep_id,
                    nuevo_estado=nuevo_estado,
                    categoria=df.loc[idx, "categoria"],
                    sector=df.loc[idx, "sector"]
                )
                if exito:
                    st.success(f"✅ Reporte #{rep_id} actualizado. Notificación enviada a {correo_vecino}.")
                else:
                    st.warning(f"✅ Estado actualizado, pero no se envió correo: {msg}")
            else:
                st.success(f"✅ Reporte #{rep_id} actualizado exitosamente.")
            st.rerun()

    st.markdown("---")
    st.subheader("📄 Reportes de Gestión para Autoridades")
    
    pdf_bytes = generar_pdf_gestion(df)
    
    col_pdf1, col_pdf2 = st.columns([1, 2])
    with col_pdf1:
        st.download_button(
            label="📥 Descargar Informe Mensual (PDF)",
            data=pdf_bytes,
            file_name=f"Informe_Gestion_Vallenar_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    with col_pdf2:
        st.caption("Genera un documento PDF oficial con membrete municipal, métricas generales e inventario detallado de casos.")

# ----------------------------------------------------
# Galería e Histórico de Incidencias
# ----------------------------------------------------
st.markdown("---")
st.subheader("📋 Galería de Reportes y Evidencia Fotográfica")

if len(df_filtrado) > 0:
    for _, row in df_filtrado.iloc[::-1].iterrows():
        with st.expander(f"📍 Folio #{row['id']} - {row['categoria']} ({row['sector']}) — Estado: [{row['estado']}]"):
            c_info, c_img = st.columns([2, 1])
            with c_info:
                st.write(f"*Fecha:* {row['fecha']} | *Urgencia:* {row['prioridad']}")
                st.write(f"*Contacto Vecino:* {row.get('contacto', 'No especificado')}")
                st.info(f"*Descripción del Vecino:* {row['comentario']}")
                st.success(f"*Respuesta Municipal:* {row.get('obs_municipal', 'Sin observaciones aún.')}")
            with c_img:
                if row["imagen"] is not None:
                    st.image(row["imagen"], caption=f"Evidencia Folio #{row['id']}", use_container_width=True)
