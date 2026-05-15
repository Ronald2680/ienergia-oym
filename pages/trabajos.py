import streamlit as st
from utils.database import get_conn
from utils.auth import is_supervisor, is_admin
from datetime import datetime, date

PRIORIDAD_OPTS = ["Crítica","Alta","Media","Baja"]
ESTADO_OPTS = ["Pendiente","Agendado","En ejecución","Completado","Bloqueado"]
PROBLEMA_OPTS = ["Sin problemas","Material faltante","Espera grúa/maquinaria","Clima adverso","Error diagnóstico","Coordinación cliente","Permiso no disponible","Falta personal","Otro"]

def render():
    conn = get_conn()
    rol = st.session_state.user["rol"]

    if rol == "tecnico":
        _render_tecnico(conn)
    else:
        _render_supervisor(conn)
    conn.close()

def _render_tecnico(conn):
    st.title("🔧 Mis tareas asignadas")
    usuario = st.session_state.user
    id_personal = usuario.get("id_personal")

    trabajos = conn.execute("""
        SELECT t.*, p.nombre as proyecto_nombre, tt.nombre_tipo
        FROM trabajos t
        LEFT JOIN proyectos p ON t.id_proyecto=p.id
        LEFT JOIN tipos_trabajo tt ON t.id_tipo_trabajo=tt.id
        WHERE t.estado IN ('Agendado','En ejecución')
        ORDER BY CASE t.prioridad WHEN 'Crítica' THEN 1 WHEN 'Alta' THEN 2 WHEN 'Media' THEN 3 ELSE 4 END
    """).fetchall()

    if not trabajos:
        st.info("No tienes trabajos asignados actualmente.")
        return

    for t in trabajos:
        with st.expander(f"🔧 {t['proyecto_nombre']} — {t['nombre_tipo']} [{t['prioridad']}]", expanded=True):
            st.caption(t["descripcion_corta"])
            st.markdown("**Checklist de ejecución:**")

            exec_row = conn.execute(
                "SELECT * FROM ejecucion_trabajo WHERE id_trabajo=? ORDER BY rowid DESC LIMIT 1",
                (t["id"],)
            ).fetchone()

            with st.form(f"checklist_{t['id']}", clear_on_submit=False):
                completado = st.selectbox("Estado del trabajo *",
                    ["Pendiente","Completado","Parcial","No ejecutado"],
                    index=0 if not exec_row else ["Pendiente","Completado","Parcial","No ejecutado"].index(
                        exec_row["trabajo_completado"] if exec_row and exec_row["trabajo_completado"] else "Pendiente"
                    ))
                problema = st.selectbox("Problema principal *", PROBLEMA_OPTS,
                    index=0 if not exec_row else PROBLEMA_OPTS.index(
                        exec_row["problema_principal"] if exec_row and exec_row["problema_principal"] in PROBLEMA_OPTS else "Sin problemas"
                    ))
                obs = st.text_area("Observación (opcional)", value=exec_row["observacion"] if exec_row else "")
                col1, col2 = st.columns(2)
                hora_inicio = col1.time_input("Hora inicio tarea", value=None)
                hora_fin = col2.time_input("Hora fin tarea", value=None)

                if st.form_submit_button("💾 Guardar checklist", use_container_width=True):
                    exec_id = f"EJEC-{t['id']}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    conn2 = get_conn()
                    conn2.execute("""
                        INSERT OR REPLACE INTO ejecucion_trabajo
                        (id, id_trabajo, fecha_ejecucion, trabajo_completado, problema_principal,
                         observacion, hora_inicio_tarea, hora_fin_tarea)
                        VALUES (?,?,?,?,?,?,?,?)
                    """, (exec_id, t["id"], date.today().isoformat(), completado, problema, obs,
                          str(hora_inicio) if hora_inicio else None,
                          str(hora_fin) if hora_fin else None))
                    if completado == "Completado":
                        conn2.execute("UPDATE trabajos SET estado='Completado', resultado='Completado' WHERE id=?", (t["id"],))
                    elif completado == "Parcial":
                        conn2.execute("UPDATE trabajos SET estado='En ejecución' WHERE id=?", (t["id"],))
                    conn2.commit(); conn2.close()
                    st.success("Checklist guardado correctamente ✓")
                    st.rerun()

def _render_supervisor(conn):
    st.title("🔧 Gestión de trabajos")

    col_filtros, col_btn = st.columns([3, 1])
    with col_filtros:
        filtro_estado = st.multiselect("Filtrar por estado", ESTADO_OPTS, default=["Pendiente","Agendado","En ejecución"])
    with col_btn:
        st.markdown("<div style='margin-top:28px'>", unsafe_allow_html=True)
        if st.button("➕ Nuevo trabajo", use_container_width=True):
            st.session_state["show_nuevo_trabajo"] = True
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.get("show_nuevo_trabajo"):
        _form_nuevo_trabajo(conn)

    estado_in = "','".join(filtro_estado) if filtro_estado else "'Pendiente'"
    trabajos = conn.execute(f"""
        SELECT t.*, p.nombre as proyecto_nombre, tt.nombre_tipo
        FROM trabajos t
        LEFT JOIN proyectos p ON t.id_proyecto=p.id
        LEFT JOIN tipos_trabajo tt ON t.id_tipo_trabajo=tt.id
        WHERE t.estado IN ('{estado_in}')
        ORDER BY CASE t.prioridad WHEN 'Crítica' THEN 1 WHEN 'Alta' THEN 2 WHEN 'Media' THEN 3 ELSE 4 END,
                 t.fecha_registro DESC
    """).fetchall()

    if not trabajos:
        st.info("No hay trabajos con los filtros seleccionados.")
        return

    for t in trabajos:
        _render_trabajo_card(t, conn)

