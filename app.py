import streamlit as st
from utils.database import init_db
from utils.auth import require_login, show_login, logout, is_admin, is_supervisor

st.set_page_config(
    page_title="iEnergia OyM",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stSidebar"] { min-width: 230px; max-width: 230px; }
[data-testid="stSidebar"] .block-container { padding: 0; }
.stButton > button {
    border-radius: 8px;
    font-weight: 500;
}
div[data-testid="metric-container"] {
    background: #f8f9fa;
    border-radius: 10px;
    padding: .75rem 1rem;
    border: 0.5px solid #e0e0e0;
}
.priority-critica { color: #c62828; font-weight: 600; }
.priority-alta    { color: #e65100; font-weight: 600; }
.priority-media   { color: #1565c0; font-weight: 600; }
.priority-baja    { color: #555;    font-weight: 600; }
</style>
""", unsafe_allow_html=True)

init_db()

if "user" not in st.session_state:
    st.session_state.user = None
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "page" not in st.session_state:
    st.session_state.page = "dashboard"

if st.session_state.user is None:
    show_login()
    st.stop()

user = st.session_state.user
rol = user["rol"]

with st.sidebar:
    st.markdown(f"""
    <div style='padding:16px 16px 12px;border-bottom:0.5px solid #e0e0e0;margin-bottom:8px'>
        <div style='display:flex;align-items:center;gap:10px'>
            <div style='width:38px;height:38px;background:#1a6b3a;border-radius:10px;
                        display:flex;align-items:center;justify-content:center;
                        color:white;font-weight:700;font-size:15px;flex-shrink:0'>iE</div>
            <div>
                <div style='font-weight:600;font-size:14px'>iEnergia OyM</div>
                <div style='font-size:11px;color:gray'>Gestión Operacional</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Principal**")
    if st.button("🏠 Dashboard", use_container_width=True,
                 disabled=(rol == "tecnico")):
        st.session_state.page = "dashboard"
    if st.button("🔔 Alertas / Tareas", use_container_width=True):
        st.session_state.page = "alertas"
    if st.button("🔧 Trabajos", use_container_width=True):
        st.session_state.page = "trabajos"
    if is_supervisor():
        if st.button("🧠 Optimización IA", use_container_width=True):
            st.session_state.page = "optimizacion"
        if st.button("💬 Chat IA", use_container_width=True):
            st.session_state.page = "chat"

    if is_supervisor():
        st.markdown("**Datos maestros**")
        if st.button("👥 Personal", use_container_width=True):
            st.session_state.page = "personal"
        if st.button("📍 Proyectos", use_container_width=True):
            st.session_state.page = "proyectos"
        if st.button("📦 Materiales", use_container_width=True):
            st.session_state.page = "materiales"
        if st.button("🚗 Vehículos", use_container_width=True):
            st.session_state.page = "vehiculos"
        if st.button("⚙️ Tipos de trabajo", use_container_width=True):
            st.session_state.page = "tipos_trabajo"

    if is_admin():
        st.markdown("**Sistema**")
        if st.button("🔌 Fuentes de datos", use_container_width=True):
            st.session_state.page = "fuentes"
        if st.button("🔐 Usuarios", use_container_width=True):
            st.session_state.page = "usuarios"

    st.markdown("---")
    roles_label = {"admin": "Administrador", "supervisor": "Supervisor", "tecnico": "Técnico"}
    st.markdown(f"""
    <div style='font-size:12px;color:gray;padding:0 4px'>
        <b style='color:#333'>{user['nombre']}</b><br>
        {roles_label.get(rol,'')}<br>
        <span style='font-size:11px'>{user.get('email','')}</span>
    </div>
    """, unsafe_allow_html=True)
    if st.button("⬅ Cerrar sesión", use_container_width=True):
        logout()

page = st.session_state.page

if page == "dashboard":
    from pages.dashboard import render
    render()
elif page == "alertas":
    from pages.alertas import render
    render()
elif page == "trabajos":
    from pages.trabajos import render
    render()
elif page == "optimizacion":
    from pages.optimizacion import render
    render()
elif page == "chat":
    from pages.chat import render
    render()
elif page == "personal":
    from pages.personal import render
    render()
elif page == "proyectos":
    from pages.proyectos import render
    render()
elif page == "materiales":
    from pages.materiales import render
    render()
elif page == "vehiculos":
    from pages.vehiculos import render
    render()
elif page == "tipos_trabajo":
    from pages.tipos_trabajo import render
    render()
elif page == "fuentes":
    from pages.fuentes import render
    render()
elif page == "usuarios":
    from pages.usuarios import render
    render()
