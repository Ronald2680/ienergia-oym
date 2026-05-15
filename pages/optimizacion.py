import streamlit as st
from utils.database import get_conn
from utils.auth import require_role

def render():
    require_role("admin", "supervisor")
    st.title("🧠 Optimización IA")

    conn = get_conn()

    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("⚡ Generar nuevas ventanas óptimas", use_container_width=True, type="primary"):
            with st.spinner("Analizando trabajos, personal y distancias... esto puede tomar unos segundos"):
                try:
                    from utils.ai_engine import generate_ventanas_optimas
                    ventanas = generate_ventanas_optimas()
                    conn2 = get_conn()
                    from datetime import datetime
                    for v in ventanas:
                        vid = v.get("id", f"OPT-{datetime.now().strftime('%Y%m%d%H%M%S')}")
                        conn2.execute("""
                            INSERT OR REPLACE INTO ventanas_optimas
                            (id, fecha_ejecucion, trabajos_incluidos, personal_sugerido,
                             id_vehiculo, tiempo_total_est_h, costo_total_est,
                             score_optimizacion, restricciones_det, alternativa_b, estado_decision)
                            VALUES (?,?,?,?,?,?,?,?,?,?,'Pendiente')
                        """, (vid,
                              v.get("fecha_ejecucion"),
                              ", ".join(v.get("trabajos_incluidos", [])),
                              ", ".join(v.get("nombres_personal", [])),
                              v.get("id_vehiculo"),
                              v.get("tiempo_total_est_h", 0),
                              v.get("costo_total_est", 0),
                              v.get("score_optimizacion", 0),
                              v.get("restricciones_det", ""),
                              v.get("justificacion", "")))
                    conn2.commit(); conn2.close()
                    st.success(f"Se generaron {len(ventanas)} ventanas óptimas.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al generar ventanas: {e}")

    with col2:
        if st.button("📊 Análisis de cuellos de botella", use_container_width=True):
            st.session_state["show_cuellos"] = True

    if st.session_state.get("show_cuellos"):
        with st.spinner("Analizando historial de retrasos..."):
            try:
                from utils.ai_engine import chat_with_ai
                resp = chat_with_ai([{"role":"user","content":
                    "Analiza el historial de trabajos y alertas en el sistema y dime cuáles son los "
                    "principales cuellos de botella operacionales. Categoriza por tipo, frecuencia e impacto. "
                    "Incluye recomendaciones concretas para cada uno."}])
                st.info(resp)
            except Exception as e:
                st.error(f"Error: {e}")
        if st.button("Cerrar análisis"):
            st.session_state["show_cuellos"] = False

    st.divider()

    tab_pend, tab_aprobadas, tab_hist = st.tabs(["Pendientes de aprobación", "Aprobadas", "Historial"])

    def render_ventana(v):
        score = v["score_optimizacion"] or 0
        color = "🟢" if score >= 80 else ("🟡" if score >= 60 else "🔴")
        with st.container(border=True):
            col_s, col_d, col_btn = st.columns([1, 4, 1.5])
            col_s.metric("Score IA", f"{score:.0f}", help="Mayor score = mayor eficiencia operacional")
            with col_d:
                st.markdown(f"**📅 Fecha propuesta: {v['fecha_ejecucion']}**")
                st.caption(f"Trabajos: {v['trabajos_incluidos']}")
                st.caption(f"Personal: {v['personal_sugerido']}")
                c1, c2, c3 = st.columns(3)
                c1.metric("Tiempo est.", f"{v['tiempo_total_est_h']}h")
                c2.metric("Costo est.", f"${v['costo_total_est']:,.0f}" if v['costo_total_est'] else "—")
                c3.markdown(f"**Vehículo:** {v['id_vehiculo'] or '—'}")
                if v["restricciones_det"]:
                    st.warning(f"⚠️ {v['restricciones_det']}")
                if v["alternativa_b"]:
                    st.info(f"💡 Alternativa: {v['alternativa_b']}")
            with col_btn:
                if v["estado_decision"] == "Pendiente":
                    if st.button("✅ Aprobar", key=f"apr_{v['id']}"):
                        conn2 = get_conn()
                        conn2.execute("UPDATE ventanas_optimas SET estado_decision='Aprobada' WHERE id=?", (v["id"],))
                        conn2.commit(); conn2.close()
                        st.success("Aprobada"); st.rerun()
                    motivo = st.text_input("Motivo rechazo", key=f"mot_{v['id']}", placeholder="Opcional")
                    if st.button("❌ Rechazar", key=f"rec_{v['id']}"):
                        conn2 = get_conn()
                        conn2.execute("UPDATE ventanas_optimas SET estado_decision='Rechazada', motivo_rechazo=? WHERE id=?",
                                      (motivo, v["id"]))
                        conn2.commit(); conn2.close()
                        st.rerun()
                else:
                    st.markdown(f"**{v['estado_decision']}**")

    with tab_pend:
        ventanas = conn.execute(
            "SELECT * FROM ventanas_optimas WHERE estado_decision='Pendiente' ORDER BY score_optimizacion DESC"
        ).fetchall()
        if not ventanas:
            st.info("No hay ventanas pendientes. Haz clic en 'Generar nuevas ventanas óptimas' para crear propuestas.")
        for v in ventanas:
            render_ventana(v)

    with tab_aprobadas:
        ventanas = conn.execute(
            "SELECT * FROM ventanas_optimas WHERE estado_decision='Aprobada' ORDER BY fecha_ejecucion DESC"
        ).fetchall()
        if not ventanas:
            st.info("No hay ventanas aprobadas aún.")
        for v in ventanas:
            render_ventana(v)

    with tab_hist:
        ventanas = conn.execute(
            "SELECT * FROM ventanas_optimas ORDER BY fecha_propuesta DESC LIMIT 20"
        ).fetchall()
        if not ventanas:
            st.info("Sin historial aún.")
        for v in ventanas:
            render_ventana(v)

    st.divider()
    st.subheader("📈 Métricas de eficiencia")
    total_ej = conn.execute("SELECT COUNT(*) FROM ejecucion_trabajo").fetchone()[0]
    completados = conn.execute("SELECT COUNT(*) FROM ejecucion_trabajo WHERE trabajo_completado='Completado'").fetchone()[0]
    sin_prob = conn.execute("SELECT COUNT(*) FROM ejecucion_trabajo WHERE problema_principal='Sin problemas'").fetchone()[0]
    mat_retraso = conn.execute("SELECT COUNT(*) FROM trabajos WHERE retraso_materiales=1").fetchone()[0]
    maq_retraso = conn.execute("SELECT COUNT(*) FROM trabajos WHERE retraso_maquinaria=1").fetchone()[0]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Ejecuciones totales", total_ej)
    c2.metric("Completados", completados)
    c3.metric("Sin problemas", sin_prob)
    c4.metric("Retrasos por materiales", mat_retraso)
    c5.metric("Retrasos por maquinaria", maq_retraso)

    conn.close()
