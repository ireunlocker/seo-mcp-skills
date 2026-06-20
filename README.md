# SEO MCP Skill — Automatización SEO con IA + Google APIs + MCP

**Creado por Kerwyn Arias**

Sistema autónomo de auditoría, monitoreo y optimización SEO que combina inteligencia artificial (OpenRouter/Gemini), Google Analytics 4, Google Search Console y el protocolo MCP (Model Context Protocol) para mejorar el posicionamiento web de forma automatizada.

---

## 📋 Tabla de Contenidos

- [🚀 ¿Qué es SEO MCP Skill?](#-qué-es-seo-mcp-skill)
- [✨ Características Principales](#-características-principales)
- [🏗️ Arquitectura del Sistema](#️-arquitectura-del-sistema)
- [📦 Requisitos del Sistema](#-requisitos-del-sistema)
- [🔧 Instalación Paso a Paso](#-instalación-paso-a-paso)
- [🎯 Skills de IA Disponibles](#-skills-de-ia-disponibles)
- [📋 Comandos de Uso](#-comandos-de-uso)
- [🔌 Modo MCP Avanzado](#-modo-mcp-avanzado)
- [📚 Sistema de Auto-Aprendizaje](#-sistema-de-auto-aprendizaje)
- [🌐 Integración con Proyectos Web](#-integración-con-proyectos-web)
- [➕ Cómo Agregar Más Sitios Web al Mismo Sistema](#-cómo-agregar-más-sitios-web-al-mismo-sistema)
- [🐳 Despliegue en Servidor (Docker)](#-despliegue-en-servidor-docker)
- [📤 Subir a GitHub](#-subir-a-github)
- [📝 Cómo Registrar tu Proyecto](#-cómo-registrar-tu-proyecto)
- [🛠️ Solución de Problemas](#️-solución-de-problemas)

---

## 🚀 ¿Qué es SEO MCP Skill?

SEO MCP Skill es un **sistema autónomo de auditoría, monitoreo y optimización SEO** que utiliza inteligencia artificial para analizar, diagnosticar y mejorar el posicionamiento de sitios web en motores de búsqueda.

A diferencia de las herramientas SEO tradicionales que solo generan reportes, **SEO MCP Skill ejecuta correcciones en tiempo real**: modifica archivos MDX/TSX/JSX directamente en el proyecto, actualiza sitemaps, hace commit y push automáticos a Git, y notifica los resultados por Telegram.

### ¿Qué lo hace único?

| Característica | SEO MCP Skill | Herramientas tradicionales |
|---|---|---|
| Correcciones automáticas | ✅ Modifica archivos en tiempo real | ❌ Solo reportan problemas |
| Auto-aprendizaje | ✅ SQLite history mejora respuestas | ❌ No aprenden de ejecuciones pasadas |
| Múltiples IAs | ✅ OpenRouter + Gemini con fallback automático | ❌ Usan un único modelo |
| MCP Protocol | ✅ Navegador, GSC, herramientas externas | ❌ Sin integración MCP |
| Precio | ✅ Modelos económicos (DeepSeek, GLM-4) | ❌ Suscripciones mensuales caras |
| Open Source | ✅ Código libre y personalizable | ❌ Software propietario |

### Stack Tecnológico

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.12+ |
| IA Principal | OpenRouter API (DeepSeek, Claude, Gemini, GPT-4o) |
| IA Alternativa | Google Gemini API |
| Analítica | Google Analytics Data API (GA4) |
| Search Console | Google Search Console API |
| Protocolo Herramientas | MCP (Model Context Protocol) |
| Base de Datos | SQLite (auto-aprendizaje) |
| Automatización | schedule (cron en Python) |
| Notificaciones | Telegram Bot API |
| Control Versiones | Git (auto push) |
| Contenedores | Docker |

---

## ✨ Características Principales

### 1. Auditoría Técnica SEO Automatizada
Analiza la estructura del código, jerarquía de headings, meta tags, Core Web Vitals, indexación, sitemaps y robots.txt. **Corrige los errores automáticamente** sobrescribiendo los archivos del proyecto.

### 2. Creación de Contenido SEO Optimizado
Genera artículos, páginas de servicio y meta tags con densidad de keywords optimizada, estructura semántica correcta y contenido original. Soporta MDX con frontmatter para Next.js y otros frameworks.

### 3. Dashboard de Performance en Tiempo Real
Conecta con GA4 y GSC para generar reportes detallados de tráfico orgánico, posiciones de keywords, clics, impresiones y CTR. Traduce datos en recomendaciones accionables.

### 4. Multi-Modelo de IA con Fallback Automático
Si el modelo principal falla (límite de rate, caída del servicio), el sistema intenta automáticamente con modelos alternativos: DeepSeek → GLM-4 → Claude → Llama → Gemini → GPT-4o. Esto garantiza alta disponibilidad.

### 5. Function Calling Nativo
Los skills se definen como funciones JSON con parámetros tipados. La IA los invoca mediante Function Calling, asegurando que el output tenga siempre la estructura esperada.

### 6. MCP (Model Context Protocol)
Conecta con servidores MCP externos como navegadores headless (Puppeteer), herramientas de análisis, o APIs adicionales. El agente universal puede navegar por la web, hacer scraping y ejecutar herramientas en tiempo real.

### 7. Auto-Aprendizaje con SQLite
Cada ejecución se registra en una base de datos SQLite con inputs, outputs, éxito/fallo y metadatos. La IA recibe contexto histórico en ejecuciones posteriores, mejorando sus respuestas con el tiempo.

### 8. Git Automático
Detecta cambios en los archivos del proyecto, hace commit con mensajes descriptivos (prefijo `auto:`) y hace push al repositorio remoto automáticamente.

### 9. Notificaciones Telegram
Envía resúmenes de ejecución, reportes y alertas a un chat o grupo de Telegram configurado, permitiendo monitoreo remoto sin necesidad de revisar logs.

### 10. Arquitectura Multi-Proyecto
Un mismo sistema puede gestionar múltiples sitios web usando diferentes archivos `.env`. Ideal para agencias SEO que manejan varios clientes.

### 11. Docker Listo
Incluye Dockerfile y docker-compose.yml para despliegue en servidores VPS. Con systemd para ejecución como servicio del sistema.

### 12. Sitemap Updater
Tras crear nuevo contenido o modificar páginas existentes, puede regenerar automáticamente el sitemap.xml del proyecto.

---

## 🏗️ Arquitectura del Sistema

```
                              ┌─────────────────────────────────────┐
                              │           INTERNET / WEB            │
                              └──────────┬──────────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    ▼                    ▼                    ▼
            ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐
            │  Google      │   │  Google      │   │  Sitio Web del   │
            │  Analytics 4 │   │  Search      │   │  Cliente         │
            │  (GA4 API)   │   │  Console API │   │  (Next.js, etc.) │
            └──────┬───────┘   └──────┬───────┘   └────────┬─────────┘
                   │                  │                     │
                   └──────┬───────────┴──────────┬──────────┘
                          │                      │
                          ▼                      ▼
              ┌─────────────────────────────────────────┐
              │           PYTHON ORCHESTRATOR            │
              │         (orchestrator.py)                │
              │                                          │
              │  ┌─────────┐  ┌──────────┐  ┌────────┐  │
              │  │  GA4    │  │   GSC    │  │History │  │
              │  │ Client  │  │  Client  │  │ Client │  │
              │  └────┬────┘  └────┬─────┘  └────┬───┘  │
              │       │            │              │      │
              │       ▼            ▼              ▼      │
              │  ┌────────────────────────────────────┐  │
              │  │         OpenRouter / Gemini        │  │
              │  │     (openrouter_client.py)         │  │
              │  │  • Function Calling                │  │
              │  │  • Fallback automático             │  │
              │  │  • Múltiples modelos               │  │
              │  └────────────────┬───────────────────┘  │
              │                   │                      │
              │                   ▼                      │
              │  ┌────────────────────────────────────┐  │
              │  │   Skills (JSON Schemas)            │  │
              │  │  • seo_content_creator             │  │
              │  │  • seo_dashboard                   │  │
              │  │  • seo_site_auditor                │  │
              │  └────────────────┬───────────────────┘  │
              │                   │                      │
              │                   ▼                      │
              │  ┌────────────────────────────────────┐  │
              │  │   Acciones según skill ejecutado   │  │
              │  │                                    │  │
              │  │  ┌─────────────────────┐           │  │
              │  │  │ Site Auditor:       │           │  │
              │  │  │ Sobrescribe archivos│           │  │
              │  │  │ MDX/TSX/JSX        │           │  │
              │  │  └─────────────────────┘           │  │
              │  │                                    │  │
              │  │  ┌─────────────────────┐           │  │
              │  │  │ Content Creator:    │           │  │
              │  │  │ Crea nuevos .mdx    │           │  │
              │  │  └─────────────────────┘           │  │
              │  │                                    │  │
              │  │  ┌─────────────────────┐           │  │
              │  │  │ Dashboard:          │           │  │
              │  │  │ Guarda reportes .md │           │  │
              │  │  └─────────────────────┘           │  │
              │  └────────────────┬───────────────────┘  │
              │                   │                      │
              └───────────────────┼──────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  Git Auto     │      │  Telegram        │      │  Backend API     │
│  Push         │      │  Notifier        │      │  (opcional)      │
│  (commit +    │      │  (resumen +      │      │  (envía reportes │
│   push a      │      │   reporte)       │      │   a tu panel)    │
│   remoto)     │      └──────────────────┘      └──────────────────┘
└───────────────┘

              ┌─────────────────────────────────────────┐
              │   MODO AVANZADO: Universal SEO Agent    │
              │   (universal_seo_agent.py)              │
              │                                          │
              │  ┌──────────┐  ┌──────────┐  ┌────────┐  │
              │  │ MCP      │  │ MCP      │  │ MCP    │  │
              │  │ Browser  │  │ GSC      │  │ Custom │  │
              │  │(Puppeteer)│  │ Server   │  │ Server │  │
              │  └──────────┘  └──────────┘  └────────┘  │
              └──────────────────────────────────────────┘
```

### Flujo de Datos

1. **Inicio**: El orquestador se ejecuta manualmente (`monitor`) o por cron (`schedule`)
2. **Recolección**: Obtiene datos de GA4 (tráfico orgánico) y GSC (keywords, posiciones)
3. **Análisis**: Envía los datos al modelo de IA junto con el schema JSON del skill correspondiente
4. **Decisión**: La IA procesa los datos y devuelve el output estructurado según el schema
5. **Acción**: El orquestador ejecuta la acción correspondiente (sobrescribir archivo, crear contenido, guardar reporte)
6. **Registro**: Almacena la ejecución en SQLite con timestamp, inputs, outputs y resultado
7. **Notificación**: Envía resumen por Telegram y/o al backend API
8. **Versión**: Si hay cambios, hace commit y push a Git automáticamente

---

## 📦 Requisitos del Sistema

### Software Requerido

| Requisito | Versión Mínima | Opcional |
|---|---|---|
| Python | 3.12+ | — |
| pip | Última estable | — |
| Git | 2.x+ | — |
| Node.js | 18.x+ (para MCP Puppeteer) | ✅ |
| Docker | 24.x+ | ✅ |
| npx | Incluido con Node.js | ✅ |

### APIs Necesarias

| API | Costo | Prioridad |
|---|---|---|
| OpenRouter | Pago por uso (~$0.14/1M tokens DeepSeek) | Recomendada |
| Google Gemini | Gratuito (60 requests/minuto) | Alternativa |
| Google Cloud Platform | Gratuito (cuota estándar) | Obligatorio |
| GA4 + GSC | Gratuito | Obligatorio para dashboard |

### Permisos Google Cloud

Para que el sistema funcione completamente, necesitas:

1. Una **cuenta de servicio** (Service Account) en Google Cloud
2. La API de **Google Analytics Data** habilitada
3. La API de **Google Search Console** habilitada
4. La cuenta de servicio debe tener acceso a:
   - La propiedad GA4 como "Lector"
   - El sitio en GSC como "Propietario" o "Lector"

---

## 🔧 Instalación Paso a Paso

### 1. Clonar o descargar

```bash
git clone https://github.com/tuusuario/seo-mcp-skill.git
cd seo-mcp-skill
```

### 2. Ejecutar setup

```bash
bash setup.sh
```

Este script:
- Verifica que Python 3.12+ esté instalado
- Instala todas las dependencias Python (pip install -r requirements.txt)
- Crea el archivo `inputs/.env` desde la plantilla (si no existe)
- Inicializa la base de datos SQLite
- Configura permisos de los scripts

### 3. Configurar .env

```bash
cp config/.env.template inputs/.env
# Ahora edita inputs/.env con tus API keys reales
nano inputs/.env   # o cualquier editor de texto
```

**Variables obligatorias:**
- `OPENROUTER_API_KEY` o `GEMINI_API_KEY` (al menos una)
- `PROJECT_PATH` (ruta a tu proyecto web)
- `GA4_CREDENTIALS_PATH` y `GA4_PROPERTY_ID` (para dashboard)
- `GSC_CREDENTIALS_PATH` y `GSC_SITE_URL` (para dashboard)

### 4. Obtener credenciales Google APIs

Sigue estos pasos para configurar el acceso a GA4 y GSC:

#### 4.1 Crear proyecto en Google Cloud Console

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Haz clic en "Seleccionar proyecto" → "Nuevo proyecto"
3. Ponle un nombre (ej: "seo-mcp-skill") y crealo
4. Espera a que se cree y seleccionalo

#### 4.2 Habilitar APIs necesarias

1. En el menú de navegación, ve a "APIs y Servicios" → "Biblioteca"
2. Busca y habilita: **Google Analytics Data API**
3. Busca y habilita: **Google Search Console API**
4. Busca y habilita: **Google Search Console API** (sí, aparece dos veces en distintos listados)
5. Espera 2-3 minutos a que se activen

#### 4.3 Crear cuenta de servicio

1. Ve a "IAM y Administración" → "Cuentas de servicio"
2. Haz clic en "Crear cuenta de servicio"
3. Ponle un nombre (ej: "seo-service-account")
4. Asigna el rol: **Editor** (o "Visualizador" si prefieres mínimos permisos)
5. Haz clic en "Hecho"

#### 4.4 Generar clave JSON

1. En la lista de cuentas de servicio, haz clic en la que acabas de crear
2. Ve a la pestaña "Claves"
3. Haz clic en "Agregar clave" → "Crear clave nueva" → JSON
4. Se descargará un archivo `.json`. **Guárdalo en un lugar seguro**
5. Mueve este archivo a `inputs/ga4-service-account.json` (o la ruta que prefieras)
6. Actualiza `GA4_CREDENTIALS_PATH` en tu `.env` con esta ruta
7. Si usas el mismo service account para GSC, copia también a `GSC_CREDENTIALS_PATH`

#### 4.5 Dar acceso a GA4

1. Ve a [Google Analytics](https://analytics.google.com/)
2. Selecciona tu propiedad
3. Ve a "Administrar" → "Gestión de usuarios" (en la columna de la propiedad)
4. Haz clic en "Añadir usuario"
5. Introduce el email de la cuenta de servicio (termina en `@*.gserviceaccount.com`)
6. Asigna permisos: al menos "Lector"
7. Guarda

#### 4.6 Dar acceso a GSC

1. Ve a [Google Search Console](https://search.google.com/search-console/)
2. Selecciona tu sitio (o añádelo si no lo has hecho)
3. Ve a "Configuración" → "Usuarios y permisos"
4. Haz clic en "Añadir usuario"
5. Introduce el email de la cuenta de servicio
6. Permiso: "Lector" o "Propietario completo"
7. Guarda

#### 4.7 Obtener GA4 Property ID

1. En Google Analytics, ve a "Administrar"
2. En la columna "Propiedad", haz clic en "Configuración de la propiedad"
3. El **ID de la propiedad** aparece al principio (ej: "123456789")
4. Copia este número en `GA4_PROPERTY_ID`

### 5. Verificar conexión

```bash
# Probar OpenRouter (recomendado)
python scripts/orchestrator.py test-openrouter

# O probar Gemini
python scripts/orchestrator.py test-gemini
```

Si todo funciona, verás la respuesta de la IA en consola.

---

## 🎯 Skills de IA Disponibles

| Skill | Archivo JSON | Descripción |
|---|---|---|
| SEO Content Creator | `skills/seo-content-creator.json` | Creación y optimización de contenido SEO |
| SEO Dashboard | `skills/seo-dashboard.json` | Reportes de performance y análisis de métricas |
| SEO Site Auditor | `skills/seo-site-auditor.json` | Auditoría técnica SEO completa |

### SEO Content Creator

**Propósito:** Genera contenido SEO optimizado para artículos, páginas de servicio, landing pages y meta tags.

**Inputs:**
- `slug`: Slug de la URL recomendada (se genera automáticamente si no se provee)
- `title`: Título optimizado (máx 60 caracteres)
- `content_mdx`: Contenido completo en formato MDX con frontmatter

**Parámetros adicionales (configurables):**
- `keyword_principal`: La keyword principal a posicionar
- `tipo_contenido`: Artículo, página servicio, guía, tutorial
- `tono`: Profesional, cercano, técnico, divulgativo
- `longitud`: Número aproximado de palabras

**Output:**
- `slug`: String con el slug optimizado
- `title`: String con el título (≤60 chars)
- `content_mdx`: String con el contenido completo MDX

**Ejemplo de uso:**
```python
result = orch.execute_skill_with_ai("seo_content_creator", {
    "keyword_principal": "seguros hogar Madrid",
    "tipo_contenido": "artículo informacional",
    "tono": "profesional",
    "longitud_aprox": "1000 palabras"
})
# → Guarda el .mdx en el proyecto y actualiza el sitemap
```

### SEO Dashboard

**Propósito:** Genera reportes detallados de performance SEO basados en datos reales de GA4 y GSC.

**Inputs:**
- `report_markdown`: Análisis detallado en Markdown
- `suggested_actions`: Lista de acciones recomendadas

**Parámetros configurables:**
- `periodo_desde`, `periodo_hasta`: Rango de fechas
- `include_gsc`, `include_ga4`: Qué fuentes incluir
- `top_n_keywords`, `top_n_pages`: Cuántos elementos analizar
- `ga4_data`: Datos de Google Analytics 4
- `gsc_keywords`: Keywords desde Google Search Console

**Output:**
- `report_markdown`: String con el reporte completo en Markdown
- `suggested_actions`: Array de strings con acciones priorizadas

**Ejemplo de uso:**
```python
result = orch.execute_skill_with_ai("seo_dashboard", {
    "periodo_desde": "2026-05-20",
    "periodo_hasta": "2026-06-19",
    "ga4_data": {"organic_sessions": 5420, "organic_users": 4100},
    "gsc_keywords": [...]
})
# → Guarda el reporte en outputs/YYYYMMDD_reporte_*.md
```

### SEO Site Auditor

**Propósito:** Realiza auditorías técnicas SEO completas, detecta errores y genera el código corregido.

**Inputs:**
- `updated_mdx_content`: Código fuente completo corregido y optimizado
- `summary_of_changes`: Resumen de cambios realizados

**Parámetros configurables:**
- `url_sitio`: URL de la página a auditar
- `plataforma_web`: Framework utilizado (Next.js, WordPress, etc.)
- `contenido_actual`: Contenido actual del archivo

**Output:**
- `updated_mdx_content`: String con el archivo completo corregido
- `summary_of_changes`: String con resumen markdown de cambios

**Ejemplo de uso:**
```python
result = orch.execute_skill_with_ai("seo_site_auditor", {
    "url_sitio": "/servicios",
    "plataforma_web": "Next.js (App Router) con Tailwind y MDX",
    "contenido_actual": "... contenido del archivo ..."
})
# → Sobrescribe el archivo físico con las correcciones
```

---

## 📋 Comandos de Uso

### Probar conexión

```bash
# Probar OpenRouter (recomendado por su soporte de Function Calling)
python scripts/orchestrator.py test-openrouter

# Probar Gemini (alternativa gratuita)
python scripts/orchestrator.py test-gemini
```

### Monitoreo manual

Ejecuta un ciclo completo de monitoreo SEO (obtiene métricas GA4 + GSC, genera reporte, notifica):

```bash
python scripts/orchestrator.py monitor
```

### Monitoreo programado (cron)

Inicia el planificador que ejecuta automáticamente:
- Reporte global diario a las 08:00
- Auditoría por página a las 10:00 y 22:00
- Reporte semanal los lunes a las 09:00

```bash
python scripts/orchestrator.py schedule
```

Para ejecutarlo en segundo plano en un servidor:

```bash
nohup python scripts/orchestrator.py schedule > outputs/scheduler.log 2>&1 &
```

### Ejecutar skill específica desde Python

```python
from scripts.orchestrator import SEOOrchestrator

orch = SEOOrchestrator()

# Ejemplo 1: Crear contenido
result = orch.execute_skill_with_ai(
    "seo_content_creator",
    {
        "keyword_principal": "seguros hogar Madrid 2026",
        "tipo_contenido": "artículo informacional",
        "tono": "profesional y cercano",
        "longitud_aprox": "1200 palabras",
        "audiencia": "propietarios de vivienda en Madrid"
    }
)
print(result["function_calls"][0]["args"]["slug"])
print(result["function_calls"][0]["args"]["title"])
print(result["function_calls"][0]["args"]["content_mdx"])

# Ejemplo 2: Auditar una página
result = orch.execute_skill_with_ai(
    "seo_site_auditor",
    {
        "url_sitio": "/",
        "plataforma_web": "Next.js (App Router) con Tailwind y MDX",
        "contenido_actual": open("ruta/al/archivo/page.tsx").read(),
        "date": "2026-06-20 10:00:00"
    }
)
print(result["function_calls"][0]["args"]["summary_of_changes"])

# Ejemplo 3: Generar dashboard
result = orch.execute_skill_with_ai(
    "seo_dashboard",
    {
        "periodo_desde": "2026-05-20",
        "periodo_hasta": "2026-06-19",
        "include_gsc": True,
        "include_ga4": True,
        "ga4_data": {"organic_sessions": 5420, "organic_users": 4100},
        "gsc_keywords": [{"query": "ejemplo", "clicks": 120, "impressions": 5400}]
    }
)
print(result["function_calls"][0]["args"]["report_markdown"])
print(result["function_calls"][0]["args"]["suggested_actions"])
```

---

## 🔌 Modo MCP Avanzado

### ¿Qué es MCP?

MCP (Model Context Protocol) es un protocolo abierto desarrollado por Anthropic que estandariza cómo los modelos de lenguaje pueden interactuar con herramientas y fuentes de datos externas. Piensa en MCP como "USB-C para IAs": un conector universal que permite conectar cualquier modelo con cualquier herramienta.

En SEO MCP Skill, MCP se usa para:

- **Navegación web**: Abrir páginas, hacer scroll, capturar screenshots
- **Scraping**: Extraer contenido de competidores
- **Google Search Console**: Consultar datos directamente via MCP server
- **Análisis en vivo**: Ver cómo se renderiza una página en tiempo real

### Cómo configurar servidores MCP

Los servidores MCP se configuran en el archivo `.env` mediante la variable `MCP_SERVERS`:

```bash
# Ejemplo: Servidor Puppeteer para navegación headless
MCP_SERVERS=[{"name":"browser","command":"npx","args":["-y","@modelcontextprotocol/server-puppeteer"]}]

# Ejemplo: Múltiples servidores
MCP_SERVERS=[{"name":"browser","command":"npx","args":["-y","@modelcontextprotocol/server-puppeteer"]}]
```

### El Agente Universal

El `UniversalSEOAgent` (en `scripts/universal_seo_agent.py`) es la implementación más avanzada del sistema. Combina:

1. **OpenRouterClient**: Para la generación de lenguaje y toma de decisiones
2. **UniversalMCPBridge**: Para conectar con servidores MCP
3. **Pipeline autónomo**: El modelo recibe las herramientas disponibles, decide cuáles usar, las ejecuta, y continúa hasta completar la tarea

**Cómo funciona:**

```
1. Inicializa conexión con todos los servidores MCP
2. Obtiene la lista de herramientas disponibles
3. Construye un payload de chat completions con las herramientas
4. Envía el prompt a la IA (OpenRouter)
5. La IA puede:
   a) Responder directamente (si no necesita herramientas)
   b) Solicitar ejecutar una herramienta específica
6. Si la IA pide una herramienta, el agente la ejecuta
7. El resultado se devuelve al modelo para continuar
8. Se cierran las conexiones MCP al finalizar
```

**Ejemplo con Puppeteer:**

```bash
export RUN_UNIVERSAL_AGENT=1
python scripts/universal_seo_agent.py
```

Este comando:
1. Inicia un navegador headless via Puppeteer
2. Pide a la IA que busque en Google un tema específico
3. La IA navega, extrae información de competidores
4. El agente entrega el análisis completo

### Ejemplo con Google Search Console MCP

Si tienes un servidor MCP que expone la API de GSC, puedes configurarlo:

```python
servers = [
    {"name": "gsc", "command": "python3", "args": ["-m", "mcp_server_gsc"]},
    {"name": "browser", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-puppeteer"]}
]

agent = UniversalSEOAgent("/ruta/proyecto", servers)
await agent.run_task("Analiza mis keywords de GSC y sugiere mejoras")
```

---

## 📚 Sistema de Auto-Aprendizaje

### ¿Cómo funciona?

Cada ejecución de cualquier skill se registra en una base de datos SQLite (`outputs/seo_history.db`). La tabla principal registra:

- `execution_id`: Identificador único
- `skill_name`: Qué skill se ejecutó
- `input_data`: Los parámetros de entrada (JSON)
- `output_data`: La respuesta de la IA (JSON)
- `success`: Si la ejecución fue exitosa
- `model_used`: Qué modelo de IA se usó
- `tokens_used`: Consumo de tokens
- `created_at`: Timestamp

### Tablas SQLite

```
seo_executions
  ├── id (INTEGER PRIMARY KEY)
  ├── skill_name (TEXT)
  ├── input_data (TEXT - JSON)
  ├── output_data (TEXT - JSON)
  ├── success (BOOLEAN)
  ├── model_used (TEXT)
  ├── tokens_used (INTEGER)
  ├── execution_time_ms (INTEGER)
  └── created_at (DATETIME)

seo_keywords
  ├── id (INTEGER PRIMARY KEY)
  ├── execution_id (INTEGER FK)
  ├── query (TEXT)
  ├── clicks (INTEGER)
  ├── impressions (INTEGER)
  ├── ctr (REAL)
  ├── position (REAL)
  └── date (DATE)
```

### ¿Cómo mejora las respuestas?

Cuando se ejecuta un skill, el orquestador consulta el histórico para obtener contexto de adaptación. Este contexto incluye:

- Ejecuciones previas del mismo skill con inputs similares
- Keywords que han funcionado bien en el pasado
- Patrones de éxito/fracaso

La IA recibe este contexto como parte del prompt, lo que le permite:

1. Evitar errores cometidos en ejecuciones anteriores
2. Reforzar estrategias que funcionaron
3. Adaptar el tono y estilo según el historial
4. Reconocer keywords y temas recurrentes

### Consultar el histórico

Puedes consultar la base de datos directamente con SQLite:

```bash
sqlite3 outputs/seo_history.db "SELECT * FROM seo_executions ORDER BY created_at DESC LIMIT 10;"
sqlite3 outputs/seo_history.db "SELECT query, clicks, position FROM seo_keywords ORDER BY clicks DESC LIMIT 20;"
```

---

## 🌐 Integración con Proyectos Web

### Next.js (App Router)

El sistema está optimizado para proyectos Next.js con App Router. La estructura esperada es:

```
proyecto/
  app/
    frontend/
      app/
        page.tsx           → Ruta: /
        servicios/
          page.tsx         → Ruta: /servicios
        blog/
          [slug]/
            page.mdx       → Ruta: /blog/[slug]
      posts.ts             → Lista de posts (slug, title, etc.)
```

**Para contenido nuevo (Content Creator):**
1. La IA genera el slug, título y contenido MDX
2. El orquestador crea `app/frontend/app/blog/[slug]/page.mdx`
3. Si existe `posts.ts`, se actualiza con la nueva entrada
4. Se regenera el sitemap si el `sitemap_updater` está configurado

**Para auditorías (Site Auditor):**
1. La IA recibe el contenido actual del archivo
2. Devuelve el contenido corregido y optimizado
3. El orquestador sobrescribe el archivo físico
4. Los cambios se versionan con Git

### Express / Cualquier Backend

Si tienes un backend API, puedes enviar reportes y métricas configurando `BACKEND_API_URL`:

```bash
BACKEND_API_URL=http://tu-servidor:3001/api
```

Los endpoints que usa el sistema son:
- `POST /api/seo/reports` → Enviar reportes generados
- `POST /api/seo/metrics` → Enviar métricas de GA4/GSC

### Sitio Estático

Para sitios estáticos (HTML, Jekyll, Hugo, etc.):

1. El Content Creator genera el archivo Markdown/MDX
2. El Site Auditor modifica archivos HTML directamente
3. Git auto push se encarga de desplegar los cambios
4. Configura `FRONTEND_PATH` para apuntar al directorio correcto

---

## ➕ Cómo Agregar Más Sitios Web al Mismo Sistema

**ESTO ES CRUCIAL** — El sistema puede gestionar múltiples sitios web desde una sola instalación. Aquí tienes las tres opciones:

### Opción 1: Múltiples archivos .env (Recomendada)

Crea un archivo `.env` diferente para cada cliente y ejecuta el orquestador con ese archivo:

```bash
# Crear archivos de configuración por cliente
cp inputs/.env inputs/.env-cliente-a
cp inputs/.env inputs/.env-cliente-b

# Editar cada uno con sus respectivas credenciales
nano inputs/.env-cliente-a
nano inputs/.env-cliente-b

# Ejecutar para un cliente específico
env $(cat inputs/.env-cliente-a | xargs) python scripts/orchestrator.py monitor
```

### Opción 2: Instancias separadas del orquestador

Usa la clase `SEOOrchestrator` desde código Python con diferentes configuraciones:

```python
# scripts/multi_site_manager.py
import os
from dotenv import load_dotenv
from orchestrator import SEOOrchestrator

# Configuración de múltiples sitios
proyectos = [
    {
        "name": "Cliente A",
        "env_file": "inputs/.env-cliente-a",
        "schedule_time": "08:00"
    },
    {
        "name": "Cliente B",
        "env_file": "inputs/.env-cliente-b",
        "schedule_time": "09:00"
    },
    {
        "name": "Cliente C",
        "env_file": "inputs/.env-cliente-c",
        "schedule_time": "10:00"
    }
]

def ejecutar_cliente(proyecto):
    """Carga el entorno y ejecuta el monitoreo para un cliente."""
    load_dotenv(proyecto["env_file"], override=True)
    print(f"=== Ejecutando monitoreo para: {proyecto['name']} ===")
    
    orch = SEOOrchestrator()
    result = orch.automated_seo_monitoring()
    
    print(f"Resultado: {result['status']}")
    return result

# Ejecutar todos los clientes secuencialmente
for proyecto in proyectos:
    ejecutar_cliente(proyecto)

# O ejecutar en paralelo (con concurrent.futures)
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {executor.submit(ejecutar_cliente, p): p["name"] for p in proyectos}
    for future in futures:
        name = futures[future]
        try:
            future.result()
            print(f"✓ {name}: Completado")
        except Exception as e:
            print(f"✗ {name}: Error - {e}")
```

### Opción 3: Config JSON con múltiples proyectos

Crea un archivo de configuración centralizado:

```json
// config/proyectos.json
{
  "proyectos": [
    {
      "nombre": "Cliente A",
      "env": "inputs/.env-cliente-a",
      "schedule": {
        "monitoreo": "08:00",
        "auditoria": ["10:00", "22:00"]
      }
    },
    {
      "nombre": "Cliente B",
      "env": "inputs/.env-cliente-b",
      "schedule": {
        "monitoreo": "09:00",
        "auditoria": ["11:00", "23:00"]
      }
    }
  ]
}
```

Luego, un script centralizado lee esta configuración:

```python
import json
import schedule
import time
from dotenv import load_dotenv
from orchestrator import SEOOrchestrator

with open("config/proyectos.json") as f:
    config = json.load(f)

def ejecutar_proyecto(env_file):
    load_dotenv(env_file, override=True)
    orch = SEOOrchestrator()
    orch.automated_seo_monitoring()

for proyecto in config["proyectos"]:
    schedule.every().day.at(proyecto["schedule"]["monitoreo"]).do(
        ejecutar_proyecto, proyecto["env"]
    )

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## 🐳 Despliegue en Servidor (Docker)

### Usando Docker Compose

Crea un archivo `docker-compose.yml`:

```yaml
version: '3.8'

services:
  seo-agent:
    build: .
    container_name: seo-mcp-agent
    volumes:
      - ./inputs:/app/inputs
      - ./outputs:/app/outputs
      - ./config:/app/config
      - /ruta/a/tu/proyecto/web:/app/project:rw
    environment:
      - TZ=Europe/Madrid
    restart: unless-stopped
```

Construir y ejecutar:

```bash
docker compose build
docker compose up -d
```

Ver logs:

```bash
docker compose logs -f
```

### Dockerfile incluido

El proyecto ya incluye un `Dockerfile` que:

1. Usa Python 3.12-slim como base
2. Instala Git para auto push
3. Instala las dependencias Python
4. Crea los directorios inputs y outputs
5. Ejecuta el scheduler como comando por defecto

### Usando systemd (Linux VPS)

Para ejecutar como servicio del sistema en un VPS Linux:

```bash
# Crear archivo de servicio
sudo nano /etc/systemd/system/seo-mcp-agent.service
```

```ini
[Unit]
Description=SEO MCP Agent - Automated SEO Monitoring
After=network.target

[Service]
Type=simple
User=tu_usuario
WorkingDirectory=/ruta/a/seo-mcp-skill
ExecStart=/usr/bin/python3 scripts/orchestrator.py schedule
Restart=on-failure
RestartSec=30
StandardOutput=append:/ruta/a/seo-mcp-skill/outputs/scheduler.log
StandardError=append:/ruta/a/seo-mcp-skill/outputs/scheduler-error.log

[Install]
WantedBy=multi-user.target
```

```bash
# Habilitar e iniciar el servicio
sudo systemctl daemon-reload
sudo systemctl enable seo-mcp-agent
sudo systemctl start seo-mcp-agent

# Ver estado
sudo systemctl status seo-mcp-agent

# Ver logs en tiempo real
journalctl -u seo-mcp-agent -f
```

### Configuración para producción

Para un despliegue en producción, ten en cuenta:

1. **Volúmenes persistentes**: Monta `inputs/` y `outputs/` como volúmenes para no perder datos al actualizar
2. **Rotación de logs**: Configura logrotate para evitar que los logs llenen el disco
3. **Monitoreo del proceso**: Usa systemd para reinicio automático en caso de fallo
4. **Red**: Si usas MCP con Puppeteer, el contenedor necesita acceso a internet
5. **Memoria**: El scheduler consume ~150MB de RAM; el agente MCP puede consumir ~300MB

---

## 📤 Subir a GitHub

Para compartir o respaldar tu proyecto en GitHub:

```bash
cd /ruta/a/seo-mcp-skill

# Inicializar repositorio (si no lo has hecho)
git init

# Añadir todos los archivos (excepto los ignorados por .gitignore)
git add .

# Crear primer commit
git commit -m "Primer commit: SEO MCP Skill - Sistema completo de automatización SEO"

# Renombrar rama principal
git branch -M main

# Añadir repositorio remoto
git remote add origin https://github.com/tuusuario/seo-mcp-skill.git

# Subir
git push -u origin main
```

**Importante:** Revisa el `.gitignore` antes del primer commit. Asegúrate de que `inputs/.env`, `outputs/seo_history.db`, y `__pycache__/` estén ignorados.

---

## 📝 Cómo Registrar tu Proyecto

### 1. Crear repositorio en GitHub

1. Ve a [GitHub](https://github.com/) e inicia sesión
2. Haz clic en el botón "+" → "New repository"
3. Nombre: `seo-mcp-skill`
4. Descripción: "Sistema autónomo de auditoría, monitoreo y optimización SEO con IA + Google APIs + MCP"
5. Visibilidad: Público (recomendado) o Privado
6. No marques "Initialize with README" (ya tienes uno)
7. Haz clic en "Create repository"

### 2. Push del código

```bash
git remote add origin https://github.com/tuusuario/seo-mcp-skill.git
git push -u origin main
```

### 3. Configurar GitHub Pages (opcional)

Para tener documentación online:

1. Ve a Settings → Pages
2. Selecciona "Deploy from branch"
3. Branch: main, carpeta: /docs
4. Guarda
5. Crea un archivo `docs/index.md` con un resumen del README

### 4. Agregar LICENSE

Se recomienda MIT License:

```bash
curl -o LICENSE https://raw.githubusercontent.com/git/git/master/COPYING
# O mejor, crear el archivo manualmente:
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2026 Kerwyn Arias

Permission is hereby granted...
...
EOF
```

### 5. Promocionar

- Comparte en LinkedIn con hashtags: #SEO #Python #IA #MCP #MarketingDigital
- Publica en ProductHunt si es relevante
- Escribe un post técnico en Medium o Dev.to
- Comparte en comunidades de SEO y desarrollo

---

## 🛠️ Solución de Problemas

### Error: "OPENROUTER_API_KEY no encontrada"

**Causa:** Falta la API key en `inputs/.env`.

**Solución:**
```bash
cp config/.env.template inputs/.env
nano inputs/.env
# Añade OPENROUTER_API_KEY=tu_clave_real
```

### Error: "ModuleNotFoundError: No module named 'openai'"

**Causa:** Falta instalar dependencias.

**Solución:**
```bash
pip install -r requirements.txt
# Y específicamente para OpenRouter:
pip install openai
```

### Error: "google.auth.exceptions.DefaultCredentialsError"

**Causa:** Las rutas a los JSON de credenciales Google son incorrectas.

**Solución:**
```bash
# Verifica que el archivo existe
ls -la /ruta/a/tu/ga4-service-account.json

# Verifica la ruta en .env
grep CREDENTIALS_PATH inputs/.env
```

### Error: "GA4 Property ID not found"

**Causa:** El ID de propiedad GA4 es incorrecto o la cuenta de servicio no tiene acceso.

**Solución:**
1. Verifica el ID en Google Analytics (Admin → Configuración de propiedad)
2. Verifica que la cuenta de servicio tenga permisos de "Lector" en GA4
3. Espera 1-2 horas después de dar permisos (a veces tarda en propagarse)

### Error: "403 Permission denied" en GSC

**Causa:** La cuenta de servicio no tiene acceso al sitio en Google Search Console.

**Solución:**
1. Ve a [Google Search Console](https://search.google.com/search-console/)
2. Selecciona el sitio
3. Configuración → Usuarios y permisos
4. Añade el email de la service account
5. Asigna al menos "Lector"

### Error: "502 Bad Gateway" al usar OpenRouter

**Causa:** El modelo de OpenRouter puede estar caído o sobrecargado.

**Solución:** El sistema intenta automáticamente con modelos alternativos (fallback). Si el error persiste, espera unos minutos y vuelve a intentar.

### Error: "No se encontró archivo físico para /blog/..."

**Causa:** El sistema busca en `{PROJECT_PATH}/app/frontend/app/blog/{slug}/page.mdx` pero puede estar en otra ubicación.

**Solución:**
1. Verifica la ruta del proyecto en `PROJECT_PATH`
2. Ajusta la lógica en `orchestrator.py` si tu estructura de carpetas es diferente
3. O configura `FRONTEND_PATH` si el frontend está en un subdirectorio

### Error: "Git: fatal: not a git repository"

**Causa:** El directorio del proyecto no está inicializado como repositorio Git.

**Solución:**
```bash
cd /ruta/tu/proyecto
git init
git add .
git commit -m "init"
```

### Error: "sqlite3.OperationalError: no such table"

**Causa:** La base de datos no se ha inicializado correctamente.

**Solución:**
```bash
python -c "from scripts.history_client import SEOHistoryClient; SEOHistoryClient(); print('✓ DB inicializada')"
```

### Error: "schedule: no module named 'schedule'"

**Causa:** Falta la dependencia schedule.

**Solución:**
```bash
pip install schedule
```

### El sistema no envía notificaciones Telegram

**Causa:** `TELEGRAM_BOT_TOKEN` o `TELEGRAM_CHAT_ID` no están configurados o son incorrectos.

**Solución:**
1. Verifica las variables en `.env`
2. Prueba el bot manualmente:
   ```bash
   curl -s "https://api.telegram.org/bot<TU_TOKEN>/getMe"
   ```
3. Obtén el chat ID correcto:
   ```bash
   curl -s "https://api.telegram.org/bot<TU_TOKEN>/getUpdates"
   ```

### Los reportes se guardan vacíos o incompletos

**Causa:** El modelo de IA no está generando el output en el formato esperado.

**Solución:**
1. Verifica los logs en `outputs/seo_orchestrator.log`
2. Comprueba que el modelo soporte Function Calling (DeepSeek, Claude, GPT-4o sí; algunos modelos pequeños no)
3. Prueba con un modelo diferente en `openrouter_client.py`

### El sistema se ejecuta pero no modifica archivos

**Causa:** `PROJECT_PATH` no está configurado o apunta a un directorio incorrecto.

**Solución:**
```bash
# Verifica la ruta configurada
grep PROJECT_PATH inputs/.env

# Verifica que la ruta existe
ls -la /ruta/a/tu/proyecto
```

---

<p align="center">
  <strong>SEO MCP Skill</strong> — Creado por <strong>Kerwyn Arias</strong><br>
  <em>Sistema de Automatización SEO con Inteligencia Artificial</em><br>
  GitHub: <a href="https://github.com/tuusuario/seo-mcp-skill">github.com/tuusuario/seo-mcp-skill</a>
</p>
