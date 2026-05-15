import streamlit as st
from utils.database import get_conn
from utils.auth import is_admin

def render():
    st.title("📦 Materiales")
    conn = get_conn()

    mat_bajo = conn.execute(
        "SELECT COUNT(*) FROM materiales WHERE (stock_bodega+stock_vehiculos) <= stock_minimo"
    ).fetchone()[0]
    if mat_bajo > 0:
        st.error(f"⚠️ {mat_bajo} material(es) por debajo del stock mínimo. Revisar y solicitar reposición.")

    if is_admin():
        if st.button("➕ Agregar material"):
            st.session_state["show_form_mat"] = True
        if st.session_state.get("show_form_mat"):
            with st.form("form_mat", clear_on_submit=True):
                c1,c2 = st.columns(2)
                nid = c1.text_input("ID *", placeholder="MAT-008")
                nombre = c2.text_input("Nombre *")
                c3,c4 = st.columns(2)
                codigo = c3.text_input("Código interno *")
                unidad = c4.selectbox("Unidad", ["unidad","metro","kg","litro","caja"])
                c5,c6,c7 = st.columns(3)
                stock_b = c5.number_input("Stock bodega", 0.0, step=1.0)
                stock_v = c6.number_input("Stock vehículos", 0.0, step=1.0)
                stock_min = c7.number_input("Stock mínimo", 0.0, step=1.0, value=5.0)
                c8,c9,c10 = st.columns(3)
                lead = c8.number_input("Lead time (días)", 0, 30, 5)
                precio = c9.number_input("Precio unitario (CLP)", 0.0, step=100.0)
                proveedor = c10.text_input("Proveedor")
                if st.form_submit_button("Guardar") and nombre and nid and codigo:
                    conn2 = get_conn()
                    try:
                        conn2.execute("""INSERT INTO materiales (id,nombre,codigo_interno,unidad,
                            stock_bodega,stock_vehiculos,stock_minimo,lead_time_dias,proveedor,precio_unitario)
                            VALUES (?,?,?,?,?,?,?,?,?,?)""",
                            (nid,nombre,codigo,unidad,stock_b,stock_v,stock_min,lead,proveedor,precio))
                        conn2.commit()
                        st.success("Material agregado."); st.session_state["show_form_mat"]=False; st.rerun()
                    except Exception as e: st.error(f"Error: {e}")
                    finally: conn2.close()
            if st.button("Cancelar##mat"): st.session_state["show_form_mat"]=False; st.rerun()

    materiales = conn.execute("SELECT * FROM materiales ORDER BY nombre").fetchall()
    for m in materiales:
        stock_total = (m["stock_bodega"] or 0) + (m["stock_vehiculos"] or 0)
        alerta = stock_total <= (m["stock_minimo"] or 0)
        with st.container(border=True):
            c1,c2,c3,c4,c5 = st.columns([3,1,1,1,2])
            c1.markdown(f"**{m['nombre']}** `{m['codigo_interno']}`")
            c2.markdown(f"Bodega: **{m['stock_bodega']} {m['unidad']}**")
            c3.markdown(f"Veh.: **{m['stock_vehiculos']} {m['unidad']}**")
            c4.markdown(f"Mín.: {m['stock_minimo']} {m['unidad']}")
            if alerta:
                c5.error(f"⚠️ BAJO STOCK — Lead time: {m['lead_time_dias']}d")
            else:
                c5.success("✅ Stock OK")
            if is_admin():
                with st.expander("Actualizar stock"):
                    with st.form(f"upd_mat_{m['id']}", clear_on_submit=True):
                        na,nb = st.columns(2)
                        ns_b = na.number_input("Nuevo stock bodega", value=float(m["stock_bodega"] or 0), step=1.0, key=f"sb_{m['id']}")
                        ns_v = nb.number_input("Nuevo stock vehículos", value=float(m["stock_vehiculos"] or 0), step=1.0, key=f"sv_{m['id']}")
                        if st.form_submit_button("Actualizar"):
                            from datetime import datetime
                            conn2 = get_conn()
                            conn2.execute("UPDATE materiales SET stock_bodega=?,stock_vehiculos=?,ultima_actualizacion=? WHERE id=?",
                                (ns_b,ns_v,datetime.now().isoformat(),m["id"]))
                            conn2.commit(); conn2.close(); st.rerun()
    conn.close()
