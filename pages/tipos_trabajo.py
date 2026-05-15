import streamlit as st
from utils.database import get_conn
from utils.auth import is_admin

def render():
    st.title("⚙️ Tipos de trabajo")
    conn = get_conn()
    if is_admin():
        if st.button("➕ Agregar tipo"):
            st.session_state["show_form_tipo"] = True
        if st.session_state.get("show_form_tipo"):
            with st.form("form_tipo", clear_on_submit=True):
                c1,c2 = st.columns(2)
                nid = c1.text_input("ID *", placeholder="TIPO-008")
                nombre = c2.text_input("Nombre *")
                c3,c4 = st.columns(2)
                cat = c3.selectbox("Categoría", ["Eléctrico","Mecánico","Civil","Instrumentación","Otro"])
                riesgo = c4.selectbox("Nivel de riesgo", ["Alto","Medio","Bajo"])
                c5,c6,c7 = st.columns(3)
                esp_req = c5.text_input("Especialidad requerida")
                cert_req = c6.text_input("Certificación requerida")
                pers_min = c7.number_input("Personal mínimo", 1, 10, 1)
                c8,c9 = st.columns(2)
                dur_est = c8.number_input("Duración estimada (h)", 0.5, 24.0, 3.0, step=0.5)
                desv = c9.number_input("Desviación estándar (h)", 0.0, 10.0, 1.0, step=0.5)
                herramientas = st.text_area("Herramientas base (separadas por coma)", height=60)
                id_pts = st.text_input("ID PTS asociado")
                req_maq = st.checkbox("¿Siempre requiere maquinaria?")
                if st.form_submit_button("Guardar") and nombre and nid:
                    conn2 = get_conn()
                    try:
                        conn2.execute("""INSERT INTO tipos_trabajo (id,nombre_tipo,categoria,especialidad_req,
                            certificacion_req,personal_minimo,duracion_est_h,desv_estandar_h,
                            herramientas_base,nivel_riesgo,id_pts,requiere_maquinaria)
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (nid,nombre,cat,esp_req,cert_req,pers_min,dur_est,desv,herramientas,riesgo,id_pts,int(req_maq)))
                        conn2.commit()
                        st.success("Tipo de trabajo agregado."); st.session_state["show_form_tipo"]=False; st.rerun()
                    except Exception as e: st.error(f"Error: {e}")
                    finally: conn2.close()
            if st.button("Cancelar##tipo"): st.session_state["show_form_tipo"]=False; st.rerun()

    tipos = conn.execute("SELECT * FROM tipos_trabajo ORDER BY categoria, nombre_tipo").fetchall()
    cat_actual = None
    for t in tipos:
        if t["categoria"] != cat_actual:
            cat_actual = t["categoria"]
            st.markdown(f"### {cat_actual}")
        with st.container(border=True):
            c1,c2,c3,c4 = st.columns([3,2,2,2])
            c1.markdown(f"**{t['nombre_tipo']}** `{t['id']}`")
            riesgo_icons = {"Alto":"🔴","Medio":"🟡","Bajo":"🟢"}
            c2.markdown(f"{riesgo_icons.get(t['nivel_riesgo'],'⚪')} Riesgo: {t['nivel_riesgo']}")
            c3.markdown(f"⏱ {t['duracion_est_h']}h ± {t['desv_estandar_h']}h")
            c4.markdown(f"👥 Mín. {t['personal_minimo']} · PTS: {t['id_pts'] or '—'}")
            st.caption(f"Especialidad: {t['especialidad_req'] or '—'} · Cert.: {t['certificacion_req'] or '—'}")
            if t["herramientas_base"]:
                st.caption(f"🔧 Herramientas: {t['herramientas_base']}")
    conn.close()
