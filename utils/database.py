import os, sqlite3, hashlib, streamlit as st

DB_PATH = os.environ.get("DB_PATH", "data/ienergia_oym.db")

def _use_supabase():
    try:
        return bool(st.secrets.get("SUPABASE_URL") and st.secrets.get("SUPABASE_KEY"))
    except Exception:
        return False

def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()

@st.cache_resource
def _sb():
    from supabase import create_client
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def _sqlite():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    return c

def get_conn(): return _sqlite()

def db_select(table, filters=None, order=None, limit=None):
    if _use_supabase():
        q = _sb().table(table).select("*")
        if filters:
            for k,v in filters.items(): q = q.eq(k,v)
        if order: q = q.order(order)
        if limit: q = q.limit(limit)
        return q.execute().data or []
    c = _sqlite()
    sql = f"SELECT * FROM {table}"
    params = []
    if filters:
        sql += " WHERE " + " AND ".join(f"{k}=?" for k in filters)
        params = list(filters.values())
    if order: sql += f" ORDER BY {order}"
    if limit: sql += f" LIMIT {limit}"
    rows = c.execute(sql, params).fetchall()
    c.close()
    return [dict(r) for r in rows]

def db_select_sql(sql, params=()):
    c = _sqlite(); rows = c.execute(sql, params).fetchall(); c.close()
    return [dict(r) for r in rows]

