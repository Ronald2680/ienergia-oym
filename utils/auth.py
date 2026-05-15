import streamlit as st
import hashlib
from utils.database import get_conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def login(username: str, password: str):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM usuarios WHERE username=? AND activo=1", (username,)
    ).fetchone()
    conn.close()
    if row and row["password_hash"] == hash_password(password):
        return dict(row)
    return None

def require_login():
    if "user" not in st.session_state or st.session_state.user is None:
        show_login()
        st.stop()

def require_role(*roles):
    require_login()
    if st.session_state.user["rol"] not in roles:
        st.error("No tienes permisos para acceder a esta sección.")
        st.stop()

def show_login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div style='text-align:center;padding:2rem 0 1rem'>
            <div style='width:64px;height:64px;background:#1a6b3a;border-radius:16px;
                        display:inline-flex;align-items:center;justify-content:center;
                        font-size:24px;font-weight:700;color:white'>iE</div>
            <h2 style='margin:.5rem 0 .2rem;font-weight:600'>iEnergia OyM</h2>
            <p style='color:gray;font-size:.9rem;margin:0'>Plataforma de Optimización Operacional</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Usuario", placeholder="Usuario")
            password = st.text_input("Contraseña", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Ingresar", use_container_width=True)

        if submitted:
            user = login(username, password)
            if user:
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")

        st.markdown("""
        <p style='text-align:center;color:#aaa;font-size:.75rem;margin-top:2rem'>
            v2.0 — Sistema Gestión OyM · iEnergia
        </p>""", unsafe_allow_html=True)

def logout():
    st.session_state.user = None
    st.rerun()

def is_admin():
    return st.session_state.get("user", {}).get("rol") == "admin"

def is_supervisor():
    return st.session_state.get("user", {}).get("rol") in ("admin", "supervisor")
