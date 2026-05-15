import streamlit as st
from utils.database import get_conn
from datetime import date

PRIORIDAD_COLOR = {"Crítica":"🔴","Alta":"🟠","Media":"🟡","Baja":"🟢"}
ESTADO_COLOR = {"Pendiente":"⚪","Agendado":"🔵","En ejecución":"🟢","Completado":"✅","Bloqueado":"🔴"}

def render():
    st.title("Dashboard")
    conn = get_conn()

    trabajos_pend = conn.execute(
        "SELECT COUNT(*) FROM trabajos WHERE estado IN ('Pendiente','Agendado')"
    ).fetchone()[0]
    trabajos_crit = conn.execute(
        "SELECT COUNT(*) FROM trabajos WHERE estado IN ('Pendiente','Agendado') AND prioridad='Crítica'"
    ).fetchone()[0]
    alertas_activas = conn.execute(
        "SELECT COUNT(*) FROM alertas WHERE estado='Sin asignar'"
    ).fetchone()[0]
    personal_disp = conn.execute(
        "SELECT COUNT(*) FROM personal WHERE activo=1"
    ).fetchone()[0]
    ventanas_pend = conn.execute(
        "SELECT COUNT(*) FROM ventanas_optimas WHERE estado_decision='Pendiente'"
    ).fetchone()[0]
    mat_bajo = conn.execute(
        "SELECT COUNT(*) FROM materiales WHERE (stock_bodega+stock_vehiculos) <= stock_minimo"
    ).fetchone()[0]

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Trabajos pendientes", trabajos_pend, f"{trabajos_crit} críticos" if trabajos_crit else "")
    c2.metric("Alertas sin asignar", alertas_activas)
    c3.metric("Personal activo", personal_disp)
    c4.metric("Ventanas IA pendientes", ventanas_pend)
    c5.metric("Materiales bajo stock", mat_bajo, delta=f"⚠️ Revisar" if mat_bajo > 0 else None, delta_color="inverse")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Trabajos activos")
        rows = conn.execute("""
            SELECT t.id, t.prioridad, t.estado, t.descripcion_corta, t.fecha_objetivo,
                   p.nombre as proyecto
            FROM trabajos t
            LEFT JOIN proyectos p ON t.id_proyecto=p.id
            WHERE t.estado IN ('Pendiente','Agendado','En ejecución')
            ORDER BY CASE t.prioridad WHEN 'Crítica' THEN 1 WHEN 'Alta' THEN 2 WHEN 'Media' THEN 3 ELSE 4 END
            LIMIT 8
        """).fetchall()
        for r in rows:
            icon_p = PRIORIDAD_COLOR.get(r["prioridad"],"⚪")
            icon_e = ESTADO_COLOR.get(r["estado"],"⚪")
            with st.container(border=True):
                c_a, c_b = st.columns([3,1])
                c_a.markdown(f"**{r['proyecto']}** — {r['descripcion_corta'][:60]}")
                c_b.markdown(f"{icon_p} {r['prioridad']} · {icon_e} {r['estado']}")
                if r["fecha_objetivo"]:
                    dias = (date.fromisoformat(r["fecha_objetivo"]) - date.today()).days
                    color = "red" if dias < 3 else ("orange" if dias < 7 else "green")
                    st.caption(f":{color}[Fecha objetivo: {r['fecha_objetivo']} ({dias}d)]")

    with col2:
        st.subheader("Alertas recientes")
        alertas = conn.execute("""
            SELECT a.id, a.nivel_falla, a.sistema_afectado, a.impacto_kw,
                   a.estado, a.fecha_registro, p.nombre as proyecto
            FROM alertas a
            LEFT JOIN proyectos p ON a.id_proyecto=p.id
            ORDER BY a.fecha_registro DESC LIMIT 5
        """).fetchall()
        nivel_icon = {"Crítico":"🔴","Alto":"🟠","Medio":"🟡","Bajo":"🟢"}
        for a in alertas:
            icon = nivel_icon.get(a["nivel_falla"],"⚪")
            with st.container(border=True):
                st.markdown(f"{icon} **{a['proyecto']}** — {a['sistema_afectado']}")
                st.caption(f"Impacto: {a['impacto_kw']} kW · {a['estado']} · {a['fecha_registro'][:16]}")

        if ventanas_pend > 0:
            st.divider()
            st.subheader("Ventana óptima IA")
            v = conn.execute(
                "SELECT * FROM ventanas_optimas WHERE estado_decision='Pendiente' ORDER BY score_optimizacion DESC LIMIT 1"
            ).fetchone()
            if v:
                with st.container(border=True):
                    col_s, col_d = st.columns([1, 3])
                    col_s.metric("Score", f"{v['score_optimizacion']:.0f}")
                    col_d.markdown(f"**{v['fecha_ejecucion']}**")
                    col_d.caption(f"Trabajos: {v['trabajos_incluidos']}")
                    col_d.caption(f"Costo est.: ${v['costo_total_est']:,.0f} · {v['tiempo_total_est_h']}h")
                    ca, cb = st.columns(2)
                    if ca.button("✅ Aprobar", key="dash_aprobar"):
                        conn2 = get_conn()
                        conn2.execute("UPDATE ventanas_optimas SET estado_decision='Aprobada' WHERE id=?", (v["id"],))
                        conn2.commit(); conn2.close()
                        st.success("Ventana aprobada"); st.rerun()
                    if cb.button("Ver detalle", key="dash_detalle"):
                        st.session_state.page = "optimizacion"; st.rerun()

    conn.close()
