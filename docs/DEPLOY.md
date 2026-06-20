# Guía de Despliegue — Servidor, Docker, CORS y Git Automático

> **Propósito:** Esta guía cubre todos los aspectos del despliegue del sistema SEO MCP Skill en producción: Docker Compose, systemd (VPS Linux), configuración de CORS en el backend, flujo Git automático desde el agente hasta el servidor productivo, webhooks, CI/CD, monitoreo, seguridad y resolución de problemas comunes.

---

## Índice

1. [Despliegue con Docker Compose](#1-despliegue-con-docker-compose)
2. [Despliegue con systemd (VPS Linux)](#2-despliegue-con-systemd-vps-linux)
3. [Configuración de CORS](#3-configuración-de-cors)
4. [Flujo Git Automático: Agent Push → Server Pull](#4-flujo-git-automático-agent-push--server-pull)
5. [Script de Git Pull (Server Side)](#5-script-de-git-pull-server-side)
6. [Webhook Endpoint (para recibir push de GitHub)](#6-webhook-endpoint-para-recibir-push-de-github)
7. [Ejemplo de CI/CD Completo](#7-ejemplo-de-cicd-completo)
8. [Monitoreo y Logs](#8-monitoreo-y-logs)
9. [Seguridad](#9-seguridad)
10. [Troubleshooting de Despliegue](#10-troubleshooting-de-despliegue)

---

## 1. Despliegue con Docker Compose

### Archivo docker-compose.yml completo

```yaml
# docker-compose.yml
# Despliegue del sistema SEO MCP Agent en producción
# Uso: docker compose up -d
version: '3.8'

services:
  seo-agent:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: seo-mcp-agent
    image: seo-mcp-agent:latest
    
    # Volúmenes: montan directorios locales para persistencia y acceso a datos
    volumes:
      # Configuración y credenciales (solo lectura por seguridad)
      - ./inputs:/app/inputs:ro
      
      # Salidas: reportes, logs, base de datos SQLite (lectura-escritura)
      - ./outputs:/app/outputs
      
      # Config compartida (contexto de empresa, reglas)
      - ./config:/app/config:ro
      
      # Prompts de IA (se pueden personalizar sin rebuild)
      - ./prompts:/app/prompts:ro
      
      # Schemas JSON de skills
      - ./skills:/app/skills:ro
      
      # ⚠️ PROYECTO WEB DEL CLIENTE
      # El agente necesita acceso de escritura para modificar archivos
      # (MDX, TSX, páginas web). Asegúrate de que el contenedor
      # tenga permisos de escritura en este directorio.
      - /var/www/tu-proyecto-web:/app/project:rw
    
    # Variables de entorno desde archivo .env
    env_file:
      - ./inputs/.env
    
    # Variables adicionales (no sensibles)
    environment:
      - TZ=Europe/Madrid
      - PYTHONUNBUFFERED=1  # Logs sin buffer para mejor debugging
    
    # Política de reinicio
    restart: unless-stopped
    
    # Comando por defecto: ejecuta el planificador de tareas
    command: python3 scripts/orchestrator.py schedule
    
    # Límites de recursos (opcional pero recomendado)
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
    
    # Healthcheck para monitorear que el proceso está vivo
    healthcheck:
      test: ["CMD-SHELL", "pgrep -f 'orchestrator.py schedule' || exit 1"]
      interval: 60s
      timeout: 10s
      retries: 3
      start_period: 30s

  # Opcional: servidor webhook para recibir push de GitHub
  # (solo si necesitas el flujo Git inverso)
  webhook-server:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: seo-mcp-webhook
    ports:
      - "9000:9000"
    volumes:
      - /var/www/tu-proyecto-web:/app/project:rw
      - ./scripts/webhook_server.py:/app/webhook_server.py:ro
      - ./inputs/.env:/app/inputs/.env:ro
    environment:
      - TZ=Europe/Madrid
      - WEBHOOK_PORT=9000
      - WEBHOOK_SECRET=tu_secreto_compartido
    restart: unless-stopped
    command: python3 webhook_server.py
    
    # Si el webhook necesita acceso al repo del proyecto
    volumes:
      - /var/www/tu-proyecto-web:/app/project:rw
      - ~/.ssh:/root/.ssh:ro  # Clave SSH para git pull
    
    depends_on:
      - seo-agent
```

### Construir y Ejecutar

```bash
# Construir la imagen
docker compose build

# Iniciar en segundo plano
docker compose up -d

# Verificar que el contenedor está corriendo
docker compose ps

# Ver logs en tiempo real
docker compose logs -f

# Detener
docker compose down

# Reconstruir tras cambios en requirements.txt o Dockerfile
docker compose build --no-cache
docker compose up -d
```

### Estructura de Directorios Esperada en el Servidor

```
/opt/seo-mcp-skill/           ← Raíz del proyecto SEO MCP Skill
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── inputs/
│   ├── .env                  ← Variables de entorno (NUNCA subir a Git)
│   └── credenciales-ga4.json ← Credenciales Google (NUNCA subir a Git)
├── outputs/                  ← Reportes, logs, SQLite
├── config/
│   ├── .env.template
│   └── context/
│       ├── empresa.md
│       ├── servicios.md
│       └── reglas.md
├── prompts/
│   ├── content-creator.md
│   ├── dashboard.md
│   └── site-auditor.md
├── skills/
│   ├── seo-content-creator.json
│   ├── seo-dashboard.json
│   └── seo-site-auditor.json
├── scripts/
│   ├── orchestrator.py
│   ├── openrouter_client.py
│   ├── git_auto_push.py
│   └── ...
└── docs/
    ├── ADAPTATION.md
    ├── DEPLOY.md
    └── TODO.md

/var/www/tu-proyecto-web/     ← Proyecto web del cliente (montado como volumen)
├── app/
│   └── frontend/
│       ├── app/
│       │   ├── page.tsx
│       │   ├── servicios/
│       │   │   └── page.tsx
│       │   └── blog/
│       │       └── [slug]/
│       │           └── page.mdx
│       └── posts.ts
├── package.json
└── .git/
```

### Configuración del Dockerfile

El `Dockerfile` incluido en el proyecto ya está listo para producción:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . .

# Crear directorios de entrada/salida
RUN mkdir -p inputs outputs

# Comando por defecto
CMD ["python3", "scripts/orchestrator.py", "schedule"]
```

**Notas importantes para producción:**
- No copies `inputs/.env` dentro de la imagen (usa volúmenes o `env_file`)
- No copies credenciales JSON dentro de la imagen (usa volúmenes)
- Si necesitas Node.js para MCP Puppeteer, añádelo al Dockerfile
- Considera usar una imagen más pequeña como `python:3.12-alpine` si no necesitas Git

---

## 2. Despliegue con systemd (VPS Linux)

Para servidores VPS donde no se usa Docker, puedes ejecutar el agente como un servicio del sistema.

### Crear el Archivo de Servicio

```bash
sudo nano /etc/systemd/system/seo-mcp-agent.service
```

```ini
[Unit]
Description=SEO MCP Agent — Automated SEO Monitoring and Optimization
Documentation=https://github.com/tuusuario/seo-mcp-skill
After=network.target network-online.target
Wants=network-online.target

[Service]
# Tipo: simple (el proceso principal es el que se ejecuta)
Type=simple

# Usuario del sistema (crear uno dedicado si es posible)
User=deploy
Group=deploy

# Directorio de trabajo
WorkingDirectory=/opt/seo-mcp-skill

# Comando a ejecutar
ExecStart=/usr/bin/python3 /opt/seo-mcp-skill/scripts/orchestrator.py schedule

# Archivo de variables de entorno
EnvironmentFile=/opt/seo-mcp-skill/inputs/.env

# Política de reinicio
Restart=always
RestartSec=30

# Límites de tiempo
TimeoutStartSec=60
TimeoutStopSec=30

# Límites de recursos (opcional)
CPUQuota=80%
MemoryMax=512M

# Logs
StandardOutput=append:/opt/seo-mcp-skill/outputs/systemd-stdout.log
StandardError=append:/opt/seo-mcp-skill/outputs/systemd-stderr.log

# Seguridad: evitar que el proceso escriba en directorios sensibles
ProtectSystem=full
ProtectHome=true
PrivateTmp=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

### Activar y Gestionar el Servicio

```bash
# Recargar systemd para que reconozca el nuevo servicio
sudo systemctl daemon-reload

# Habilitar el servicio (se inicia automáticamente al arrancar el sistema)
sudo systemctl enable seo-mcp-agent

# Iniciar el servicio ahora
sudo systemctl start seo-mcp-agent

# Verificar estado
sudo systemctl status seo-mcp-agent

# Logs en tiempo real
sudo journalctl -u seo-mcp-agent -f

# Últimos 50 logs
sudo journalctl -u seo-mcp-agent -n 50 --no-pager

# Detener
sudo systemctl stop seo-mcp-agent

# Reiniciar
sudo systemctl restart seo-mcp-agent

# Deshabilitar (no se inicia al arrancar)
sudo systemctl disable seo-mcp-agent

# Ver el contenido completo del servicio
sudo systemctl cat seo-mcp-agent
```

### Servicio para Múltiples Proyectos (Multi-Project)

Si gestionas varios proyectos con el multi-project runner, crea un servicio que ejecute el script runner en lugar del orquestador directamente:

```ini
[Unit]
Description=SEO MCP Multi-Project Runner
After=network.target

[Service]
Type=simple
User=deploy
WorkingDirectory=/opt/seo-mcp-skill
ExecStart=/usr/bin/python3 /opt/seo-mcp-skill/scripts/multi_project_runner.py
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
```

Pero lo más común es ejecutar el multi-project runner como un cron que se dispara varias veces al día:

```bash
# Editar crontab del usuario deploy
sudo crontab -u deploy -e

# Añadir estas líneas:
# Ejecutar multi-project runner a las 8:00, 14:00 y 22:00
0 8,14,22 * * * cd /opt/seo-mcp-skill && /usr/bin/python3 scripts/multi_project_runner.py >> outputs/cron.log 2>&1

# Ejecutar sólo un proyecto específico
30 6 * * * cd /opt/seo-mcp-skill && env $(cat inputs/.env-cliente-a | xargs) python3 scripts/orchestrator.py monitor >> outputs/cron-cliente-a.log 2>&1
```

---

## 3. Configuración de CORS

Cuando el agente SEO envía reportes y métricas a un backend web (Express, FastAPI, etc.), es necesario configurar CORS correctamente para permitir las peticiones.

### Express.js

```javascript
// backend/src/middleware/cors.ts
import cors from 'cors';

const corsOptions = {
  // Orígenes permitidos
  origin: [
    'https://tudominio.com',
    'https://admin.tudominio.com',
    'http://localhost:3000',           // Desarrollo
    'http://localhost:3001',           // Backend local
    'http://seo-agent:9000',           // Desde contenedor Docker (por nombre de servicio)
  ],
  
  // Métodos HTTP permitidos
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
  
  // Headers permitidos
  allowedHeaders: [
    'Content-Type',
    'Authorization',
    'X-SEO-Source',                    // Header personalizado: "python-orchestrator"
    'X-API-Key',
  ],
  
  // Headers expuestos al cliente
  exposedHeaders: ['X-Request-ID'],
  
  // Credenciales (cookies, auth headers)
  credentials: true,
  
  // Tiempo máximo de cache del preflight (en segundos)
  maxAge: 86400,                       // 24 horas
};

export default cors(corsOptions);
```

```javascript
// backend/src/app.ts — Aplicar CORS globalmente
import express from 'express';
import cors from 'cors';
import corsOptions from './middleware/cors';

const app = express();

// Middleware global
app.use(cors(corsOptions));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Opción más restrictiva: CORS solo para rutas SEO
const seoRouter = express.Router();
seoRouter.use(cors(corsOptions));
app.use('/api/seo', seoRouter);
```

### Endpoint para Recibir Datos SEO

```javascript
// backend/src/routes/seo.routes.ts
import { Router, Request, Response } from 'express';

const router = Router();

/**
 * POST /api/seo/reports
 * Recibe reportes SEO generados por el orquestador Python.
 * El agente Python envía estos datos tras cada ciclo de monitoreo.
 */
router.post('/reports', async (req: Request, res: Response) => {
  try {
    const {
      title,                // Título del reporte
      period_start,         // Fecha inicio del período
      period_end,           // Fecha fin del período
      summary,              // Resumen (primeros 2000 chars)
      full_report_path,     // Ruta local al archivo .md (opcional)
      full_report_text,     // Texto completo del reporte (opcional)
      skills_executed,      // Lista de skills ejecutadas
      ga4_organic_sessions, // Métrica GA4
      gsc_keywords_count,   // Total de keywords GSC
      execution_id,         // ID único de ejecución
      status,               // "success" | "error"
    } = req.body;

    // Validar datos requeridos
    if (!title || !summary) {
      return res.status(400).json({
        error: 'Datos incompletos',
        required: ['title', 'summary'],
      });
    }

    // Guardar en base de datos (ejemplo con Supabase)
    const { data, error } = await supabase
      .from('seo_reports')
      .insert({
        title,
        period_start,
        period_end,
        summary,
        full_report_text,
        skills_executed,
        ga4_organic_sessions,
        gsc_keywords_count,
        execution_id,
        source: req.headers['x-seo-source'] || 'unknown',
        created_at: new Date().toISOString(),
      })
      .select()
      .single();

    if (error) throw error;

    logger.info(`Reporte SEO recibido: ${title} (ID: ${data.id})`);

    return res.status(201).json({
      status: 'ok',
      id: data.id,
      message: 'Reporte almacenado correctamente',
    });
  } catch (error) {
    logger.error('Error guardando reporte SEO:', error);
    return res.status(500).json({
      error: 'Error interno del servidor',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

/**
 * POST /api/seo/metrics
 * Recibe métricas de GA4 y GSC para almacenamiento histórico.
 * Estos datos permiten construir dashboards de evolución temporal.
 */
router.post('/metrics', async (req: Request, res: Response) => {
  try {
    const metrics = req.body;
    
    // Las métricas pueden ser de diferentes tipos:
    // - ga4: sesiones orgánicas, usuarios, bounce rate
    // - gsc_keywords: lista de keywords con posición, clics, impresiones
    
    const { error } = await supabase
      .from('seo_metrics')
      .insert({
        ...metrics,
        received_at: new Date().toISOString(),
      });

    if (error) throw error;

    return res.json({ status: 'ok' });
  } catch (error) {
    logger.error('Error guardando métricas:', error);
    return res.status(500).json({ error: 'Error interno' });
  }
});

/**
 * POST /api/seo/content-queue
 * Recibe contenido generado por la IA para aprobación humana.
 */
router.post('/content-queue', async (req: Request, res: Response) => {
  try {
    const contentData = req.body;
    
    const { data, error } = await supabase
      .from('seo_content_queue')
      .insert({
        ...contentData,
        status: 'pending',   // pending → approved → published
        created_at: new Date().toISOString(),
      })
      .select()
      .single();

    if (error) throw error;

    // Notificar a los administradores (opcional)
    await notifyContentForApproval(data);

    return res.status(201).json({
      status: 'ok',
      id: data.id,
      message: 'Contenido en cola de aprobación',
    });
  } catch (error) {
    return res.status(500).json({ error: 'Error interno' });
  }
});

export default router;
```

### FastAPI (Python)

Si el backend está escrito en Python (FastAPI), la configuración de CORS es:

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SEO Reports API")

origins = [
    "https://tudominio.com",
    "http://localhost:3000",
    "http://localhost:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-SEO-Source"],
)

@app.post("/api/seo/reports")
async def receive_report(report: dict):
    # Guardar en base de datos
    return {"status": "ok", "id": 123}
```

---

## 4. Flujo Git Automático: Agent Push → Server Pull

El sistema implementa un flujo bidireccional de Git para mantener sincronizados el agente SEO y el servidor de producción.

### Arquitectura del Flujo

```
 ┌─────────────────────────────────────────────────────────┐
 │                   AGENTE SEO (Docker/VPS)                │
 │                                                         │
 │  08:00 → Monitoreo global (GA4 + GSC + Dashboard)      │
 │  10:00 → Auditoría por página + correcciones            │
 │  22:00 → Segunda auditoría del día                      │
 │                                                         │
 │  ┌──────────────────────────────────────────────┐       │
 │  │  Si hay cambios en archivos del proyecto:    │       │
 │  │                                              │       │
 │  │  1. git add .                                │       │
 │  │  2. git commit -m "auto: mejoras SEO [fecha]"│       │
 │  │  3. git push origin main                     │       │
 │  └──────────────────┬───────────────────────────┘       │
 └─────────────────────┼───────────────────────────────────┘
                       │
                       ▼
 ┌─────────────────────────────────────────────────────────┐
 │                 GITHUB / GITLAB / BITBUCKET              │
 │                                                         │
 │  Repositorio remoto (origin/main)                       │
 │  - Recibe push del agente SEO                           │
 │  - Dispara webhook al servidor productivo               │
 └─────────────────────┬───────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
 ┌──────────────┐ ┌────────┐ ┌──────────┐
 │  Opción A:   │ │Opción B│ │ Opción C │
 │  Webhook     │ │ Cron   │ │ Watch    │
 │  GitHub →    │ │ cada   │ │ inotify  │
 │  servidor    │ │ 30 min │ │ + pull   │
 │  POST        │ │ git    │ │ autom.   │
 │  /webhook/   │ │ pull   │ │          │
 │  git-pull    │ │        │ │          │
 └──────┬───────┘ └───┬────┘ └─────┬────┘
        │             │            │
        ▼             ▼            ▼
 ┌─────────────────────────────────────────────────────────┐
 │               SERVIDOR PRODUCTIVO                       │
 │                                                         │
 │  git pull origin main                                   │
 │  # Si el frontend cambió:                               │
 │  cd app/frontend && pnpm build                          │
 │  # Si Docker, rebuild:                                  │
 │  docker compose up -d --build                           │
 └─────────────────────────────────────────────────────────┘
```

### ¿Cuándo hace push el agente?

El agente hace push automático en estos momentos:

1. **Después del monitoreo global** (08:00) — si se generó un reporte
2. **Después de la auditoría por página** (10:00 y 22:00) — si se modificaron archivos
3. **Después de crear contenido nuevo** (bajo demanda)
4. **Después de actualizar el sitemap** (bajo demanda)

El código que lo gestiona está en `scripts/git_auto_push.py`:

```python
# Llamada en orchestrator.py (líneas 335-337):
git_status = self.git.get_status()
if git_status:
    self.git.commit_and_push(
        f"auto: SEO monitoring report {datetime.now().strftime('%Y-%m-%d')}"
    )
```

### Configuración del Remoto en el Agente

```bash
# En inputs/.env del agente SEO:
PROJECT_PATH=/var/www/tu-proyecto-web
REPO_REMOTE=https://github.com/tu-usuario/tu-repo.git
GIT_BRANCH=main
```

**Importante:** Si el repositorio es privado, necesitas configurar autenticación:

```bash
# Opción 1: Token de acceso personal (recomendado)
# Crear token en GitHub: Settings → Developer settings → Personal access tokens
# Luego configurar el remote:
git remote set-url origin https://TOKEN@github.com/tu-usuario/tu-repo.git

# Opción 2: SSH (si el agente tiene clave SSH configurada)
git remote set-url origin git@github.com:tu-usuario/tu-repo.git

# Opción 3: GitHub CLI (gh)
gh auth login
```

---

## 5. Script de Git Pull (Server Side)

En el servidor de producción, necesitas un script que haga `git pull` periódicamente para recibir los cambios que el agente SEO empujó a GitHub.

### Script Completo

```bash
#!/bin/bash
# ============================================================
# scripts/git-pull.sh
# Script de sincronización para el servidor productivo.
# Ejecuta git pull del repositorio y reconstruye si es necesario.
#
# Uso:
#   ./scripts/git-pull.sh                    # Pull normal
#   ./scripts/git-pull.sh --force            # Pull con force
#   ./scripts/git-pull.sh --rebuild-frontend # Pull + rebuild frontend
#   ./scripts/git-pull.sh --rebuild-docker   # Pull + rebuild Docker
#
# Uso típico en cron:
#   */30 * * * * /opt/seo-mcp-skill/scripts/git-pull.sh >> /var/log/git-pull.log 2>&1
# ============================================================

set -euo pipefail  # Salir en caso de error, variables no definidas, pipes rotos

# ============================================================
# CONFIGURACIÓN
# ============================================================
PROJECT_DIR="/var/www/tu-proyecto-web"
FRONTEND_DIR="$PROJECT_DIR/app/frontend"
LOG_FILE="/var/log/git-pull.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# ============================================================
# FUNCIONES
# ============================================================
log() {
    echo "[$TIMESTAMP] $1" | tee -a "$LOG_FILE"
}

error_exit() {
    echo "[$TIMESTAMP] ERROR: $1" | tee -a "$LOG_FILE" >&2
    exit 1
}

notify_telegram() {
    local message="$1"
    local bot_token="${TELEGRAM_BOT_TOKEN:-}"
    local chat_id="${TELEGRAM_CHAT_ID:-}"
    
    if [ -n "$bot_token" ] && [ -n "$chat_id" ]; then
        curl -s -X POST "https://api.telegram.org/bot$bot_token/sendMessage" \
            -d "chat_id=$chat_id" \
            -d "text=$message" \
            -d "parse_mode=HTML" > /dev/null 2>&1 || true
    fi
}

# ============================================================
# VERIFICACIONES PREVIAS
# ============================================================
log "Iniciando git-pull.sh..."

# Verificar que el directorio del proyecto existe
if [ ! -d "$PROJECT_DIR" ]; then
    error_exit "Directorio del proyecto no encontrado: $PROJECT_DIR"
fi

# Verificar que es un repositorio Git
if [ ! -d "$PROJECT_DIR/.git" ]; then
    error_exit "No es un repositorio Git: $PROJECT_DIR"
fi

# Ir al directorio del proyecto
cd "$PROJECT_DIR" || error_exit "No se pudo acceder a $PROJECT_DIR"

# ============================================================
# GUARDAR HASH ACTUAL
# ============================================================
BEFORE_HASH=$(git rev-parse HEAD)
log "Hash actual: $BEFORE_HASH"

# ============================================================
# GIT PULL
# ============================================================
log "Ejecutando: git pull origin main"

# Si hay cambios locales sin commit, stash temporalmente
if ! git diff --quiet; then
    log "Hay cambios locales sin commit. Guardando en stash..."
    git stash push -m "auto-stash antes de pull $(date '+%Y%m%d%H%M%S')"
    STASHED=true
else
    STASHED=false
fi

# Ejecutar git pull
if git pull origin main; then
    AFTER_HASH=$(git rev-parse HEAD)
    log "✓ Git pull exitoso"
    
    if [ "$BEFORE_HASH" != "$AFTER_HASH" ]; then
        log "✓ Nuevos cambios detectados: $BEFORE_HASH → $AFTER_HASH"
        CHANGES_DETECTED=true
    else
        log "No hay cambios nuevos (ya estaba actualizado)"
        CHANGES_DETECTED=false
    fi
else
    # Restaurar stash si hubo error
    if [ "$STASHED" = true ]; then
        git stash pop || true
    fi
    error_exit "Error en git pull. Revisa la conexión o conflictos."
fi

# Restaurar stash si se guardó
if [ "$STASHED" = true ]; then
    log "Restaurando cambios locales del stash..."
    git stash pop || true
fi

# ============================================================
# POST-PULL: RECONSTRUIR SI HUBO CAMBIOS
# ============================================================
if [ "$CHANGES_DETECTED" = true ]; then
    log "Iniciando post-pull: reconstrucción..."
    
    # Mostrar qué cambió (primeros 10 commits)
    log "Commits recibidos:"
    git log --oneline --no-decorate "$BEFORE_HASH..$AFTER_HASH" 2>/dev/null | head -10 | while read line; do
        log "  • $line"
    done
    
    # 1. Reconstruir frontend si existe pnpm y cambió el frontend
    if [ -f "$FRONTEND_DIR/package.json" ] && command -v pnpm &> /dev/null; then
        log "Reconstruyendo frontend Next.js..."
        cd "$FRONTEND_DIR"
        if pnpm build; then
            log "✓ Frontend reconstruido correctamente"
        else
            log "⚠ Error en build del frontend (puede ser por cambios parciales)"
        fi
    fi
    
    # 2. Reconstruir Docker si hay docker-compose
    if [ -f "$PROJECT_DIR/docker-compose.yml" ] && command -v docker &> /dev/null; then
        log "Reconstruyendo contenedores Docker..."
        cd "$PROJECT_DIR"
        if docker compose up -d --build 2>&1; then
            log "✓ Contenedores Docker reconstruidos"
        else
            log "⚠ Error reconstruyendo contenedores Docker"
        fi
    fi
    
    # 3. Limpiar cachés si aplica
    if [ -d "$FRONTEND_DIR/.next" ]; then
        log "Limpiando caché de Next.js..."
        rm -rf "$FRONTEND_DIR/.next/cache" 2>/dev/null || true
    fi
    
    # Notificar por Telegram
    notify_telegram "🔄 <b>Despliegue automático</b>

Repositorio actualizado: <code>$PROJECT_DIR</code>
Cambios: <code>$BEFORE_HASH..$AFTER_HASH</code>
Frontend: $( [ "$CHANGES_DETECTED" = true ] && echo '✅ Reconstruido' || echo '⚠ Sin cambios' )
Hora: $TIMESTAMP"

    log "✓ Post-pull completado"
else
    log "No hubo cambios, se omite reconstrucción."
fi

log "git-pull.sh finalizado correctamente."
exit 0
```

### Configuración del Script en el Servidor

```bash
# Hacer el script ejecutable
chmod +x /opt/seo-mcp-skill/scripts/git-pull.sh

# Probar manualmente
/opt/seo-mcp-skill/scripts/git-pull.sh

# Añadir al crontab para ejecución periódica
sudo crontab -e

# Cada 30 minutos (recomendado para recibir cambios SEO rápidamente)
*/30 * * * * /opt/seo-mcp-skill/scripts/git-pull.sh

# O cada hora en punto
0 * * * * /opt/seo-mcp-skill/scripts/git-pull.sh

# En momentos clave del día (antes de los picos de tráfico)
0 7 * * * /opt/seo-mcp-skill/scripts/git-pull.sh  # Antes de las 8
30 9 * * * /opt/seo-mcp-skill/scripts/git-pull.sh  # Antes de las 10
30 21 * * * /opt/seo-mcp-skill/scripts/git-pull.sh # Antes de las 22
```

---

## 6. Webhook Endpoint (para recibir push de GitHub)

Cuando GitHub Actions o un push directo al repositorio necesitan notificar al servidor productivo, un webhook HTTP es la opción más rápida (tiempo real).

### Servidor Webhook en Python (Flask)

```python
#!/usr/bin/env python3
"""
scripts/webhook_server.py
Servidor webhook que escucha peticiones POST de GitHub y ejecuta git pull.

Uso:
  python3 scripts/webhook_server.py

Variables de entorno:
  WEBHOOK_PORT=9000
  WEBHOOK_SECRET=tu_secreto_compartido
  PROJECT_PATH=/var/www/tu-proyecto-web
"""
import os
import sys
import hmac
import json
import hashlib
import subprocess
import logging
from flask import Flask, request, jsonify

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("WebhookServer")

# Configuración desde variables de entorno
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "9000"))
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
PROJECT_PATH = os.getenv("PROJECT_PATH", "/var/www/tu-proyecto-web")

app = Flask(__name__)


def verify_signature(payload_body: bytes, signature_header: str) -> bool:
    """
    Verifica la firma HMAC-SHA256 de GitHub para asegurar que la
    petición viene realmente de GitHub y no de un atacante.
    """
    if not WEBHOOK_SECRET:
        logger.warning("WEBHOOK_SECRET no configurado. Saltando verificación de firma.")
        return True

    if not signature_header:
        logger.error("Falta el header X-Hub-Signature-256")
        return False

    # GitHub envía: sha256=HEXDIGEST
    expected_prefix = "sha256="
    if not signature_header.startswith(expected_prefix):
        logger.error(f"Formato de firma inválido: {signature_header[:20]}...")
        return False

    expected_sig = signature_header[len(expected_prefix):]
    computed_sig = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        payload_body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(computed_sig, expected_sig)


@app.route('/webhook/git-pull', methods=['POST'])
def webhook_git_pull():
    """
    Endpoint principal del webhook.
    GitHub POSTea aquí cuando hay push al repositorio.
    """
    # 1. Verificar la firma de seguridad
    signature = request.headers.get('X-Hub-Signature-256', '')
    if not verify_signature(request.data, signature):
        logger.error("Firma inválida — posible ataque o configuración incorrecta")
        return jsonify({"error": "Firma inválida"}), 403

    # 2. Obtener información del evento
    event = request.headers.get('X-GitHub-Event', 'push')
    payload = request.json or {}

    branch = payload.get('ref', '')
    logger.info(f"Webhook recibido — Evento: {event}, Branch: {branch}")

    # Solo procesar pushes a main
    if event == 'push' and branch == 'refs/heads/main':
        # Extraer información del commit
        commits = payload.get('commits', [])
        if commits:
            logger.info(f"Commits recibidos: {len(commits)}")
            for c in commits[:5]:
                logger.info(f"  • {c.get('id', '')[:8]}: {c.get('message', '').split(chr(10))[0]}")

        # 3. Ejecutar git pull
        try:
            logger.info("Ejecutando git pull...")
            result = subprocess.run(
                ["git", "pull", "origin", "main"],
                cwd=PROJECT_PATH,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                logger.info(f"✓ Git pull exitoso: {result.stdout[:200]}")
                
                # 4. Reconstruir frontend si cambió
                rebuild_needed = any(
                    'app/frontend' in (c.get('modified', []) + c.get('added', []))
                    for c in commits
                )
                
                if rebuild_needed:
                    logger.info("Cambios detectados en frontend. Reconstruyendo...")
                    frontend_path = os.path.join(PROJECT_PATH, "app/frontend")
                    if os.path.exists(os.path.join(frontend_path, "package.json")):
                        build_result = subprocess.run(
                            ["pnpm", "build"],
                            cwd=frontend_path,
                            capture_output=True,
                            text=True,
                            timeout=300
                        )
                        if build_result.returncode == 0:
                            logger.info("✓ Frontend reconstruido exitosamente")
                        else:
                            logger.error(f"⚠ Error en build: {build_result.stderr[:200]}")
                
                return jsonify({
                    "status": "success",
                    "message": "Git pull ejecutado correctamente",
                    "output": result.stdout[:500],
                    "rebuild": rebuild_needed
                }), 200
            else:
                logger.error(f"Error en git pull: {result.stderr}")
                return jsonify({
                    "status": "error",
                    "message": result.stderr[:500]
                }), 500

        except subprocess.TimeoutExpired:
            logger.error("Timeout ejecutando git pull")
            return jsonify({"status": "error", "message": "Timeout"}), 504
        except Exception as e:
            logger.error(f"Error: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    else:
        # Ignorar otros eventos o branches
        logger.info(f"Evento ignorado: {event}, branch: {branch}")
        return jsonify({"status": "ignored", "event": event}), 200


@app.route('/health', methods=['GET'])
def health():
    """Health check para monitoreo."""
    project_exists = os.path.exists(PROJECT_PATH)
    is_git_repo = os.path.exists(os.path.join(PROJECT_PATH, ".git"))
    
    return jsonify({
        "status": "healthy",
        "project_path": PROJECT_PATH,
        "project_exists": project_exists,
        "is_git_repo": is_git_repo,
        "uptime": os.popen('uptime').read().strip()
    })


if __name__ == '__main__':
    logger.info(f"Iniciando servidor webhook en puerto {WEBHOOK_PORT}")
    logger.info(f"Proyecto: {PROJECT_PATH}")
    logger.info(f"Webhook secret: {'✓ Configurado' if WEBHOOK_SECRET else '⚠ No configurado'}")
    
    app.run(
        host='0.0.0.0',
        port=WEBHOOK_PORT,
        debug=False
    )
```

### Configurar el Webhook en GitHub

1. Ve a tu repositorio en GitHub
2. Settings → Webhooks → Add webhook
3. **Payload URL:** `https://tuservidor.com:9000/webhook/git-pull`
   - (o `http://tuservidor:9000/webhook/git-pull` si es interno)
4. **Content type:** `application/json`
5. **Secret:** El mismo valor que `WEBHOOK_SECRET` en tu `.env`
6. **Which events:** Just the push event
7. **Active:** ✓

### Ejecutar el Webhook como Servicio systemd

```ini
[Unit]
Description=SEO MCP Webhook Server
After=network.target

[Service]
Type=simple
User=deploy
WorkingDirectory=/opt/seo-mcp-skill
ExecStart=/usr/bin/python3 /opt/seo-mcp-skill/scripts/webhook_server.py
Restart=always
RestartSec=10
EnvironmentFile=/opt/seo-mcp-skill/inputs/.env

[Install]
WantedBy=multi-user.target
```

---

## 7. Ejemplo de CI/CD Completo

### GitHub Actions Workflow

```yaml
# .github/workflows/seo-deploy.yml
# Este workflow se ejecuta cuando hay push a main.
# Despliega los cambios del agente SEO en el servidor productivo.

name: SEO Deploy — Despliegue Automático

on:
  push:
    branches: [main]
  # También se puede ejecutar manualmente
  workflow_dispatch:

jobs:
  # ============================================================
  # JOB 1: VERIFICAR CALIDAD DEL CÓDIGO
  # ============================================================
  lint-and-validate:
    name: Verificar calidad del código
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Cache Python dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      # Verificar que los schemas JSON son válidos
      - name: Validate JSON schemas
        run: |
          for f in skills/*.json; do
            python3 -c "import json; json.loads(open('$f').read()); print(f'✓ $f válido')"
          done
      
      # Verificar que los prompts markdown tienen el formato correcto
      - name: Check prompt files
        run: |
          for f in prompts/*.md; do
            echo "✓ $f existe"
          done
      
      # Verificar sintaxis de Python
      - name: Check Python syntax
        run: |
          python3 -m py_compile scripts/*.py
          echo "✓ Todos los archivos Python compilan correctamente"

  # ============================================================
  # JOB 2: DESPLEGAR EN VPS DE PRODUCCIÓN
  # ============================================================
  deploy:
    name: Desplegar en VPS
    needs: lint-and-validate
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup SSH
        run: |
          # Crear directorio y archivo de clave SSH
          mkdir -p ~/.ssh
          echo "${{ secrets.VPS_SSH_KEY }}" > ~/.ssh/id_rsa
          chmod 600 ~/.ssh/id_rsa
          
          # Añadir host known_hosts
          ssh-keyscan -H ${{ secrets.VPS_HOST }} >> ~/.ssh/known_hosts
      
      - name: Deploy via SSH
        run: |
          # Conectar al VPS y ejecutar comandos de despliegue
          ssh ${{ secrets.VPS_USER }}@${{ secrets.VPS_HOST }} "
            set -e  # Salir en caso de error
            
            echo '=== INICIO DEL DESPLIEGUE ==='
            date
            
            # 1. Ir al directorio del proyecto SEO MCP Skill
            cd /opt/seo-mcp-skill
            
            # 2. Guardar estado actual
            BEFORE=\$(git rev-parse HEAD)
            echo \"Estado anterior: \$BEFORE\"
            
            # 3. Pull de los cambios
            echo 'Haciendo git pull...'
            git pull origin main
            
            AFTER=\$(git rev-parse HEAD)
            echo \"Estado nuevo: \$AFTER\"
            
            if [ \"\$BEFORE\" != \"\$AFTER\" ]; then
              echo '=== CAMBIOS DETECTADOS, RECONSTRUYENDO ==='
              
              # 4. Reconstruir Docker si existe docker-compose
              if [ -f docker-compose.yml ]; then
                echo 'Reconstruyendo contenedores Docker...'
                docker compose up -d --build
                echo 'Contenedores actualizados:'
                docker compose ps
              fi
              
              # 5. Si cambió requirements.txt, reconstruir imagen
              if git diff --name-only \$BEFORE \$AFTER | grep -q 'requirements.txt'; then
                echo 'Requirements cambiado. Forzando rebuild completo...'
                docker compose build --no-cache
                docker compose up -d
              fi
              
              # 6. Notificar éxito
              echo '=== DESPLIEGUE COMPLETADO ==='
            else
              echo 'No hay cambios nuevos. Despliegue omitido.'
            fi
            
            # 7. Verificar que el contenedor está corriendo
            echo ''
            echo '=== ESTADO DEL CONTENEDOR ==='
            docker inspect seo-mcp-agent --format 'Estado: {{.State.Status}} - Iniciado: {{.State.StartedAt}}' 2>/dev/null || echo 'Contenedor no encontrado'
            
            echo ''
            echo '=== LOGS RECIENTES ==='
            docker logs seo-mcp-agent --tail 20 2>/dev/null || echo 'Sin logs disponibles'
            
            echo ''
            echo '=== DESPLIEGUE FINALIZADO ==='
          "
      
      - name: Health Check
        run: |
          # Esperar a que el contenedor se reinicie
          sleep 10
          
          # Verificar que el agente está corriendo vía SSH
          ssh ${{ secrets.VPS_USER }}@${{ secrets.VPS_HOST }} "
            if docker ps --format '{{.Names}}' | grep -q 'seo-mcp-agent'; then
              echo '✓ Contenedor seo-mcp-agent está corriendo'
              exit 0
            else
              echo '✗ Contenedor no encontrado'
              exit 1
            fi
          "
      
      - name: Notify Success
        if: success()
        run: |
          curl -s -X POST "https://api.telegram.org/bot${{ secrets.TELEGRAM_BOT_TOKEN }}/sendMessage" \
            -d "chat_id=${{ secrets.TELEGRAM_CHAT_ID }}" \
            -d "text=🚀 <b>Despliegue SEO Exitoso</b>
          
          Repositorio: \${{ github.repository }}
          Commit: <code>\${{ github.sha }}</code>
          Branch: main
          Autor: \${{ github.actor }}
          Hora: $(date '+%Y-%m-%d %H:%M:%S')" \
            -d "parse_mode=HTML" || true
      
      - name: Notify Failure
        if: failure()
        run: |
          curl -s -X POST "https://api.telegram.org/bot${{ secrets.TELEGRAM_BOT_TOKEN }}/sendMessage" \
            -d "chat_id=${{ secrets.TELEGRAM_CHAT_ID }}" \
            -d "text=❌ <b>Despliegue SEO FALLIDO</b>
          
          Repositorio: \${{ github.repository }}
          Commit: <code>\${{ github.sha }}</code>
          Error durante el despliegue automático.
          Revisa los logs en GitHub Actions." \
            -d "parse_mode=HTML" || true

  # ============================================================
  # JOB 3: POST-DEPLOY (opcional)
  # ============================================================
  post-deploy:
    name: Verificación post-despliegue
    needs: deploy
    runs-on: ubuntu-latest
    if: success()
    steps:
      - name: Check project health
        run: |
          ssh ${{ secrets.VPS_USER }}@${{ secrets.VPS_HOST }} "
            echo '=== VERIFICACIÓN POST-DESPLIEGUE ==='
            
            # Verificar logs del agente
            echo 'Últimas líneas del log del agente:'
            tail -5 /opt/seo-mcp-skill/outputs/seo_orchestrator.log 2>/dev/null || echo 'Log no disponible'
            
            # Verificar que el sitemap del proyecto se generó
            echo ''
            echo 'Verificando proyecto web...'
            if [ -f /var/www/tu-proyecto-web/app/frontend/.next/sitemap.xml ]; then
              echo '✓ Sitemap encontrado'
            else
              echo '⚠ Sitemap no encontrado (puede generarse en el próximo build)'
            fi
            
            echo ''
            echo '=== VERIFICACIÓN COMPLETADA ==='
          "
```

### Secrets Necesarios en GitHub

| Secret | Descripción |
|---|---|
| `VPS_HOST` | IP o dominio del VPS (ej: `123.456.789.0`) |
| `VPS_USER` | Usuario SSH (ej: `deploy`) |
| `VPS_SSH_KEY` | Clave privada SSH (contenido completo del archivo) |
| `TELEGRAM_BOT_TOKEN` | Token del bot de Telegram para notificaciones |
| `TELEGRAM_CHAT_ID` | ID del chat para notificaciones |

---

## 8. Monitoreo y Logs

### Logs del Agente (Docker)

```bash
# Logs en tiempo real
docker logs seo-mcp-agent -f

# Últimas 50 líneas
docker logs seo-mcp-agent --tail 50

# Logs con timestamps
docker logs seo-mcp-agent -t

# Desde una hora específica
docker logs seo-mcp-agent --since 2026-06-20T08:00:00

# Logs de las últimas 2 horas
docker logs seo-mcp-agent --since 2h

# Buscar errores en logs
docker logs seo-mcp-agent 2>&1 | grep -i error

# Logs del webhook (si está desplegado)
docker logs seo-mcp-webhook -f
```

### Logs del Servicio systemd

```bash
# Logs en tiempo real
journalctl -u seo-mcp-agent -f

# Últimas 100 líneas
journalctl -u seo-mcp-agent -n 100

# Logs de hoy
journalctl -u seo-mcp-agent --since today

# Logs de un rango de fechas
journalctl -u seo-mcp-agent --since "2026-06-20 08:00" --until "2026-06-20 10:00"

# Logs con prioridad (0=emerg, 3=error, 6=info)
journalctl -u seo-mcp-agent -p 3

# Ver tamaño de los logs
journalctl -u seo-mcp-agent --disk-usage

# Rotar logs (mantener solo 100MB)
sudo journalctl --vacuum-size=100M
```

### Archivos de Log del Propio Sistema

```
outputs/
├── seo_orchestrator.log          # Log principal del orquestador
├── seo_history.db                # Base de datos SQLite (auto-aprendizaje)
├── multi_runner.log              # Log del multi-project runner
├── systemd-stdout.log            # Stdout del servicio systemd
├── systemd-stderr.log            # Stderr del servicio systemd
└── cron.log                      # Log de ejecuciones cron
```

### Reportes Generados

```
outputs/
├── 20260620_reporte_automatico.md       # Reporte de monitoreo global
├── 20260621_reporte_automatico.md       # ...
├── 20260620_revision_blog_mi-articulo.md # Auditoría por página
├── 20260620_articulo_keyword-slug.md     # Nuevo contenido creado
└── multi_run_20260620_080000.json        # Resultados multi-project
```

### Verificar que el Agente está Funcionando

```bash
# Docker: verificar healthcheck
docker inspect seo-mcp-agent --format '{{.State.Health.Status}}'

# systemd: ver estado
systemctl is-active seo-mcp-agent

# Verificar procesos
pgrep -f 'orchestrator.py schedule'

# Verificar que el scheduler está ejecutando tareas
grep "Tareas automáticas programadas" outputs/seo_orchestrator.log

# Ver el último reporte generado
ls -lt outputs/*reporte* | head -5
```

### Dashboard de Monitoreo (Opcional)

Puedes construir un dashboard simple con los datos que el agente envía al backend:

```sql
-- Consultas útiles para tu panel de administración
-- (Asumiendo que almacenas los reportes en Supabase/PostgreSQL)

-- Últimos 7 reportes
SELECT title, period_start, period_end, created_at
FROM seo_reports
ORDER BY created_at DESC
LIMIT 7;

-- Evolución de sesiones orgánicas (últimos 30 días)
SELECT created_at::date, ga4_organic_sessions
FROM seo_reports
WHERE created_at >= NOW() - INTERVAL '30 days'
ORDER BY created_at;

-- Promedio de keywords por reporte
SELECT AVG(gsc_keywords_count) as avg_keywords
FROM seo_reports;

-- Skills más ejecutadas
SELECT unnest(skills_executed) as skill, COUNT(*) as veces
FROM seo_reports
GROUP BY skill
ORDER BY veces DESC;
```

---

## 9. Seguridad

### Reglas de Oro

1. **NUNCA** subir `inputs/.env` al repositorio (ya está en `.gitignore`)
2. **NUNCA** subir archivos JSON de credenciales Google (ya está en `.gitignore`)
3. **NUNCA** exponer puertos del webhook a internet sin autenticación
4. **SIEMPRE** usar HTTPS en producción
5. **SIEMPRE** rotar API keys periódicamente

### Lista de Verificación de Seguridad

| Aspecto | Recomendación | Riesgo si no se hace |
|---|---|---|
| `.gitignore` | Verificar que excluye `.env`, `*.json` de creds, `__pycache__/`, `*.db` | Filtración de API keys en GitHub |
| Permisos `inputs/` | `chmod 600 inputs/.env` | Cualquier usuario del sistema lee credenciales |
| Webhook secret | Configurar `WEBHOOK_SECRET` | Cualquiera puede disparar git pull malicioso |
| HTTPS | Usar nginx reverse proxy con SSL | Credenciales en texto plano |
| Firewall | Solo abrir puertos necesarios (3000, 3001, 80, 443) | Ataques a servicios internos |
| Actualizaciones | `pip install --upgrade` periódico | Vulnerabilidades conocidas |
| Logs sensibles | No loguear API keys ni tokens | Exposición en sistemas de logging |
| Rotación de keys | Cada 90 días | Keys comprometidas no detectadas |
| Límites de API | Configurar alerts de uso | Facturas inesperadas |
| Backups | `outputs/seo_history.db` debe respaldarse | Pérdida del histórico de aprendizaje |

### Configuración de Firewall (UFW)

```bash
# En el servidor VPS
sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH
sudo ufw allow ssh

# HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Webhook (solo desde GitHub IPs, si es posible)
sudo ufw allow from 192.30.252.0/22 to any port 9000  # GitHub webhook IPs
sudo ufw allow from 185.199.108.0/22 to any port 9000  # GitHub Pages
sudo ufw allow from 140.82.112.0/20 to any port 9000   # GitHub API

# Aplicar
sudo ufw enable
sudo ufw status verbose
```

### Nginx Reverse Proxy (para el webhook)

```nginx
# /etc/nginx/sites-available/seo-webhook
server {
    listen 443 ssl;
    server_name webhook.tudominio.com;

    ssl_certificate /etc/letsencrypt/live/webhook.tudominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/webhook.tudominio.com/privkey.pem;

    location /webhook/git-pull {
        proxy_pass http://127.0.0.1:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout largo porque git pull puede tardar
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }

    location /health {
        proxy_pass http://127.0.0.1:9000;
        proxy_set_header Host $host;
    }
}
```

---

## 10. Troubleshooting de Despliegue

### El contenedor Docker se reinicia constantemente

```
$ docker ps
CONTAINER STATUS: restarting (menos de 1 segundo)
```

**Causas posibles:**
- Error al cargar `.env` (falta variable obligatoria)
- Puerto ocupado
- Error de permisos en volúmenes montados

**Soluciones:**
```bash
# Ver logs para identificar el error
docker logs seo-mcp-agent --tail 50

# Probar ejecución interactiva
docker run -it --rm \
  -v $(pwd)/inputs:/app/inputs:ro \
  -v $(pwd)/outputs:/app/outputs \
  --env-file inputs/.env \
  seo-mcp-agent \
  python3 scripts/orchestrator.py test-openrouter

# Verificar permisos del volumen del proyecto
ls -la /var/www/tu-proyecto-web
# Asegurar que el contenedor pueda escribir (UID 1000 normalmente)
sudo chown -R 1000:1000 /var/www/tu-proyecto-web
```

### Error: "Permission denied" al escribir en el proyecto

```
OSError: [Errno 13] Permission denied: '/app/project/app/frontend/app/page.tsx'
```

**Causa:** El contenedor Docker no tiene permisos de escritura en el directorio del proyecto.

**Solución:**
```bash
# Ajustar permisos del proyecto
sudo chown -R 1000:1000 /var/www/tu-proyecto-web
# O dar permisos 777 (menos seguro)
sudo chmod -R 777 /var/www/tu-proyecto-web

# O ejecutar el contenedor con el mismo UID que el usuario del host
docker compose run --user $(id -u):$(id -g) seo-mcp-agent ...
```

### Error: "Git: fatal: not a git repository"

**Causa:** El directorio del proyecto no está inicializado como repositorio Git, o no se montó correctamente.

**Solución:**
```bash
# En el servidor host
cd /var/www/tu-proyecto-web
git init
git remote add origin https://github.com/tu-usuario/tu-repo.git
git add .
git commit -m "init"
git push -u origin main

# Verificar que el contenedor puede ver el .git
docker exec seo-mcp-agent ls -la /app/project/.git
```

### Error: "OpenRouter API key not found"

**Causa:** El archivo `.env` no se está cargando correctamente en el contenedor.

**Solución:**
```bash
# Verificar que el archivo .env existe y tiene la key
cat inputs/.env | grep OPENROUTER

# Verificar que el volumen está montado correctamente
docker exec seo-mcp-agent cat /app/inputs/.env | grep OPENROUTER

# Si está vacío, el volumen :ro puede estar mal
# Probar con :rw temporalmente
```

### El webhook no recibe peticiones de GitHub

**Causas posibles:**
- Puerto no accesible desde internet
- Firewall bloqueando
- SSL no configurado (GitHub requiere HTTPS para webhooks externos)

**Soluciones:**
```bash
# Verificar que el servidor webhook está escuchando
curl -s http://localhost:9000/health

# Verificar que el puerto está abierto
sudo lsof -i :9000

# Probar desde fuera del servidor (en tu máquina local)
curl -s https://tuservidor.com:9000/health

# Para desarrollo local, usa smee.io para tunelizar
# https://smee.io
npx smee --url https://smee.io/tu-id --path /webhook/git-pull --port 9000
```

### El agente hace push pero el servidor de producción no se actualiza

**Causas:**
- El cron de git-pull no está configurado
- El webhook falla
- Conflictos de Git en el servidor

**Soluciones:**

```bash
# Verificar que el cron está activo
sudo crontab -l | grep git-pull

# Ejecutar git-pull manualmente en el servidor
sudo /opt/seo-mcp-skill/scripts/git-pull.sh

# Si hay conflictos, resolverlos
cd /var/www/tu-proyecto-web
git status
git merge --abort  # Si hay merge conflict, abortar
git reset --hard origin/main  # Forzar estado remoto (¡cuidado! pierde cambios locales)

# Verificar logs del webhook
sudo journalctl -u seo-mcp-webhook -n 50
```

### Error: "ModuleNotFoundError: No module named 'openai'"

**Causa:** Las dependencias Python no se instalaron en la imagen Docker.

**Solución:**
```bash
# Reconstruir la imagen desde cero
docker compose build --no-cache

# O reconstruir y forzar reinstalación
docker compose build --no-cache --pull

# Verificar que requirements.txt está actualizado
cat requirements.txt
```

### La base de datos SQLite se corrompe

**Causa:** La base de datos SQLite se almacena en `outputs/` y puede corromperse si el contenedor se detiene abruptamente.

**Solución:**
```bash
# Verificar integridad
docker exec seo-mcp-agent sqlite3 /app/outputs/seo_history.db "PRAGMA integrity_check;"

# Hacer backup periódico
0 3 * * * docker exec seo-mcp-agent sqlite3 /app/outputs/seo_history.db ".backup /app/outputs/backups/seo_history_$(date +\%Y\%m\%d).db"

# Restaurar desde backup
docker exec seo-mcp-agent sqlite3 /app/outputs/seo_history.db ".restore /app/outputs/backups/seo_history_20260620.db"
```

### Error de memoria: "Killed" o "OOM"

**Causa:** El agente se queda sin memoria RAM, especialmente cuando ejecuta el Universal SEO Agent con Puppeteer.

**Solución:**
```bash
# 1. Aumentar límites de memoria en docker-compose.yml
deploy:
  resources:
    limits:
      memory: 1G  # Aumentar de 512M a 1G o 2G

# 2. Añadir swap al servidor
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 3. Deshabilitar el agente universal si no se usa
# (asegurarse de que RUN_UNIVERSAL_AGENT no esté configurado)
```

---

> **Documento de referencia para despliegue en producción** — SEO MCP Skill
> Versión: 1.0 — Junio 2026
> Próxima revisión recomendada: cada 6 meses o al cambiar la infraestructura