def _render_trabajo_card(t, conn):
    icons = {"Crítica":"🔴","Alta":"🟠","Media":"🟡","Baja":"🟢"}
    icon = icons.get(t["prioridad"],"⚪")
    label = f"{icon} **{t['id']}** · {t['proyecto_nombre']} — {t['nombre_tipo']} `{t['estado']}`"
    with st.expander(label):
        col1, col2, col3 = st.columns(3)
        col1.markdown(f"**Prioridad:** {t['prioridad']}")
        col2.markdown(f"**Estado:** {t['estado']}")
        col3.markdown(f"**Fecha objetivo:** {t['fecha_objetivo'] or '—'}")
        st.write(f"**Descripción:** {t['descripcion_corta']}")
        col4, col5, col6 = st.columns(3)
        col4.markdown(f"**Material req.:** {'⚠️ Sí' if t['requiere_material'] else '—'} {'✅ Listo' if t['materiales_listos'] else ('❌ Falta' if t['requiere_material'] else '')}")
        col5.markdown(f"**Maquinaria:** {'Sí' if t['requiere_maquinaria'] else 'No'}")
        col6.markdown(f"**PTS:** {t['pts_asociado'] or '—'}")

        retrasos = []
        if t["retraso_materiales"]: retrasos.append("Materiales")
        if t["retraso_maquinaria"]: retrasos.append("Maquinaria")
        if t["retraso_clima"]: retrasos.append("Clima")
        if t["retraso_cliente"]: retrasos.append("Cliente")
        if t["retraso_permiso"]: retrasos.append("Permiso")
        if retrasos:
            st.warning(f"Retrasos registrados: {', '.join(retrasos)} — Impacto: {t['impacto_retraso']}")

        btn1, btn2, btn3 = st.columns(3)
        if is_supervisor():
            nuevo_estado = btn1.selectbox("Cambiar estado", ESTADO_OPTS,
                index=ESTADO_OPTS.index(t["estado"]), key=f"estado_{t['id']}")
            if btn1.button("Actualizar", key=f"upd_{t['id']}"):
                conn2 = get_conn()
                conn2.execute("UPDATE trabajos SET estado=? WHERE id=?", (nuevo_estado, t["id"]))
                conn2.commit(); conn2.close()
                st.rerun()

def _form_nuevo_trabajo(conn):
    st.divider()
    st.subheader("Nuevo trabajo")
    proyectos = conn.execute("SELECT id, nombre FROM proyectos WHERE activo=1").fetchall()
    tipos = conn.execute("SELECT id, nombre_tipo FROM tipos_trabajo").fetchall()
    proy_dict = {r["nombre"]: r["id"] for r in proyectos}
    tipo_dict = {r["nombre_tipo"]: r["id"] for r in tipos}

    with st.form("form_nuevo_trabajo", clear_on_submit=True):
        col1, col2 = st.columns(2)
        proy_sel = col1.selectbox("Proyecto *", list(proy_dict.keys()))
        tipo_sel = col2.selectbox("Tipo de trabajo *", list(tipo_dict.keys()))
        col3, col4 = st.columns(2)
        prioridad = col3.selectbox("Prioridad *", PRIORIDAD_OPTS)
        fecha_obj = col4.date_input("Fecha objetivo")
        descripcion = st.text_input("Descripción corta *")
        col5, col6, col7 = st.columns(3)
        req_mat = col5.checkbox("¿Requiere material?")
        req_maq = col6.checkbox("¿Requiere maquinaria?")
        pts = col7.text_input("PTS asociado")

        submitted = st.form_submit_button("Guardar trabajo", use_container_width=True)
        if submitted and descripcion:
            import datetime as dt
            nuevo_id = f"TRB-{dt.datetime.now().strftime('%Y%m%d%H%M%S')}"
            conn2 = get_conn()
            conn2.execute("""
                INSERT INTO trabajos (id, id_proyecto, id_tipo_trabajo, prioridad,
                    descripcion_corta, pts_asociado, requiere_material, requiere_maquinaria,
                    estado, fecha_objetivo)
                VALUES (?,?,?,?,?,?,?,?,'Pendiente',?)
            """, (nuevo_id, proy_dict[proy_sel], tipo_dict[tipo_sel], prioridad,
                  descripcion, pts, int(req_mat), int(req_maq),
                  fecha_obj.isoformat() if fecha_obj else None))
            conn2.commit(); conn2.close()
            st.session_state["show_nuevo_trabajo"] = False
            st.success(f"Trabajo {nuevo_id} creado correctamente.")
            st.rerun()

    if st.button("Cancelar"):
        st.session_state["show_nuevo_trabajo"] = False
        st.rerun()
