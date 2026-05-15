# iEnergia OyM — Guía de despliegue paso a paso

## ¿Qué es cada cosa?

```
GitHub     → Carpeta en la nube donde vive el código (como un Google Drive para código)
Supabase   → Base de datos en la nube (el "Excel" donde se guardan los datos)
Streamlit  → El servicio que convierte el código en una app con link web
```

---

## PASO 1 — Crear cuenta en GitHub (5 min)

1. Ve a https://github.com/signup
2. Crea cuenta con tu email
3. Verifica el email

---

## PASO 2 — Crear cuenta en Supabase (5 min)

1. Ve a https://supabase.com → "Start for free"
2. Entra con tu cuenta de GitHub (más fácil)
3. Clic en "New project"
4. Nombre: `ienergia-oym`
5. Región: **South America (São Paulo)** — más cercano a Chile
6. Genera una contraseña segura y **guárdala**
7. Clic en "Create new project" — tarda ~2 minutos

### Obtener credenciales de Supabase:
- Ve a **Settings → Database**
- Copia la **"Connection string"** (modo URI) — empieza con `postgresql://...`
- Ve a **Settings → API**
- Copia la **"Project URL"**

---

## PASO 3 — Subir código a GitHub (10 min)

### Opción A: desde el navegador (más fácil, sin instalar nada)
1. En GitHub → "New repository"
2. Nombre: `ienergia-oym` (o el que quieras)
3. Privado (recomendado)
4. Clic en "uploading an existing file"
5. Arrastra todos los archivos de esta carpeta

### Opción B: desde terminal (si tienes Git instalado)
```bash
cd ienergia_oym_v2
git init
git add .
git commit -m "iEnergia OyM v2.0"
git remote add origin https://github.com/TU_USUARIO/ienergia-oym.git
git push -u origin main
```

---

## PASO 4 — Desplegar en Streamlit Cloud (5 min)

1. Ve a https://share.streamlit.io
2. Entra con tu cuenta de GitHub
3. Clic en "New app"
4. Selecciona tu repositorio `ienergia-oym`
5. Main file path: `app.py`
6. App URL: escribe el nombre que quieras → quedará como `tu-nombre.streamlit.app`
7. Clic en "Deploy!"

### Configurar los secrets (credenciales):
1. En tu app de Streamlit Cloud → "Settings" → "Secrets"
2. Pega esto (con tus valores reales):

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
SUPABASE_DB_URL = "postgresql://postgres:[PASSWORD]@db.[ID].supabase.co:5432/postgres"
SUPABASE_URL = "https://[ID].supabase.co"
```

3. Clic en "Save" → la app se reinicia automáticamente

---

## Credenciales iniciales de la app

| Usuario    | Contraseña | Acceso                        |
|------------|------------|-------------------------------|
| Admin      | iEnergia   | Todo                          |
| supervisor | sup123     | Dashboard + aprobar ventanas  |
| jperez     | tech123    | Solo checklist de sus tareas  |

**Cambia las contraseñas desde el módulo "Usuarios" tras el primer ingreso.**

---

## ¿Por qué Supabase y no SQLite?

SQLite guarda los datos en un archivo en el mismo servidor donde corre la app.
Streamlit Cloud reinicia la app cada cierto tiempo y **borra ese archivo**.
Supabase es una base de datos separada que vive en su propio servidor — los datos
nunca se pierden aunque Streamlit reinicie la app.

---

## Estructura del proyecto

```
ienergia_oym_v2/
├── app.py                        ← Entrada principal + menú lateral
├── requirements.txt              ← Dependencias Python
├── .streamlit/
│   ├── config.toml               ← Colores y tema de la app
│   └── secrets.toml.template     ← Plantilla de credenciales
├── utils/
│   ├── database.py               ← Conexión BD (Supabase o SQLite local)
│   ├── auth.py                   ← Login y control de acceso por rol
│   └── ai_engine.py              ← Motor de optimización con IA
└── pages/
    ├── dashboard.py              ← Pantalla principal con resumen
    ├── alertas.py                ← Gestión de alertas y tareas
    ├── trabajos.py               ← Trabajos + checklist técnicos
    ├── optimizacion.py           ← Ventanas óptimas generadas por IA
    ├── chat.py                   ← Chat directo con la IA
    ├── personal.py               ← Ficha de trabajadores
    ├── proyectos.py              ← Proyectos/parques
    ├── materiales.py             ← Stock de materiales
    ├── vehiculos.py              ← Flota de vehículos
    ├── tipos_trabajo.py          ← Catálogo de tipos de trabajo
    ├── fuentes.py                ← Estado de integraciones (GPS, SCADA, etc.)
    └── usuarios.py               ← Gestión de usuarios y roles
```
