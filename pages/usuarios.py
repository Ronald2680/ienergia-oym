import streamlit as st
from utils.database import get_conn, hash_password
from utils.auth import require_role

ROLES = {"admin": "Administrador", "supervisor": "Supervisor", "tecnico": "Técnico"}
PERMISOS = {
    "admin":      "Dashboard · Alertas · Trabajos · Optimización IA · Chat IA · Datos maestros · Fuentes · Usuarios",
    "supervisor": "Dashboard · Alertas · Trabajos · Optimización IA · Chat IA · Datos maestros (lectura)",
    "tecnico":    "Solo checklist de tareas asignadas",
}

def render():
    require_role("admin")
    st.title("🔐 Gestión de usuarios")
    conn = get_conn()

    usuarios = conn.execute("""
        SELECT u.*, p.nombre as nombre_personal
        FROM usuarios u
        LEFT JOIN personal p ON u.id_personal=p.id
        ORDER BY u.rol, u.nombre
    """).fetchall()

    st.subheader("Usuarios del sistema")
    for u in usuarios:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([3, 2, 3, 1])
            initials = "".join(n[0] for n in u["nombre"].split()[:2]).upper()
            c1.markdown(f"**{u['nombre']}** `{u['username']}`")
            c1.caption(u.get("email") or "—")
            c2.markdown(f"**Rol:** {ROLES.get(u['rol'], u['rol'])}")
            c3.caption(PERMISOS.get(u["rol"], "—"))
            estado = "✅ Activo" if u["activo"] else "❌ Inactivo"
            c4.markdown(estado)

            if u["username"] != "Admin":
                with st.expander(f"Editar {u['nombre']}"):
                    with st.form(f"edit_user_{u['id']}", clear_on_submit=False):
                        nc1, nc2 = st.columns(2)
                        nuevo_rol = nc1.selectbox("Rol", list(ROLES.keys()),
                            index=list(ROLES.keys()).index(u["rol"]),
                            key=f"rol_{u['id']}")
                        activo = nc2.checkbox("Activo", value=bool(u["activo"]), key=f"act_{u['id']}")
                        nueva_pass = st.text_input("Nueva contraseña (dejar vacío para no cambiar)",
                            type="password", key=f"pass_{u['id']}")
                        if st.form_submit_button("Guardar cambios"):
                            conn2 = get_conn()
                            if nueva_pass:
                                conn2.execute("UPDATE usuarios SET rol=?, activo=?, password_hash=? WHERE id=?",
                                    (nuevo_rol, int(activo), hash_password(nueva_pass), u["id"]))
                            else:
                                conn2.execute("UPDATE usuarios SET rol=?, activo=? WHERE id=?",
                                    (nuevo_rol, int(activo), u["id"]))
                            conn2.commit(); conn2.close()
                            st.success("Usuario actualizado."); st.rerun()

    st.divider()
    st.subheader("Crear nuevo usuario")
    personal_sin_user = conn.execute("""
        SELECT p.id, p.nombre FROM personal p
        WHERE NOT EXISTS (SELECT 1 FROM usuarios u WHERE u.id_personal=p.id)
        AND p.activo=1
    """).fetchall()

    with st.form("nuevo_usuario", clear_on_submit=True):
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombre completo *")
        username = c2.text_input("Usuario (login) *")
        c3, c4 = st.columns(2)
        email = c3.text_input("Email")
        password = c4.text_input("Contraseña *", type="password")
        c5, c6 = st.columns(2)
        rol = c5.selectbox("Rol *", list(ROLES.keys()), format_func=lambda x: ROLES[x])
        personal_opts = {"—": None}
        personal_opts.update({p["nombre"]: p["id"] for p in personal_sin_user})
        personal_sel = c6.selectbox("Vincular con personal (técnicos)", list(personal_opts.keys()))

        submitted = st.form_submit_button("Crear usuario", use_container_width=True)
        if submitted:
            if not nombre or not username or not password:
                st.error("Nombre, usuario y contraseña son obligatorios.")
            else:
                conn2 = get_conn()
                try:
                    conn2.execute("""INSERT INTO usuarios (username, nombre, email, password_hash, rol, id_personal)
                        VALUES (?,?,?,?,?,?)""",
                        (username, nombre, email, hash_password(password), rol,
                         personal_opts[personal_sel]))
                    conn2.commit()
                    st.success(f"Usuario '{username}' creado con rol '{ROLES[rol]}'.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error (¿usuario ya existe?): {e}")
                finally:
                    conn2.close()

    st.divider()
    st.subheader("Matriz de permisos por rol")
    permisos_tabla = {
        "Módulo": ["Dashboard","Alertas","Trabajos","Optimización IA","Chat IA","Personal","Proyectos","Materiales","Vehículos","Tipos trabajo","Fuentes de datos","Usuarios"],
        "Administrador": ["✅ Completo","✅ Completo","✅ Completo","✅ Completo","✅ Completo","✅ Edición","✅ Edición","✅ Edición","✅ Edición","✅ Edición","✅ Completo","✅ Completo"],
        "Supervisor":    ["✅ Completo","✅ Lectura","✅ Aprobación","✅ Aprobación","✅ Completo","✅ Lectura","✅ Lectura","✅ Lectura","✅ Lectura","✅ Lectura","❌ Sin acceso","❌ Sin acceso"],
        "Técnico":       ["❌ Sin acceso","Solo asignadas","Solo checklist","❌ Sin acceso","❌ Sin acceso","❌ Sin acceso","❌ Sin acceso","❌ Sin acceso","❌ Sin acceso","❌ Sin acceso","❌ Sin acceso","❌ Sin acceso"],
    }
    import pandas as pd
    st.dataframe(pd.DataFrame(permisos_tabla).set_index("Módulo"), use_container_width=True)
    conn.close()
