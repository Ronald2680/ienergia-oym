import anthropic
import json
import streamlit as st
from utils.database import get_conn, query, execute

def get_client():
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY no configurada en secrets.")
    return anthropic.Anthropic(api_key=api_key)

def _build_context() -> dict:
    conn = get_conn()
    trabajos_pend = [dict(r) for r in conn.execute("""
        SELECT t.id, t.prioridad, t.descripcion_corta, t.estado, t.fecha_objetivo,
               t.requiere_material, t.materiales_listos, t.requiere_maquinaria,
               p.nombre as proyecto, p.region, p.latitud, p.longitud,
               p.hora_apertura, p.hora_cierre, p.requiere_permiso, p.lead_time_permiso_d,
               tt.nombre_tipo, tt.duracion_est_h, tt.desv_estandar_h,
               tt.especialidad_req, tt.certificacion_req, tt.personal_minimo,
               tt.herramientas_base, tt.requiere_maquinaria as tipo_req_maq
        FROM trabajos t
        LEFT JOIN proyectos p ON t.id_proyecto = p.id
        LEFT JOIN tipos_trabajo tt ON t.id_tipo_trabajo = tt.id
        WHERE t.estado IN ('Pendiente','Agendado')
        ORDER BY CASE t.prioridad WHEN 'Crítica' THEN 1 WHEN 'Alta' THEN 2 WHEN 'Media' THEN 3 ELSE 4 END
    """).fetchall()]

    personal = [dict(r) for r in conn.execute("""
        SELECT id, nombre, especialidad, certificaciones, region,
               domicilio_lat, domicilio_lng, id_vehiculo, puede_liderar, jornada_max_h
        FROM personal WHERE activo=1
    """).fetchall()]

    vehiculos = [dict(r) for r in conn.execute("""
        SELECT id, marca_modelo, capacidad_personas, consumo_lts_100km,
               herramientas_fijas, km_actuales, prox_mantencion_km, disponible
        FROM vehiculos WHERE disponible=1
    """).fetchall()]

    materiales_bajos = [dict(r) for r in conn.execute("""
        SELECT id, nombre, stock_bodega, stock_vehiculos, stock_minimo, lead_time_dias
        FROM materiales
        WHERE (stock_bodega + stock_vehiculos) <= stock_minimo
    """).fetchall()]

    distancias = [dict(r) for r in conn.execute("""
        SELECT dp.*, pa.nombre as proyecto_a_nombre, pb.nombre as proyecto_b_nombre
        FROM distancias_proyectos dp
        LEFT JOIN proyectos pa ON dp.id_proyecto_a = pa.id
        LEFT JOIN proyectos pb ON dp.id_proyecto_b = pb.id
    """).fetchall()]

    conn.close()
    return {
        "trabajos_pendientes": trabajos_pend,
        "personal_disponible": personal,
        "vehiculos_disponibles": vehiculos,
        "materiales_bajo_stock": materiales_bajos,
        "distancias_proyectos": distancias,
        "fecha_hoy": __import__('datetime').date.today().isoformat(),
    }

SYSTEM_PROMPT = """Eres el motor de optimización operacional de iEnergia OyM, experto en planificación de mantenimiento fotovoltaico.

Tu objetivo es analizar trabajos pendientes y generar recomendaciones óptimas de agendamiento considerando:
- Minimizar tiempo de viaje agrupando proyectos cercanos (< 60 min entre ellos)
- Verificar disponibilidad de materiales antes de proponer una fecha
- Asegurar que el personal tenga las especialidades y certificaciones correctas
- Respetar horarios de proyectos y lead times de permisos
- Calcular costos estimados (combustible + peajes + horas-persona)
- Identificar cuellos de botella (materiales faltantes, maquinaria, clima)

Responde SIEMPRE en español. Cuando generes ventanas óptimas, usa formato JSON estructurado.
Para análisis y consultas, responde en markdown claro y conciso."""

def chat_with_ai(messages: list, include_context: bool = True) -> str:
    client = get_client()
    system = SYSTEM_PROMPT
    if include_context:
        ctx = _build_context()
        system += f"\n\n## Contexto actual del sistema:\n```json\n{json.dumps(ctx, ensure_ascii=False, default=str, indent=2)}\n```"

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        system=system,
        messages=messages
    )
    return response.content[0].text

def generate_ventanas_optimas() -> list:
    client = get_client()
    ctx = _build_context()
    prompt = f"""Analiza los trabajos pendientes y genera ventanas de tiempo óptimas para las próximas 2 semanas.

Contexto del sistema:
{json.dumps(ctx, ensure_ascii=False, default=str, indent=2)}

Genera entre 2 y 4 propuestas de ventanas. Responde ÚNICAMENTE con JSON válido, sin texto adicional, con esta estructura exacta:
{{
  "ventanas": [
    {{
      "id": "OPT-001",
      "fecha_ejecucion": "YYYY-MM-DD",
      "trabajos_incluidos": ["TRB-XXXX", "TRB-YYYY"],
      "nombres_trabajos": ["Nombre trabajo 1", "Nombre trabajo 2"],
      "proyectos": ["Proyecto A", "Proyecto B"],
      "personal_sugerido": ["PERS-001", "PERS-002"],
      "nombres_personal": ["Juan Pérez", "Carlos Méndez"],
      "id_vehiculo": "VEH-01",
      "vehiculo_nombre": "Toyota Hilux 4x4",
      "tiempo_total_est_h": 9.5,
      "costo_total_est": 185000,
      "score_optimizacion": 87.4,
      "restricciones_det": "Descripción de restricciones o vacío",
      "justificacion": "Por qué esta agrupación es óptima",
      "materiales_ok": true,
      "maquinaria_requerida": false
    }}
  ]
}}"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    data = json.loads(text)
    return data.get("ventanas", [])

def analyze_alerta(alerta: dict, proyecto: dict) -> str:
    ctx = _build_context()
    prompt = f"""Se registró una nueva alerta en el sistema:

Alerta: {json.dumps(alerta, ensure_ascii=False, default=str)}
Proyecto: {json.dumps(proyecto, ensure_ascii=False, default=str)}
Personal disponible: {json.dumps(ctx['personal_disponible'], ensure_ascii=False, default=str)}
Materiales bajo stock: {json.dumps(ctx['materiales_bajos'], ensure_ascii=False, default=str) if ctx.get('materiales_bajos') else 'Ninguno'}

Analiza y responde:
1. ¿Qué tipo de trabajo correctivo corresponde?
2. ¿Es urgente o puede esperar? ¿Por qué?
3. ¿Qué personal y especialidades se requieren?
4. ¿Hay materiales disponibles o hay que pedirlos?
5. ¿Se puede combinar con algún trabajo pendiente cercano?
6. Recomendación de fecha estimada."""

    return chat_with_ai([{"role": "user", "content": prompt}], include_context=False)
