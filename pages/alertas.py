import streamlit as st
from utils.database import get_conn
from utils.auth import is_supervisor
import datetime

NIVEL_ICON = {"Crítico":"🔴","Alto":"🟠","Medio":"🟡","Bajo":"🟢"}

def render():
    st.title("🔔 Alertas / Tareas")
    conn = get_conn()

    tab_todas, tab_sin_asignar, tab_convertidas = st.tabs(["Todas", "Sin asignar", "Convertidas a trabajo"])

    def render_alerta(a, proyecto_nombre):
        icon = NIVEL_ICON.get(a["nivel_falla"], "⚪")
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"{icon} **{a['id']} · {proyecto_nombre}** — {a['sistema_afectado']}")
                st.caption(f"Impacto: **{a['impacto_kw']} kW** · Recurrencia: {a['recurrencia']} · {a['estado']} · {a['fecha_registro'][:16]}")
                st.write(a["descripcion"])
            with col2:
                if is_supervisor() and a["estado"] == "Sin asignar":
                    if st.button("➡ Crear trabajo", key=f"crear_{a['id']}"):
                        st.session_state[f"crear_trabajo_alerta"] = dict(a)
                        st.session_state.page = "trabajos"
                        st.rerun()
                    if st.button("🧠 Analizar IA", key=f"ai_{a['id']}"):
                        st.session_state[f"analizar_alerta"] = dict(a)

            if st.session_state.get("analizar_alerta", {}).get("id") == a["id"]:
                with st.spinner("Analizando con IA..."):
                    from utils.ai_engine import analyze_alerta
                    proyecto_row = conn.execute("SELECT * FROM proyectos WHERE id=?", (a["id_proyecto"],)).fetchone()
                    resp = analyze_alerta(dict(a), dict(proyecto_row) if proyecto_row else {})
                st.info(resp)
                if st.button("Cerrar análisis", key=f"cerrar_{a['id']}"):
                    del st.session_state["analizar_alerta"]

    with tab_todas:
        alertas = conn.execute("""
            SELECT a.*, p.nombre as proyecto_nombre
            FROM alertas a LEFT JOIN proyectos p ON a.id_proyecto=p.id
            ORDER BY CASE a.nivel_falla WHEN 'Crítico' THEN 1 WHEN 'Alto' THEN 2 WHEN 'Medio' THEN 3 ELSE 4 END,
                     a.fecha_registro DESC
        """).fetchall()
        for a in alertas:
            render_alerta(a, a["proyecto_nombre"] or "—")

    with tab_sin_asignar:
        alertas = conn.execute("""
            SELECT a.*, p.nombre as proyecto_nombre
            FROM alertas a LEFT JOIN proyectos p ON a.id_proyecto=p.id
            WHERE a.estado='Sin asignar'
        """).fetchall()
        if not alertas:
            st.info("No hay alertas sin asignar.")
        for a in alertas:
            render_alerta(a, a["proyecto_nombre"] or "—")

    with tab_convertidas:
        alertas = conn.execute("""
            SELECT a.*, p.nombre as proyecto_nombre
            FROM alertas a LEFT JOIN proyectos p ON a.id_proyecto=p.id
            WHERE a.estado='Convertida'
        """).fetchall()
        if not alertas:
            st.info("No hay alertas convertidas aún.")
        for a in alertas:
            render_alerta(a, a["proyecto_nombre"] or "—")

    if is_supervisor():
        st.divider()
        st.subheader("Registrar nueva alerta manual")
        proyectos = conn.execute("SELECT id, nombre FROM proyectos WHERE activo=1").fetchall()
        proy_dict = {r["nombre"]: r["id"] for r in proyectos}
        with st.form("nueva_alerta", clear_on_submit=True):
            col1, col2 = st.columns(2)
            proy_sel = col1.selectbox("Proyecto *", list(proy_dict.keys()))
            nivel = col2.selectbox("Nivel de falla *", ["Crítico","Alto","Medio","Bajo"])
            col3, col4 = st.columns(2)
            sistema = col3.selectbox("Sistema afectado *", [
                "Inversor","Tracker / Batería","Panel solar","Estructura",
                "Comunicaciones","Eléctrico BT/AT","Otro"
            ])
            impacto = col4.number_input("Impacto generación (kW)", min_value=0.0, step=0.5)
            recurrencia = st.selectbox("Recurrencia", ["Primera vez","Baja","Media","Alta"])
            descripcion = st.text_area("Descripción del problema *", height=100)
            submitted = st.form_submit_button("Registrar alerta", use_container_width=True)
            if submitted and descripcion:
                from datetime import datetime
                nuevo_id = f"ALT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                conn2 = get_conn()
                conn2.execute("""
                    INSERT INTO alertas (id, id_proyecto, nivel_falla, sistema_afectado,
                        impacto_kw, descripcion, recurrencia, estado, fuente)
                    VALUES (?,?,?,?,?,?,?,'Sin asignar','Manual')
                """, (nuevo_id, proy_dict[proy_sel], nivel, sistema, impacto, descripcion, recurrencia))
                conn2.commit(); conn2.close()
                st.success(f"Alerta {nuevo_id} registrada correctamente.")
                st.rerun()

    conn.close()
