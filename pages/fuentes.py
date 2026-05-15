import streamlit as st

def render():
    st.title("🔌 Fuentes de datos")
    st.caption("Estado de integración de todas las fuentes de datos del sistema.")

    st.subheader("Fuentes automáticas — requieren integración API")

    fuentes_auto = [
        ("📡", "GPS Vehículos", "API REST del proveedor GPS actual. Alimenta tiempos reales de viaje, odómetro y trayectos.",
         "Pendiente", ["URL del API endpoint", "API Key o Token", "Formato: JSON con vehiculo_id, lat, lng, fecha_hora, km_odometro"]),
        ("⚡", "SCADA / Monitoreo FV", "Plataforma de monitoreo fotovoltaico (iops.ienergia.cl u similar). Genera alertas automáticas al sistema.",
         "Pendiente", ["URL del API o webhook", "Credenciales de servicio", "Mapeo de proyectos SCADA → proyectos en sistema"]),
        ("🌤", "API Clima (OpenWeatherMap)", "Datos de viento y lluvia por coordenadas de proyecto para calcular apto_trabajo_ext automáticamente.",
         "Pendiente", ["API Key de OpenWeatherMap (gratuita)", "Frecuencia: diaria automática", "Umbrales: lluvia < 5mm y viento < 60 km/h"]),
        ("🛣", "API Rutas y Peajes", "Google Maps Distance Matrix o similar. Calcula tiempos y costos entre proyectos.",
         "Pendiente", ["Google Maps API Key", "Presupuesto mensual estimado: < USD 10", "Actualizar tabla distancias_proyectos"]),
    ]

    for icon, nombre, desc, estado, config in fuentes_auto:
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"{icon} **{nombre}**")
                st.caption(desc)
                with st.expander("Ver requisitos de configuración"):
                    for req in config:
                        st.markdown(f"- {req}")
            with c2:
                if estado == "Conectado":
                    st.success("✅ Conectado")
                elif estado == "Parcial":
                    st.warning("⚠️ Parcial")
                else:
                    st.error("🔴 Pendiente")

    st.divider()
    st.subheader("Fuentes manuales — carga por Excel o formulario")

    fuentes_manual = [
        ("👥", "Personal y certificaciones", "Excel con una fila por trabajador. Columnas: id, nombre, especialidad, certificaciones, fecha_venc, region, lat_domicilio, lng_domicilio", "Parcial"),
        ("📋", "PTS (Procedimientos de Trabajo Seguro)", "PDF de cada procedimiento. El sistema puede extraer herramientas, personal mínimo y nivel de riesgo con IA.", "Requerido"),
        ("📦", "Stock de materiales", "Excel de bodega con cantidades actuales. Actualización semanal mínima recomendada.", "Parcial"),
        ("🗂", "Historial de trabajos pasados", "Excel con trabajos ejecutados. Columnas: proyecto, tipo, fecha, duración_real, personal, retrasos, resultado.", "Requerido"),
        ("📍", "Distancias entre proyectos", "Se calcula automáticamente desde GPS o Google Maps. También se puede ingresar manualmente.", "Pendiente"),
        ("🏗", "Maquinaria subcontratada", "Formulario con proveedores de grúas y maquinaria: contacto, lead time, costo/hora, regiones.", "Pendiente"),
    ]

    for icon, nombre, desc, estado in fuentes_manual:
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"{icon} **{nombre}**")
            c1.caption(desc)
            if estado == "Conectado" or estado == "Parcial":
                c2.warning("⚠️ Parcial")
            elif estado == "Requerido":
                c2.error("❗ Requerido")
            else:
                c2.info("ℹ️ Pendiente")

    st.divider()
    st.subheader("📤 Importar datos desde Excel")
    st.info("Sube un archivo Excel con datos históricos o datos maestros para carga masiva.")

    tipo_import = st.selectbox("Tipo de datos a importar", [
        "Personal", "Proyectos", "Materiales", "Vehículos",
        "Tipos de trabajo", "Historial de trabajos", "Distancias entre proyectos"
    ])
    uploaded = st.file_uploader("Selecciona el archivo Excel (.xlsx)", type=["xlsx"])
    if uploaded:
        st.warning("⚠️ La importación masiva desde Excel se habilitará en la próxima versión. Por ahora usa los formularios individuales en cada módulo.")

    st.divider()
    st.subheader("📥 Exportar datos")
    col1, col2, col3 = st.columns(3)
    if col1.button("Exportar trabajos (Excel)", use_container_width=True):
        st.info("Función disponible próximamente.")
    if col2.button("Exportar ejecuciones (Excel)", use_container_width=True):
        st.info("Función disponible próximamente.")
    if col3.button("Exportar ventanas IA (Excel)", use_container_width=True):
        st.info("Función disponible próximamente.")