def db_insert(table, data):
    if _use_supabase():
        r = _sb().table(table).upsert(data).execute()
        return r.data[0] if r.data else {}
    c = _sqlite()
    cols = ",".join(data.keys()); phs = ",".join("?"*len(data))
    c.execute(f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({phs})", list(data.values()))
    c.commit(); c.close(); return data

def db_update(table, data, filters):
    if _use_supabase():
        q = _sb().table(table).update(data)
        for k,v in filters.items(): q = q.eq(k,v)
        q.execute(); return
    c = _sqlite()
    set_ = ",".join(f"{k}=?" for k in data)
    wh = " AND ".join(f"{k}=?" for k in filters)
    c.execute(f"UPDATE {table} SET {set_} WHERE {wh}", list(data.values())+list(filters.values()))
    c.commit(); c.close()

def db_exists(table, col, val):
    return len(db_select(table, {col: val}, limit=1)) > 0

def db_count(table, filters=None):
    return len(db_select(table, filters))

TABLES = [
    "CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, nombre TEXT NOT NULL, email TEXT, password_hash TEXT NOT NULL, rol TEXT NOT NULL, id_personal TEXT, activo INTEGER DEFAULT 1, created_at TEXT DEFAULT (datetime('now')))",
    "CREATE TABLE IF NOT EXISTS proyectos (id TEXT PRIMARY KEY, nombre TEXT NOT NULL, cliente TEXT, latitud REAL, longitud REAL, region TEXT, criticidad TEXT, hora_apertura TEXT DEFAULT '07:00', hora_cierre TEXT DEFAULT '18:00', requiere_permiso INTEGER DEFAULT 0, lead_time_permiso_d INTEGER DEFAULT 0, contacto_cliente TEXT, tipo_acceso TEXT, restricciones TEXT, activo INTEGER DEFAULT 1)",
    "CREATE TABLE IF NOT EXISTS personal (id TEXT PRIMARY KEY, nombre TEXT NOT NULL, especialidad TEXT, certificaciones TEXT, fecha_venc_cert TEXT, region TEXT, domicilio_lat REAL, domicilio_lng REAL, id_vehiculo TEXT, puede_liderar INTEGER DEFAULT 0, jornada_max_h INTEGER DEFAULT 10, activo INTEGER DEFAULT 1)",
    "CREATE TABLE IF NOT EXISTS vehiculos (id TEXT PRIMARY KEY, patente TEXT UNIQUE, marca_modelo TEXT, anio INTEGER, capacidad_personas INTEGER DEFAULT 5, tipo_combustible TEXT DEFAULT 'Diesel', consumo_lts_100km REAL, herramientas_fijas TEXT, id_gps TEXT, base_habitual TEXT, km_actuales REAL DEFAULT 0, prox_mantencion_km REAL, disponible INTEGER DEFAULT 1)",
    "CREATE TABLE IF NOT EXISTS materiales (id TEXT PRIMARY KEY, nombre TEXT NOT NULL, codigo_interno TEXT UNIQUE, unidad TEXT DEFAULT 'unidad', stock_bodega REAL DEFAULT 0, stock_vehiculos REAL DEFAULT 0, stock_minimo REAL DEFAULT 5, lead_time_dias INTEGER DEFAULT 5, proveedor TEXT, precio_unitario REAL DEFAULT 0, ultima_actualizacion TEXT DEFAULT (datetime('now')))",
    "CREATE TABLE IF NOT EXISTS tipos_trabajo (id TEXT PRIMARY KEY, nombre_tipo TEXT NOT NULL, categoria TEXT, especialidad_req TEXT, certificacion_req TEXT, personal_minimo INTEGER DEFAULT 1, duracion_est_h REAL DEFAULT 4, desv_estandar_h REAL DEFAULT 1, herramientas_base TEXT, requiere_maquinaria INTEGER DEFAULT 0, nivel_riesgo TEXT, id_pts TEXT, n_ejecuciones INTEGER DEFAULT 0)",
    "CREATE TABLE IF NOT EXISTS trabajos (id TEXT PRIMARY KEY, fecha_registro TEXT DEFAULT (datetime('now')), id_proyecto TEXT, id_tipo_trabajo TEXT, prioridad TEXT, descripcion_corta TEXT, pts_asociado TEXT, personal_requerido TEXT, estado TEXT DEFAULT 'Pendiente', requiere_maquinaria INTEGER DEFAULT 0, id_maquinaria TEXT, requiere_material INTEGER DEFAULT 0, materiales_listos INTEGER DEFAULT 0, resultado TEXT, retraso_materiales INTEGER DEFAULT 0, retraso_maquinaria INTEGER DEFAULT 0, retraso_clima INTEGER DEFAULT 0, retraso_cliente INTEGER DEFAULT 0, retraso_permiso INTEGER DEFAULT 0, impacto_retraso TEXT DEFAULT 'Sin retraso', fecha_objetivo TEXT, dias_ventana INTEGER, id_alerta TEXT)",
    "CREATE TABLE IF NOT EXISTS alertas (id TEXT PRIMARY KEY, fecha_registro TEXT DEFAULT (datetime('now')), id_proyecto TEXT, nivel_falla TEXT, sistema_afectado TEXT, impacto_kw REAL DEFAULT 0, descripcion TEXT, recurrencia TEXT DEFAULT 'Primera vez', estado TEXT DEFAULT 'Sin asignar', id_trabajo TEXT, fuente TEXT DEFAULT 'Manual')",
    "CREATE TABLE IF NOT EXISTS ejecucion_trabajo (id TEXT PRIMARY KEY, id_trabajo TEXT, personal_ids TEXT, id_vehiculo TEXT, fecha_ejecucion TEXT, hora_salida TEXT, hora_llegada TEXT, hora_inicio_tarea TEXT, hora_fin_tarea TEXT, hora_salida_regreso TEXT, km_viaje REAL, tiempo_viaje_min INTEGER, tiempo_tarea_min INTEGER, trabajo_completado TEXT DEFAULT 'Pendiente', problema_principal TEXT DEFAULT 'Sin problemas', observacion TEXT, costo_viaje_est REAL)",
    "CREATE TABLE IF NOT EXISTS ventanas_optimas (id TEXT PRIMARY KEY, fecha_propuesta TEXT DEFAULT (datetime('now')), fecha_ejecucion TEXT, trabajos_incluidos TEXT, personal_sugerido TEXT, id_vehiculo TEXT, tiempo_total_est_h REAL, costo_total_est REAL, score_optimizacion REAL, restricciones_det TEXT, alternativa_b TEXT, estado_decision TEXT DEFAULT 'Pendiente', motivo_rechazo TEXT)",
    "CREATE TABLE IF NOT EXISTS maquinaria_subcontratada (id TEXT PRIMARY KEY, tipo_maquinaria TEXT, proveedor TEXT NOT NULL, contacto TEXT, regiones_servicio TEXT, lead_time_hrs INTEGER DEFAULT 48, costo_hora REAL DEFAULT 0, costo_traslado REAL DEFAULT 0, capacidad_ton REAL, disponible_hoy INTEGER DEFAULT 1, calificacion REAL DEFAULT 5, n_trabajos_conjuntos INTEGER DEFAULT 0)",
    "CREATE TABLE IF NOT EXISTS distancias_proyectos (id INTEGER PRIMARY KEY AUTOINCREMENT, id_proyecto_a TEXT, id_proyecto_b TEXT, km_entre REAL, tiempo_min INTEGER, tiempo_max_min INTEGER, peajes_aprox REAL DEFAULT 0, aptos_multivisita INTEGER DEFAULT 0, n_viajes_hist INTEGER DEFAULT 0, ultima_validacion TEXT)",
]

SEED_PROYECTOS = [
    {"id":"PROY-001","nombre":"Calle Larga","cliente":"IENERGIA","latitud":-32.890,"longitud":-71.200,"region":"V Región","criticidad":"Alta","hora_apertura":"07:00","hora_cierre":"18:00","requiere_permiso":1,"lead_time_permiso_d":2,"contacto_cliente":"Pedro Rojas +56 9 1234 5678","tipo_acceso":"Camino tierra","restricciones":"No ingresar en lluvia","activo":1},
    {"id":"PROY-002","nombre":"Falcon","cliente":"POWERTREE","latitud":-32.450,"longitud":-71.150,"region":"V Región","criticidad":"Media","hora_apertura":"07:00","hora_cierre":"18:00","requiere_permiso":0,"lead_time_permiso_d":0,"contacto_cliente":"Luis Gómez +56 9 8765 4321","tipo_acceso":"Pavimento","restricciones":"","activo":1},
    {"id":"PROY-003","nombre":"San Vicente","cliente":"OBTON","latitud":-34.440,"longitud":-71.090,"region":"VI Región","criticidad":"Media","hora_apertura":"08:00","hora_cierre":"17:00","requiere_permiso":1,"lead_time_permiso_d":1,"contacto_cliente":"Ana Torres +56 9 1111 2222","tipo_acceso":"4x4","restricciones":"Requiere 4x4","activo":1},
    {"id":"PROY-004","nombre":"Salerno","cliente":"IENERGIA","latitud":-33.450,"longitud":-70.650,"region":"RM","criticidad":"Alta","hora_apertura":"06:00","hora_cierre":"20:00","requiere_permiso":0,"lead_time_permiso_d":0,"contacto_cliente":"Jorge Silva +56 9 3333 4444","tipo_acceso":"Pavimento","restricciones":"","activo":1},
    {"id":"PROY-005","nombre":"Dinamo","cliente":"POWERTREE","latitud":-32.600,"longitud":-71.050,"region":"V Región","criticidad":"Media","hora_apertura":"07:00","hora_cierre":"18:00","requiere_permiso":0,"lead_time_permiso_d":0,"contacto_cliente":"María Vega +56 9 5555 6666","tipo_acceso":"Pavimento","restricciones":"","activo":1},
]

def init_db():
    if _use_supabase():
        try:
            _sb().table("usuarios").select("id").limit(1).execute()
            if not db_exists("usuarios","username","Admin"):
                _seed_all_supabase()
        except Exception as e:
            st.error(f"Error Supabase: {e}")
        return
    c = _sqlite()
    for sql in TABLES: c.execute(sql)
    c.commit()
    if not c.execute("SELECT 1 FROM usuarios WHERE username='Admin'").fetchone():
        _seed_sqlite(c)
    c.close()

def _seed_sqlite(c):
    c.execute("INSERT INTO usuarios (username,nombre,email,password_hash,rol) VALUES (?,?,?,?,?)",
              ("Admin","Administrador","admin@ienergia.cl",hash_password("iEnergia"),"admin"))
    for p in SEED_PROYECTOS:
        c.execute("INSERT OR IGNORE INTO proyectos (id,nombre,cliente,latitud,longitud,region,criticidad,hora_apertura,hora_cierre,requiere_permiso,lead_time_permiso_d,contacto_cliente,tipo_acceso,restricciones,activo) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  tuple(p.values()))
    seed_data = [
        ("personal",[{"id":"PERS-001","nombre":"Juan Pérez","especialidad":"Eléctrico","certificaciones":"AT,Altura","fecha_venc_cert":"2025-08-15","region":"RM","domicilio_lat":-33.52,"domicilio_lng":-70.68,"id_vehiculo":"VEH-02","puede_liderar":1,"jornada_max_h":10,"activo":1},{"id":"PERS-002","nombre":"Carlos Méndez","especialidad":"Mecánico","certificaciones":"Izaje,Altura","fecha_venc_cert":"2025-06-30","region":"RM","domicilio_lat":-33.48,"domicilio_lng":-70.72,"id_vehiculo":"VEH-01","puede_liderar":1,"jornada_max_h":10,"activo":1},{"id":"PERS-003","nombre":"Pedro Rojas","especialidad":"Eléctrico","certificaciones":"BT,AT","fecha_venc_cert":"2024-12-01","region":"V Región","domicilio_lat":-32.89,"domicilio_lng":-71.20,"id_vehiculo":"VEH-03","puede_liderar":0,"jornada_max_h":10,"activo":1},{"id":"PERS-004","nombre":"Ana López","especialidad":"Instrumentación","certificaciones":"BT,SCADA","fecha_venc_cert":"2025-03-20","region":"RM","domicilio_lat":-33.55,"domicilio_lng":-70.60,"id_vehiculo":None,"puede_liderar":0,"jornada_max_h":10,"activo":1}]),
        ("vehiculos",[{"id":"VEH-01","patente":"ABCD12","marca_modelo":"Toyota Hilux 4x4","anio":2021,"capacidad_personas":5,"tipo_combustible":"Diesel","consumo_lts_100km":9.5,"herramientas_fijas":"Escalera 4m, Taladro","id_gps":"GPS-001","base_habitual":"Bodega Ñuñoa","km_actuales":52340,"prox_mantencion_km":60000,"disponible":1},{"id":"VEH-02","patente":"EFGH34","marca_modelo":"Ford Ranger","anio":2022,"capacidad_personas":5,"tipo_combustible":"Diesel","consumo_lts_100km":8.8,"herramientas_fijas":"Multímetro, Pinzas","id_gps":"GPS-002","base_habitual":"Bodega Ñuñoa","km_actuales":38900,"prox_mantencion_km":40000,"disponible":1},{"id":"VEH-03","patente":"IJKL56","marca_modelo":"Mitsubishi L200","anio":2020,"capacidad_personas":4,"tipo_combustible":"Diesel","consumo_lts_100km":10.2,"herramientas_fijas":"Escalera 6m","id_gps":"GPS-003","base_habitual":"V Región","km_actuales":71200,"prox_mantencion_km":80000,"disponible":1}]),
        ("materiales",[{"id":"MAT-001","nombre":"Fusible 16A 1000V","codigo_interno":"F-16A-1KV","unidad":"unidad","stock_bodega":24,"stock_vehiculos":6,"stock_minimo":10,"lead_time_dias":5,"proveedor":"Schneider Electric","precio_unitario":3200},{"id":"MAT-002","nombre":"Batería tracker 30W","codigo_interno":"BAT-T30","unidad":"unidad","stock_bodega":3,"stock_vehiculos":0,"stock_minimo":8,"lead_time_dias":7,"proveedor":"SMA Solar","precio_unitario":45000},{"id":"MAT-003","nombre":"Batería tracker 60W","codigo_interno":"BAT-T60","unidad":"unidad","stock_bodega":2,"stock_vehiculos":0,"stock_minimo":6,"lead_time_dias":7,"proveedor":"SMA Solar","precio_unitario":78000},{"id":"MAT-004","nombre":"Epoxy estructural","codigo_interno":"EPX-001","unidad":"unidad","stock_bodega":0,"stock_vehiculos":0,"stock_minimo":2,"lead_time_dias":3,"proveedor":"Sika","precio_unitario":12500},{"id":"MAT-005","nombre":"Cable PV 6mm²","codigo_interno":"CAB-PV6","unidad":"metro","stock_bodega":120,"stock_vehiculos":30,"stock_minimo":50,"lead_time_dias":2,"proveedor":"Nexans","precio_unitario":1800}]),
        ("tipos_trabajo",[{"id":"TIPO-001","nombre_tipo":"Cambio fusible BT","categoria":"Eléctrico","especialidad_req":"Eléctrico","certificacion_req":"BT","personal_minimo":1,"duracion_est_h":1.5,"desv_estandar_h":0.5,"herramientas_base":"Multímetro,Destornilladores","requiere_maquinaria":0,"nivel_riesgo":"Bajo","id_pts":"PTS-ELEC-001","n_ejecuciones":0},{"id":"TIPO-002","nombre_tipo":"Reemplazo batería tracker","categoria":"Mecánico","especialidad_req":"Mecánico","certificacion_req":"Altura","personal_minimo":2,"duracion_est_h":3.0,"desv_estandar_h":1.0,"herramientas_base":"Llaves,Multímetro","requiere_maquinaria":0,"nivel_riesgo":"Medio","id_pts":"PTS-MEC-002","n_ejecuciones":0},{"id":"TIPO-003","nombre_tipo":"Reparación inversor","categoria":"Eléctrico","especialidad_req":"Eléctrico","certificacion_req":"AT","personal_minimo":2,"duracion_est_h":4.0,"desv_estandar_h":1.5,"herramientas_base":"Analizador redes,EPP AT","requiere_maquinaria":0,"nivel_riesgo":"Alto","id_pts":"PTS-ELEC-003","n_ejecuciones":0},{"id":"TIPO-004","nombre_tipo":"Epoxy A-frame","categoria":"Civil","especialidad_req":"Civil","certificacion_req":"Altura","personal_minimo":2,"duracion_est_h":5.0,"desv_estandar_h":2.0,"herramientas_base":"Amoladora,Llaves torque","requiere_maquinaria":0,"nivel_riesgo":"Alto","id_pts":"PTS-CIV-001","n_ejecuciones":0},{"id":"TIPO-005","nombre_tipo":"Instalación UPS","categoria":"Eléctrico","especialidad_req":"Eléctrico","certificacion_req":"BT","personal_minimo":1,"duracion_est_h":2.5,"desv_estandar_h":0.5,"herramientas_base":"Multímetro","requiere_maquinaria":0,"nivel_riesgo":"Bajo","id_pts":"PTS-ELEC-002","n_ejecuciones":0}]),
        ("alertas",[{"id":"ALT-2024-031","id_proyecto":"PROY-002","nivel_falla":"Crítico","sistema_afectado":"Inversores 4 y 9","impacto_kw":45.0,"descripcion":"Caída inversor #4 (recurrente) e inversor #9.","recurrencia":"Alta","estado":"Sin asignar","fuente":"Manual"},{"id":"ALT-2024-030","id_proyecto":"PROY-001","nivel_falla":"Alto","sistema_afectado":"Trackers sin batería","impacto_kw":18.0,"descripcion":"6 trackers sin batería. Baterías 30/60W agotadas.","recurrencia":"Media","estado":"Sin asignar","fuente":"Manual"},{"id":"ALT-2024-029","id_proyecto":"PROY-005","nivel_falla":"Medio","sistema_afectado":"Paneles backsheet","impacto_kw":8.0,"descripcion":"Rotura paneles backsheet. Falla sistemática.","recurrencia":"Primera vez","estado":"Sin asignar","fuente":"Manual"}]),
        ("trabajos",[{"id":"TRB-2024-0045","id_proyecto":"PROY-001","id_tipo_trabajo":"TIPO-002","prioridad":"Crítica","descripcion_corta":"6 trackers sin batería.","pts_asociado":"PTS-MEC-002","personal_requerido":"2 Mecánicos","estado":"Agendado","requiere_maquinaria":0,"requiere_material":1,"materiales_listos":0,"retraso_materiales":0,"retraso_maquinaria":0,"retraso_clima":0,"retraso_cliente":0,"retraso_permiso":0,"impacto_retraso":"Sin retraso","fecha_objetivo":"2024-03-22","id_alerta":"ALT-2024-030"},{"id":"TRB-2024-0046","id_proyecto":"PROY-002","id_tipo_trabajo":"TIPO-003","prioridad":"Alta","descripcion_corta":"Reparación inversor #4 y #9.","pts_asociado":"PTS-ELEC-003","personal_requerido":"1 Eléctrico AT","estado":"Pendiente","requiere_maquinaria":1,"requiere_material":0,"materiales_listos":1,"retraso_materiales":0,"retraso_maquinaria":0,"retraso_clima":0,"retraso_cliente":0,"retraso_permiso":0,"impacto_retraso":"Sin retraso","fecha_objetivo":"2024-03-25","id_alerta":"ALT-2024-031"}]),
    ]
    for table, rows in seed_data:
        for row in rows:
            cols = ",".join(row.keys()); phs = ",".join("?"*len(row))
            c.execute(f"INSERT OR IGNORE INTO {table} ({cols}) VALUES ({phs})", list(row.values()))
    c.commit()

def _seed_all_supabase():
    db_insert("usuarios",{"username":"Admin","nombre":"Administrador","email":"admin@ienergia.cl","password_hash":hash_password("iEnergia"),"rol":"admin","activo":1})
    for p in SEED_PROYECTOS:
        if not db_exists("proyectos","id",p["id"]): db_insert("proyectos",p)

# ── Alias de compatibilidad con versiones anteriores ─────────────────────────
def query(sql, params=None, fetchall=True):
    """Ejecuta SQL y devuelve lista de dicts (solo SQLite local)."""
    conn = _sqlite()
    cur = conn.execute(sql, params or ())
    if fetchall:
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def execute(sql, params=None):
    """Ejecuta INSERT/UPDATE/DELETE (solo SQLite local)."""
    conn = _sqlite()
    conn.execute(sql, params or ())
    conn.commit()
    conn.close()
