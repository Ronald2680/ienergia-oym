import streamlit as st
from utils.database import get_conn
from utils.auth import is_admin

def render():
    st.title("👥 Personal")
    conn = get_conn()

    if is_admin():
        if st.button("➕ Agregar personal"):
            st.session_state["show_form_personal"] = True

        if st.session_state.get("show_form_personal"):
            with st.form("form_personal", clear_on_submit=True):
                st.subheader("Nuevo trabajador")
                col1, col2 = st.columns(2)
                nuevo_id = col1.text_input("ID *", placeholder="PERS-005")
                nombre = col2.text_input("Nombre completo *")
                col3, col4 = st.columns(2)
                especialidad = col3.selectbox("Especialidad *", ["Eléctrico","Mecánico","Instrumentación","Civil","Otro"])
                region = col4.selectbox("Región", ["RM","V Región","VI Región","IV Región","III Región","Otro"])
                col5, col6 = st.columns(2)
                certs = col5.text_input("Certificaciones", placeholder="AT, Altura, Izaje")
                venc_cert = col6.date_input("Vencimiento cert. más próxima")
                col7, col8, col9 = st.columns(3)
                domicilio_lat = col7.text_input("Latitud domicilio")
                domicilio_lng = col8.text_input("Longitud domicilio")
                puede_liderar = col9.checkbox("¿Puede liderar?")
                vehiculos = conn.execute("SELECT id FROM vehiculos WHERE disponible=1").fetchall()
                id_vehiculo = st.selectbox("Vehículo asignado", ["—"] + [v["id"] for v in vehiculos])
                submitted = st.form_submit_button("Guardar")
                if submitted and nombre and nuevo_id:
                    conn2 = get_conn()
                    try:
                        conn2.execute("""INSERT INTO personal (id,nombre,especialidad,certificaciones,
                            fecha_venc_cert,region,domicilio_lat,domicilio_lng,id_vehiculo,puede_liderar)
                            VALUES (?,?,?,?,?,?,?,?,?,?)""",
                            (nuevo_id, nombre, especialidad, certs,
                             venc_cert.isoformat(), region,
                             float(domicilio_lat) if domicilio_lat else None,
                             float(domicilio_lng) if domicilio_lng else None,
                             id_vehiculo if id_vehiculo != "—" else None,
                             int(puede_liderar)))
                        conn2.commit()
                        st.success(f"Personal {nuevo_id} agregado.")
                        st.session_state["show_form_personal"] = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                    finally:
                        conn2.close()
            if st.button("Cancelar##pers"):
                st.session_state["show_form_personal"] = False
                st.rerun()

    personal = conn.execute("SELECT * FROM personal ORDER BY nombre").fetchall()
    for p in personal:
        with st.container(border=True):
            c1, c2, c3, c4, c5 = st.columns([3,2,2,2,1])
            c1.markdown(f"**{p['nombre']}** `{p['id']}`")
            c2.markdown(f"🔧 {p['especialidad']}")
            c3.markdown(f"📋 {p['certificaciones'] or '—'}")
            c4.markdown(f"📍 {p['region']}")
            lider = "✅ Lidera" if p["puede_liderar"] else ""
            c5.markdown(lider)
            if p["fecha_venc_cert"]:
                from datetime import date
                try:
                    dias = (date.fromisoformat(p["fecha_venc_cert"]) - date.today()).days
                    if dias < 90:
                        st.warning(f"⚠️ Certificación vence en {dias} días ({p['fecha_venc_cert']})")
                except: pass
    conn.close()
