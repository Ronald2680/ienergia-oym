import streamlit as st
from utils.database import get_conn
from utils.auth import is_admin

def render():
    st.title("📍 Proyectos")
    conn = get_conn()

    if is_admin():
        if st.button("➕ Agregar proyecto"):
            st.session_state["show_form_proy"] = True
        if st.session_state.get("show_form_proy"):
            with st.form("form_proy", clear_on_submit=True):
                c1, c2 = st.columns(2)
                nuevo_id = c1.text_input("ID *", placeholder="PROY-006")
                nombre = c2.text_input("Nombre *")
                c3, c4 = st.columns(2)
                cliente = c3.text_input("Cliente")
                region = c4.selectbox("Región", ["RM","V Región","VI Región","IV Región","Otro"])
                c5, c6 = st.columns(2)
                lat = c5.text_input("Latitud *")
                lng = c6.text_input("Longitud *")
                c7, c8 = st.columns(2)
                criticidad = c7.selectbox("Criticidad", ["Alta","Media","Baja"])
                acceso = c8.selectbox("Tipo acceso", ["Pavimento","Camino tierra","4x4"])
                c9, c10 = st.columns(2)
                h_ap = c9.text_input("Hora apertura", value="07:00")
                h_ci = c10.text_input("Hora cierre", value="18:00")
                req_perm = st.checkbox("¿Requiere permiso de trabajo?")
                lead_perm = st.number_input("Lead time permiso (días)", 0, 10, 0)
                contacto = st.text_input("Contacto cliente")
                restricciones = st.text_area("Restricciones", height=60)
                if st.form_submit_button("Guardar") and nombre and nuevo_id and lat and lng:
                    conn2 = get_conn()
                    try:
                        conn2.execute("""INSERT INTO proyectos (id,nombre,cliente,latitud,longitud,region,
                            criticidad,hora_apertura,hora_cierre,requiere_permiso,lead_time_permiso_d,
                            contacto_cliente,tipo_acceso,restricciones)
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (nuevo_id,nombre,cliente,float(lat),float(lng),region,criticidad,
                             h_ap,h_ci,int(req_perm),lead_perm,contacto,acceso,restricciones))
                        conn2.commit()
                        st.success("Proyecto agregado."); st.session_state["show_form_proy"]=False; st.rerun()
                    except Exception as e: st.error(f"Error: {e}")
                    finally: conn2.close()
            if st.button("Cancelar##proy"): st.session_state["show_form_proy"]=False; st.rerun()

    proyectos = conn.execute("SELECT * FROM proyectos WHERE activo=1 ORDER BY nombre").fetchall()
    for p in proyectos:
        with st.container(border=True):
            c1,c2,c3,c4 = st.columns([3,2,2,3])
            c1.markdown(f"**{p['nombre']}** `{p['id']}`")
            c2.markdown(f"🏢 {p['cliente']}")
            c3.markdown(f"📍 {p['region']}")
            c4.markdown(f"🕐 {p['hora_apertura']}–{p['hora_cierre']} · {'🔒 Permiso' if p['requiere_permiso'] else '🔓 Libre'}")
            st.caption(f"Criticidad: {p['criticidad']} · Acceso: {p['tipo_acceso']} · Contacto: {p['contacto_cliente'] or '—'}")
            if p['restricciones']: st.caption(f"⚠️ {p['restricciones']}")
    conn.close()
