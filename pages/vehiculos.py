import streamlit as st
from utils.database import get_conn
from utils.auth import is_admin

def render():
    st.title("🚗 Vehículos")
    conn = get_conn()
    if is_admin():
        if st.button("➕ Agregar vehículo"):
            st.session_state["show_form_veh"] = True
        if st.session_state.get("show_form_veh"):
            with st.form("form_veh", clear_on_submit=True):
                c1,c2 = st.columns(2)
                nid = c1.text_input("ID *", placeholder="VEH-04")
                patente = c2.text_input("Patente *")
                c3,c4 = st.columns(2)
                modelo = c3.text_input("Marca/Modelo")
                anio = c4.number_input("Año", 2010, 2030, 2022)
                c5,c6,c7 = st.columns(3)
                cap = c5.number_input("Capacidad personas", 1, 10, 5)
                consumo = c6.number_input("Consumo (l/100km)", 5.0, 25.0, 9.5, step=0.1)
                km_act = c7.number_input("Km actuales", 0.0, step=100.0)
                c8,c9 = st.columns(2)
                prox_mant = c8.number_input("Prox. mantención km", 0.0, step=1000.0)
                base = c9.text_input("Base habitual")
                herramientas = st.text_area("Herramientas fijas a bordo", height=60)
                id_gps = st.text_input("ID dispositivo GPS")
                if st.form_submit_button("Guardar") and nid and patente:
                    conn2 = get_conn()
                    try:
                        conn2.execute("""INSERT INTO vehiculos (id,patente,marca_modelo,anio,capacidad_personas,
                            consumo_lts_100km,km_actuales,prox_mantencion_km,base_habitual,herramientas_fijas,id_gps)
                            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                            (nid,patente,modelo,anio,cap,consumo,km_act,prox_mant,base,herramientas,id_gps))
                        conn2.commit()
                        st.success("Vehículo agregado."); st.session_state["show_form_veh"]=False; st.rerun()
                    except Exception as e: st.error(f"Error: {e}")
                    finally: conn2.close()
            if st.button("Cancelar##veh"): st.session_state["show_form_veh"]=False; st.rerun()

    vehiculos = conn.execute("SELECT * FROM vehiculos ORDER BY id").fetchall()
    for v in vehiculos:
        prox = v["prox_mantencion_km"] or 0
        km = v["km_actuales"] or 0
        alerta_km = prox > 0 and (prox - km) < 2000
        with st.container(border=True):
            c1,c2,c3,c4 = st.columns([3,2,2,2])
            c1.markdown(f"**{v['id']}** — {v['marca_modelo']} `{v['patente']}`")
            c2.markdown(f"👥 {v['capacidad_personas']} personas")
            c3.markdown(f"📏 {km:,.0f} km actuales")
            if alerta_km:
                c4.warning(f"⚠️ Mantención a {(prox-km):,.0f} km")
            else:
                c4.success(f"✅ Disponible")
            st.caption(f"Herramientas: {v['herramientas_fijas'] or '—'} · Base: {v['base_habitual'] or '—'} · GPS: {v['id_gps'] or '—'}")
    conn.close()
