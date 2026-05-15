import streamlit as st
from utils.auth import require_role

SUGERENCIAS = [
    "¿Cuáles trabajos se pueden agrupar esta semana para optimizar viajes?",
    "¿Qué materiales debo pedir urgente para no bloquear trabajos?",
    "¿Cuál es el mejor técnico para el trabajo en Falcon?",
    "Genera el checklist de preparación para la visita a Calle Larga",
    "¿Cuáles son los proyectos con mayor historial de retrasos y por qué?",
    "¿Qué pasa si el epoxy para San Vicente llega en 3 días? ¿Afecta otras ventanas?",
]

def render():
    require_role("admin", "supervisor")
    st.title("💬 Chat con IA de Optimización")
    st.caption("El asistente tiene acceso en tiempo real a todos los datos del sistema: trabajos, personal, materiales, proyectos y distancias.")

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    if not st.session_state.chat_messages:
        st.markdown("**Preguntas sugeridas:**")
        cols = st.columns(3)
        for i, sug in enumerate(SUGERENCIAS):
            if cols[i % 3].button(sug, key=f"sug_{i}", use_container_width=True):
                st.session_state.chat_messages.append({"role": "user", "content": sug})
                st.rerun()

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Pregunta al sistema de optimización..."):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analizando datos del sistema..."):
                try:
                    from utils.ai_engine import chat_with_ai
                    include_ctx = len(st.session_state.chat_messages) <= 2
                    response = chat_with_ai(
                        st.session_state.chat_messages,
                        include_context=include_ctx
                    )
                    st.markdown(response)
                    st.session_state.chat_messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    err = f"Error al conectar con la IA: {e}"
                    st.error(err)
                    st.session_state.chat_messages.append({"role": "assistant", "content": err})

    if st.session_state.chat_messages:
        if st.button("🗑 Limpiar conversación"):
            st.session_state.chat_messages = []
            st.rerun()
