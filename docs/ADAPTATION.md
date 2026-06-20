# Guía de Adaptación — Cómo Personalizar SEO MCP Skill para Cada Proyecto

> **Propósito:** Esta guía explica cómo adaptar el sistema SEO MCP Skill para gestionar múltiples proyectos web, personalizar skills existentes, agregar nuevas capacidades, cambiar el modelo de IA y ajustar los prompts según el nicho de cada cliente.

---

## Índice

1. [Estructura Multi-Proyecto](#1-estructura-multi-proyecto)
2. [Archivos a Modificar por Proyecto](#2-archivos-a-modificar-por-proyecto)
3. [Cómo Agregar un Skill Nuevo](#3-cómo-agregar-un-skill-nuevo)
4. [Cómo Cambiar el Modelo de IA](#4-cómo-cambiar-el-modelo-de-ia)
5. [Cómo Adaptar los Prompts para Diferentes Nichos](#5-cómo-adaptar-los-prompts-para-diferentes-nichos)
6. [Variables de Entorno por Proyecto](#6-variables-de-entorno-por-proyecto)
7. [Ejemplo Completo: Adaptar para una Inmobiliaria](#7-ejemplo-completo-adaptar-para-una-inmobiliaria)

---

## 1. Estructura Multi-Proyecto

El sistema está diseñado para gestionar múltiples sitios web desde una sola instalación. Existen tres enfoques según la escala y necesidades operativas.

### Opción A: Variables de Entorno Separadas (Recomendada para ≤10 proyectos)

Cada cliente tiene su propio archivo `.env` dentro del directorio `inputs/`. El orquestador carga el archivo correspondiente según el proyecto que se quiera ejecutar.

```bash
# Desde la raíz del proyecto SEO MCP Skill
cp config/.env.template inputs/.env-cliente-a  # Editar con datos del cliente A
cp config/.env.template inputs/.env-cliente-b  # Editar con datos del cliente B
cp config/.env.template inputs/.env-cliente-c  # Editar con datos del cliente C

# Ejecutar para un cliente específico
env $(cat inputs/.env-cliente-a | xargs) python scripts/orchestrator.py monitor
```

**Ventajas:**
- Aislamiento total entre proyectos
- Cada cliente tiene sus propias API keys, rutas y configuraciones
- Fácil de auditar y depurar
- No requiere modificar código

**Desventajas:**
- Ejecución manual o con scripts wrapper
- No hay programación centralizada de horarios

### Opción B: Script Runner Multi-Proyecto (Recomendada para 10-50 proyectos)

Un script Python centralizado itera sobre una lista de proyectos, carga el entorno de cada uno y ejecuta el orquestador secuencial o paralelamente.

```python
# scripts/multi_project_runner.py
"""
Ejecuta el monitoreo SEO para múltiples proyectos desde un solo punto de entrada.
Uso: python scripts/multi_project_runner.py
"""
import os
import json
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('outputs/multi_runner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def ejecutar_proyecto(proyecto: dict) -> dict:
    """
    Carga el entorno de un proyecto y ejecuta el monitoreo SEO completo.
    
    Args:
        proyecto: Diccionario con nombre y ruta al archivo .env.
    
    Returns:
        Diccionario con nombre, estado y timestamp.
    """
    env_file = proyecto["env"]
    if not os.path.exists(env_file):
        logger.error(f"Archivo .env no encontrado: {env_file}")
        return {"nombre": proyecto["nombre"], "status": "error", "error": "env_not_found"}
    
    load_dotenv(env_file, override=True)
    logger.info(f"=== Ejecutando: {proyecto['nombre']} ===")
    
    try:
        from orchestrator import SEOOrchestrator
        orch = SEOOrchestrator()
        resultado = orch.automated_seo_monitoring()
        logger.info(f"✓ {proyecto['nombre']}: {resultado.get('status', 'ok')}")
        return {
            "nombre": proyecto["nombre"],
            "status": resultado.get("status", "success"),
            "report_path": resultado.get("report_path"),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"✗ {proyecto['nombre']}: {e}")
        return {"nombre": proyecto["nombre"], "status": "error", "error": str(e)}


def ejecutar_todos_secuencial(proyectos: list) -> list:
    """Ejecuta proyectos uno tras otro."""
    resultados = []
    for p in proyectos:
        resultados.append(ejecutar_proyecto(p))
    return resultados


def ejecutar_todos_paralelo(proyectos: list, max_workers: int = 3) -> list:
    """Ejecuta proyectos en paralelo con un límite de workers."""
    resultados = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futuros = {executor.submit(ejecutar_proyecto, p): p["nombre"] for p in proyectos}
        for futuro in as_completed(futuros):
            nombre = futuros[futuro]
            try:
                resultado = futuro.result()
                resultados.append(resultado)
                logger.info(f"Completado: {nombre} → {resultado['status']}")
            except Exception as e:
                logger.error(f"Fallo: {nombre} → {e}")
                resultados.append({"nombre": nombre, "status": "error", "error": str(e)})
    return resultados


def guardar_resultados(resultados: list):
    """Persiste los resultados en un archivo JSON para auditoría."""
    path = f"outputs/multi_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(path, "w") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    logger.info(f"Resultados guardados en: {path}")


# ============================================================
# CONFIGURACIÓN: Lista de proyectos
# ============================================================
# Agrega aquí todos los proyectos que quieras monitorear.
# Cada proyecto necesita su propio archivo .env en inputs/
# con las variables de entorno correspondientes.
# ============================================================
proyectos = [
    {"nombre": "E-commerce Tech",       "env": "inputs/.env-ecommerce"},
    {"nombre": "Seguros Leads",         "env": "inputs/.env-seguros"},
    {"nombre": "Inmobiliaria Premium",  "env": "inputs/.env-inmobiliaria"},
    {"nombre": "Blog Salud",            "env": "inputs/.env-salud"},
    {"nombre": "Consultoría Legal",     "env": "inputs/.env-legal"},
]

if __name__ == "__main__":
    logger.info(f"Iniciando ejecución multi-proyecto: {len(proyectos)} proyectos")
    
    # Elegir modo:
    resultados = ejecutar_todos_secuencial(proyectos)
    # resultados = ejecutar_todos_paralelo(proyectos, max_workers=3)
    
    guardar_resultados(resultados)
    
    # Resumen
    exitosos = sum(1 for r in resultados if r["status"] == "success")
    fallidos = sum(1 for r in resultados if r["status"] == "error")
    logger.info(f"Resumen: {exitosos} exitosos, {fallidos} fallidos de {len(resultados)} totales")
```

**Ventajas:**
- Horarios centralizados
- Ejecución paralela opcional
- Logging unificado con resultados persistentes
- Fácil de integrar con cron o systemd

### Opción C: Docker con Volúmenes Separados (Recomendada para producción aislada)

Cada proyecto se ejecuta en su propio contenedor Docker con volúmenes montados específicos.

```yaml
# docker-compose.multi.yml
# Ejecutar: docker compose -f docker-compose.multi.yml up -d
version: '3.8'

services:
  seo-ecommerce:
    build: .
    container_name: seo-mcp-ecommerce
    volumes:
      - ./inputs/.env-ecommerce:/app/inputs/.env:ro
      - /var/www/ecommerce:/app/project:rw
      - ./outputs/ecommerce:/app/outputs
      - ./config:/app/config:ro
    environment:
      - TZ=Europe/Madrid
    restart: unless-stopped
    command: python3 scripts/orchestrator.py schedule

  seo-seguros:
    build: .
    container_name: seo-mcp-seguros
    volumes:
      - ./inputs/.env-seguros:/app/inputs/.env:ro
      - /var/www/seguros:/app/project:rw
      - ./outputs/seguros:/app/outputs
      - ./config:/app/config:ro
    environment:
      - TZ=Europe/Madrid
    restart: unless-stopped
    command: python3 scripts/orchestrator.py schedule

  seo-inmobiliaria:
    build: .
    container_name: seo-mcp-inmobiliaria
    volumes:
      - ./inputs/.env-inmobiliaria:/app/inputs/.env:ro
      - /var/www/inmobiliaria:/app/project:rw
      - ./outputs/inmobiliaria:/app/outputs
      - ./config:/app/config:ro
    environment:
      - TZ=Europe/Madrid
    restart: unless-stopped
    command: python3 scripts/orchestrator.py schedule
```

**Ventajas:**
- Aislamiento completo entre proyectos
- Cada contenedor tiene sus propios recursos y logs
- Fácil escalado (Kubernetes, Docker Swarm)
- Actualizaciones independientes

---

## 2. Archivos a Modificar por Proyecto

Cada proyecto requiere personalizar varios archivos. La siguiente tabla detalla qué cambiar y cómo.

| Archivo | Qué cambiar | Ejemplo de modificación |
|---|---|---|
| `inputs/.env` | API keys, rutas, URLs del proyecto, credenciales GA4/GSC | `PROJECT_PATH=/var/www/cliente-a` |
| `config/context/empresa.md` | Descripción del negocio, tono de comunicación, keywords principales, competidores | Cambiar de "tienda tech" a "comparador seguros" |
| `config/context/servicios.md` | Servicios/productos reales del cliente, beneficios, precios, preguntas frecuentes | Listar los 5 servicios principales con keywords |
| `config/context/reglas.md` | Reglas de contenido específicas por cliente (tono, longitud, formato, restricciones) | "Tono formal y profesional" vs "Tono cercano y divertido" |
| `prompts/content-creator.md` | Ajustar tono, ejemplos, triggers y referencias al nicho del proyecto | Personalizar la sección de triggers y el ejemplo de invocación |
| `prompts/site-auditor.md` | Adaptar las reglas de auditoría al framework y estructura del proyecto | Ajustar rutas de archivos si no es Next.js |
| `prompts/dashboard.md` | Personalizar métricas relevantes para el nicho del proyecto | Para lead-gen: añadir métricas de conversión |
| `skills/seo-content-creator.json` | (Opcional) Añadir campos requeridos específicos del proyecto | template_id, categoría, autor |
| `skills/seo-dashboard.json` | (Opcional) Añadir campos específicos de reporting | ROI estimado, leads generados |
| `skills/seo-site-auditor.json` | (Opcional) Añadir parámetros de auditoría específicos | framework_version, plugins_activos |

### Personalización de context/empresa.md

Este archivo es el más importante para la calidad del contenido generado. Debe rellenarse completamente:

```markdown
# Contexto de Empresa — Cliente: Inmobiliaria Premium Madrid

## Descripción de la Empresa
Inmobiliaria Premium Madrid es una agencia inmobiliaria boutique especializada en
viviendas de lujo en las zonas de Salamanca, Chamberí,Retiro y La Moraleja.
Ofrecemos compraventa, alquiler y asesoramiento integral a clientes nacionales
e internacionales con un patrimonio superior a 500.000€.

## Sitio Web
- **URL:** https://inmobiliariapremium.es/
- **Tecnología:** Next.js 16 con App Router
- **CMS:** Headless (archivos MDX)
- **Framework CSS:** Tailwind v4
- **Despliegue:** Docker en VPS con Cloudflare

## Mercado Objetivo
- **Ámbito geográfico:** Madrid capital y zona noroeste
- **Segmento demográfico:** 35-65 años, alto poder adquisitivo
- **Principales necesidades:** Encontrar vivienda de lujo, vender propiedades rápido,
  asesoramiento fiscal y legal, inversión inmobiliaria
- **Nivel de conocimiento:** Alto (clientes experimentados)

## Tono de Comunicación
- **Estilo:** Exclusivo, profesional, cercano pero formal
- **Idioma:** Español de España
- **Personalidad:** Elegante, resolutivo, experto
- **Regla de oro:** "Habla de aspiraciones, no solo de metros cuadrados"

## Keywords Principales
1. pisos de lujo Madrid
2. viviendas exclusivas Madrid
3. inmobiliaria premium Madrid
4. áticos lujo Salamanca Madrid
5. casa lujo La Moraleja

## Acceso a APIs (marcar con X)
- [X] OpenRouter API
- [X] GA4
- [X] Google Search Console
- [ ] Backend propio

## Competidores Principales
1. [lucasfox.com](https://lucasfox.com)
2. [engelvoelkers.com](https://engelvoelkers.com/es/madrid)
3. [barnes-madrid.com](https://barnes-madrid.com)
4. [coldwellbanker.es](https://coldwellbanker.es)
5. [promora.com](https://promora.com)
```

### Personalización de context/servicios.md

```markdown
# Servicios / Productos — Inmobiliaria Premium Madrid

## Servicio 1: Compraventa de Viviendas de Lujo

**Nombre:** Asesoramiento Integral en Compraventa de Lujo

**Descripción breve:**
Acompañamos a nuestros clientes en todo el proceso de compra o venta de
inmuebles de alto standing, desde la tasación hasta la firma notarial,
incluyendo due diligence legal y fiscal.

**Público objetivo:** Propietarios de inmuebles >500.000€ y compradores
con capacidad de inversión en este segmento.

**Beneficios clave:**
- Red de contactos exclusiva (compradores internacionales)
- Due diligence legal y fiscal incluida
- Reportaje fotográfico profesional y tour virtual 3D
- Negociación discreta y personalizada
- Postventa: gestión de reformas y mudanza

**Precio / Modelo:** Comisión del 3-5% sobre precio de venta

**Keywords asociadas:**
- vender piso lujo Madrid
- comprar casa exclusiva Madrid
- tasación vivienda lujo Madrid
- inmobiliaria lujo Madrid precios

## Servicio 2: Alquiler de Larga Temporada Premium

**Nombre:** Alquiler Residencial Premium

**Descripción breve:**
Selección de viviendas de alta gama en alquiler para profesionales
internacionales, familias y ejecutivos que buscan lo mejor de Madrid.

**Público objetivo:** Expatriados, directivos, familias con alto poder adquisitivo.

**Beneficios clave:**
- Viviendas completamente amuebladas y equipadas
- Contratos en inglés y español
- Gestión integral (altas suministros, seguros)
- Servicio de concierge 24/7

**Precio / Modelo:** Comisión de un mes de alquiler + IVA

**Keywords asociadas:**
- alquiler piso lujo Madrid
- alquiler temporal ejecutivos Madrid
- piso amueblado lujo Madrid alquiler
- renta alta Madrid

## Terminología del Negocio
- **Due diligence:** Proceso de verificación legal y fiscal de una propiedad
- **Arrás:** Cantidad que el comprador entrega como garantía (10% del precio)
- **Nota simple:** Documento del Registro de la Propiedad que acredita titularidad
- **Plusvalía municipal:** Impuesto municipal sobre el incremento del valor del terreno
- **IBI:** Impuesto sobre Bienes Inmuebles (anual)
- **Certificado energético:** Documento obligatorio para vender o alquilar
- **ASEME:** Asociación de Servicios del Mercado Exclusivo (asociación profesional)

## Proceso de Venta/Conversión
1. **Primera visita:** Usuario llega al blog o ficha de propiedad
2. **Consideración:** Solicita más información o visita guiada
3. **Decisión:** Tasación o due diligence de la propiedad
4. **Conversión:** Firma de arras o contrato de alquiler

## Preguntas Frecuentes
- **¿Cuánto cuesta tasar mi piso?** La tasación es gratuita y sin compromiso
- **¿Cuánto tarda en venderse un piso de lujo en Madrid?** Entre 3 y 12 meses
- **¿Trabajáis con compradores extranjeros?** Sí, tenemos clientes en más de 15 países
- **¿Qué documentos necesito para vender?** Escritura, nota simple, certificado energético,IBI
```

---

## 3. Cómo Agregar un Skill Nuevo

El sistema permite agregar skills personalizados en 5 pasos. Cada skill es una capacidad que la IA puede ejecutar mediante Function Calling.

### Paso 1: Crear el JSON Schema en `skills/`

Define la estructura de datos que el skill recibirá y devolverá.

```json
{
  "name": "seo_mi_skill",
  "description": "Descripción clara de qué hace mi skill y cuándo debe activarse. Incluye los triggers al final para que el orquestador pueda decidir.",
  "parameters": {
    "type": "object",
    "properties": {
      "input_1": {
        "type": "string",
        "description": "Descripción detallada del campo. La IA usará esto para saber qué escribir aquí."
      },
      "input_2": {
        "type": "integer",
        "description": "Descripción del campo numérico."
      },
      "input_3": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "Lista de elementos."
      },
      "output_1": {
        "type": "string",
        "description": "El resultado principal que debe generar la IA."
      }
    },
    "required": ["input_1", "output_1"]
  }
}
```

**Reglas para nombrar skills:**
- Usar prefijo `seo_` para todos los skills SEO
- Usar snake_case (ej: `seo_competitor_analysis`)
- El nombre debe coincidir con el archivo JSON (ej: `seo-competitor-analysis.json`)

### Paso 2: Crear el System Prompt en `prompts/`

Crea un archivo markdown con las instrucciones detalladas para la IA. Sigue el formato de los prompts existentes:

```markdown
<!--
================================================================================
PROMPT: Mi Nuevo Skill SEO
================================================================================
¿Qué hace este skill?
Descripción detallada de la funcionalidad.

Inputs requeridos:
- input_1: Descripción

¿Cuándo se usa?
- Trigger 1
- Trigger 2

Integración:
- Cómo se conecta con el resto del sistema
================================================================================
-->

# System Prompt: Nombre del Skill

Eres un [rol] con [X] años de experiencia en [área].

## Tu Misión
[Descripción detallada de lo que debe hacer la IA]

## Reglas Estrictas
- Regla 1
- Regla 2

## Formato de Respuesta
Debes responder invocando la función `seo_mi_skill` con los siguientes argumentos:

```json
{
  "output_1": "...",
  "output_2": "..."
}
```

## Proceso de Ejecución
1. Paso 1
2. Paso 2

## Triggers de Activación
- trigger 1, trigger 2

## Ejemplo de Invocación
```python
from scripts.orchestrator import SEOOrchestrator
orch = SEOOrchestrator()
result = orch.execute_skill_with_gemini("seo_mi_skill", {"input_1": "valor"})
```
```

### Paso 3: Registrar el Schema en el Orquestador

El orquestador carga automáticamente cualquier schema JSON del directorio `skills/`. No es necesario registrar nada explícitamente. Solo asegúrate de que:

1. El archivo JSON esté en `skills/` con la extensión `.json`
2. El prompt markdown esté en `prompts/` (opcional, usado como documentación)
3. El nombre del skill coincida con el nombre del archivo sin extensión

El orquestador usa `load_function_schema()` que busca en `skills/`:

```python
# orchestrator.py (línea 139)
def load_function_schema(self, skill_name: str) -> Dict:
    json_path = os.path.join(self.skills_path, f"{skill_name}.json")
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Schema no encontrado: {json_path}")
    with open(json_path, 'r') as f:
        return json.load(f)
```

### Paso 4: Agregar Triggers en el Prompt (Opcional)

Los triggers ayudan a decidir cuándo invocar cada skill. Se documentan en el prompt markdown y en el campo `description` del JSON.

### Paso 5: Probar el Nuevo Skill

```bash
# Probar que el schema se carga correctamente
python3 -c "
import json
from pathlib import Path
schema = json.loads(Path('skills/seo-mi-skill.json').read_text())
print(f'Skill: {schema[\"name\"]}')
print(f'Campos requeridos: {schema[\"parameters\"][\"required\"]}')
"

# Probar la ejecución con el orquestador
python3 -c "
from scripts.orchestrator import SEOOrchestrator
orch = SEOOrchestrator()
try:
    result = orch.execute_skill_with_gemini('seo_mi_skill', {'input_1': 'test'})
    print('✓ Ejecución exitosa')
    print(result['response_text'][:200])
except Exception as e:
    print(f'Error: {e}')
"
```

### Ejemplo Completo: Skill de Análisis de Competidores

```json
{
  "name": "seo_competitor_analysis",
  "description": "Analiza sitios web de la competencia y genera un informe comparativo detallado. Incluye estructura, keywords, contenido, backlinks y estrategia SEO. Actívalo cuando se pida: analizar competencia, investigación competitiva, benchmark SEO, comparativa con competidores.",
  "parameters": {
    "type": "object",
    "properties": {
      "competitor_url": {
        "type": "string",
        "description": "URL completa del competidor a analizar (ej: https://competidor.com)"
      },
      "our_url": {
        "type": "string",
        "description": "URL de nuestra página equivalente para comparación"
      },
      "analysis_report": {
        "type": "string",
        "description": "Informe completo en formato Markdown con el análisis comparativo"
      },
      "opportunities": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Lista de oportunidades detectadas donde podemos superar al competidor"
      }
    },
    "required": ["competitor_url", "analysis_report", "opportunities"]
  }
}
```

---

## 4. Cómo Cambiar el Modelo de IA

### Cambio del Modelo por Defecto

Edita `scripts/openrouter_client.py` en el constructor de `OpenRouterClient`:

```python
# Línea 70: Modelo por defecto
def __init__(self, api_key=None, model="deepseek/deepseek-chat"):
```

Puedes cambiarlo a cualquier modelo compatible con OpenRouter:

```python
# Modelos recomendados por caso de uso:
model="deepseek/deepseek-chat"           # Mejor relación calidad/precio (recomendado)
model="zhipu/glm-4"                      # Muy bueno para Function Calling
model="anthropic/claude-3.5-sonnet"      # Mejor calidad general
model="google/gemini-2.5-pro"            # Bueno para tareas técnicas
model="openai/gpt-4o"                    # Referencia de calidad (más caro)
model="meta-llama/llama-3.1-70b-instruct" # Open source, buena calidad
model="mistralai/mistral-large"          # Bueno para español
```

### Cambio de la Lista de Fallback

Los modelos de respaldo se definen en `generate_content()`:

```python
# Líneas 129-137: Lista de fallback
fallback_models = [
    self.model,                              # Modelo principal
    "deepseek/deepseek-chat",                # Fallback 1
    "zhipu/glm-4",                           # Fallback 2
    "anthropic/claude-3.5-sonnet",           # Fallback 3
    "meta-llama/llama-3.1-70b-instruct",     # Fallback 4
    "google/gemini-2.5-pro",                 # Fallback 5
    "openai/gpt-4o"                          # Fallback 6
]
```

**Estrategias recomendadas:**

| Estrategia | Lista de modelos | Costo | Calidad |
|---|---|---|---|
| Económica | DeepSeek → GLM-4 → Llama 70B | Bajo | Alta |
| Equilibrada | Claude 3.5 → Gemini 2.5 → GPT-4o | Medio | Muy alta |
| Máxima calidad | GPT-4o → Claude 3.5 → Gemini 2.5 | Alto | Excelente |
| Solo open source | DeepSeek → GLM-4 → Llama 70B → Mistral | Muy bajo | Buena |

### Configuración por Proyecto via .env

Puedes sobreescribir el modelo desde el archivo `.env` de cada proyecto:

```bash
# En inputs/.env-cliente-a
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
```

Luego en `openrouter_client.py`, lee esta variable (si existe):

```python
class OpenRouterClient:
    def __init__(self, api_key=None, model=None):
        # Si no se pasa modelo, leer del .env o usar defecto
        self.model = model or os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat")
```

---

## 5. Cómo Adaptar los Prompts para Diferentes Nichos

### Nicho: E-commerce

**Características del contenido:**
- Keywords: nombres de productos, categorías, marcas
- Tono: descriptivo, persuasivo, orientado a conversión
- Tipo de contenido: fichas de producto, guías de compra, comparativas, categorías

**Adaptación del prompt `content-creator.md`:**

```markdown
## Reglas Específicas para E-commerce
- Incluir especificaciones técnicas en formato tabla
- Optimizar para búsqueda por voz ("dónde comprar...", "mejor... para...")
- Incluir FAQs con preguntas reales de compradores
- Usar CTAs de compra ("Añadir al carrito", "Comprar ahora")
- Incluir datos de envío, garantía y devoluciones
- Para fichas de producto: título ≤60 chars, descripción ≤155 chars,
  bullets con beneficios, especificaciones técnicas
- Para guías de compra: estructura comparativa, tabla de pros/contra,
  recomendación según presupuesto
```

**Adaptación de `prompts/site-auditor.md`:**

```markdown
## Reglas Específicas para E-commerce
- Verificar que las fichas de producto tengan schema.org/Product
- Comprobar que haya breadcrumbs (schema.org/BreadcrumbList)
- Revisar que las imágenes de producto tengan alt text descriptivo
- Verificar que los precios estén actualizados (precio, oferta, IVA)
- Asegurar que los filtros de categoría sean crawlables
- Comprobar que las URLs de producto sean canónicas
- Verificar paginación correcta con rel=next/prev
```

### Nicho: Generación de Leads (Seguros, Hipotecas, Servicios Profesionales)

**Características del contenido:**
- Keywords: problemas, soluciones, comparativas, costes
- Tono: profesional, empático, informativo, generador de confianza
- Tipo de contenido: guías descargables, calculadoras, comparativas, casos de éxito

**Adaptación del prompt `content-creator.md`:**

```markdown
## Reglas Específicas para Generación de Leads
- Incluir llamados a la acción de conversión ("Solicita tu presupuesto gratuito",
  "Compara las mejores opciones", "Habla con un asesor")
- Estructurar el contenido para capturar leads: introducción → problema → solución →
  beneficios → CTA
- Incluir datos y estadísticas del sector (con fuente verificable)
- Usar un tono empático que reconozca las preocupaciones del usuario
- Para calculadoras: incluir simulaciones de ejemplo con cifras realistas
- Para comparativas: tabla imparcial con pros/contra de cada opción
- Incluir preguntas frecuentes con respuestas detalladas
- **NUNCA** dar consejos legales o financieros sin calificarlos como informativos
```

**Adaptación de `prompts/dashboard.md`:**

```markdown
## Métricas Clave para Lead Gen
- Sesiones orgánicas a páginas de servicio
- Tasa de conversión de lead (formularios completados / visitas)
- Coste por lead estimado (si hay datos de inversión)
- Keywords con intención transaccional (vs informacional)
- Páginas con mejor y peor tasa de conversión
- Tiempo medio en páginas de servicio (engagement)
```

### Nicho: Blogs Informativos / Editoriales

**Características del contenido:**
- Keywords: preguntas, tutoriales, guías, listas
- Tono: divulgativo, educativo, cercano
- Tipo de contenido: artículos largos, listas, FAQ, tutoriales paso a paso

**Adaptación del prompt `content-creator.md`:**

```markdown
## Reglas Específicas para Blogs Informativos
- Priorizar intención informacional: responder preguntas, explicar conceptos,
  enseñar procesos
- Estructura ideal: titular potente → introducción → desarrollo por subtemas →
  conclusión + CTA de suscripción
- Incluir ejemplos prácticos y casos de uso reales
- Usar listas numeradas, tablas y diagramas de texto para facilitar la lectura
- Incluir enlaces internos a otros artículos relacionados (aumenta páginas vistas)
- Optimizar para featured snippets: responder preguntas directamente al inicio
  de cada sección
- Longitud mínima recomendada: 1500 palabras
- Incluir índice al inicio del artículo con anclas
- **SIEMPRE** citar fuentes cuando se mencionen datos o estadísticas
```

---

## 6. Variables de Entorno por Proyecto

| Variable | Obligatoria | Descripción | Qué cambiar por proyecto |
|---|---|---|---|
| `OPENROUTER_API_KEY` | Sí (o Gemini) | API key de OpenRouter | Usar la key del cliente si tiene cuenta propia, o la general |
| `GEMINI_API_KEY` | Sí (o OpenRouter) | API key de Google Gemini | Alternativa gratuita a OpenRouter |
| `OPENROUTER_MODEL` | No | Modelo específico para este proyecto | Proyectos premium pueden usar Claude/GPT-4o; económicos DeepSeek |
| `GA4_CREDENTIALS_PATH` | Sí (para dashboard) | Ruta al JSON de cuenta de servicio GA4 | Cada proyecto necesita su propio service account |
| `GA4_PROPERTY_ID` | Sí (para dashboard) | ID de propiedad de Google Analytics 4 | Diferente para cada proyecto/cliente |
| `GSC_CREDENTIALS_PATH` | Sí (para dashboard) | Ruta al JSON de cuenta de servicio GSC | Puede ser el mismo que GA4 si tiene acceso |
| `GSC_SITE_URL` | Sí (para dashboard) | URL del sitio en Google Search Console | Diferente para cada proyecto |
| `PROJECT_PATH` | Sí | Ruta absoluta al repositorio local del proyecto web | Apunta al directorio raíz de cada cliente |
| `REPO_REMOTE` | No | URL del repositorio Git remoto | Cada proyecto tiene su propio repo |
| `GIT_BRANCH` | No | Rama de Git (por defecto: main) | Algunos proyectos usan develop o staging |
| `FRONTEND_PATH` | No | Subdirectorio del frontend (por defecto: app/frontend) | Proyectos sin Next.js pueden tener estructura diferente |
| `TELEGRAM_BOT_TOKEN` | No | Token del bot de Telegram para notificaciones | Puede ser el mismo bot para todos o uno por cliente |
| `TELEGRAM_CHAT_ID` | No | ID del chat/grupo de Telegram | Cada cliente puede tener su propio grupo |
| `BACKEND_API_URL` | No | URL del backend para enviar reportes | Cada proyecto puede tener su propio backend |
| `MCP_SERVERS` | No | Configuración JSON de servidores MCP | Proyectos avanzados pueden necesitar servidores adicionales |
| `DEFAULT_LANG` | No | Idioma por defecto (por defecto: es) | Proyectos multilingüe pueden usar en, ca, eu |
| `TZ` | No | Zona horaria (por defecto: Europe/Madrid) | Ajustar según ubicación del cliente |

---

## 7. Ejemplo Completo: Adaptar para una Inmobiliaria

A continuación se muestra el proceso completo de adaptación para "Inmobiliaria Premium Madrid", una agencia de viviendas de lujo.

### Paso 1: Crear el archivo .env del proyecto

```bash
cp config/.env.template inputs/.env-inmobiliaria
```

Editar `inputs/.env-inmobiliaria`:

```bash
# ============================================================
# INMOBILIARIA PREMIUM MADRID — Configuración SEO
# ============================================================
OPENROUTER_API_KEY=sk-or-v1-clave_del_cliente
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet  # Cliente premium, mejor modelo

GA4_CREDENTIALS_PATH=/opt/seo-mcp-skill/inputs/credenciales-ga4-inmobiliaria.json
GA4_PROPERTY_ID=987654321
GSC_CREDENTIALS_PATH=/opt/seo-mcp-skill/inputs/credenciales-gsc-inmobiliaria.json
GSC_SITE_URL=https://inmobiliariapremium.es/

PROJECT_PATH=/var/www/inmobiliariapremium
REPO_REMOTE=https://github.com/cliente/inmobiliariapremium.git
GIT_BRANCH=main
FRONTEND_PATH=app/frontend

TELEGRAM_BOT_TOKEN=7777777777:AAEclave_del_bot
TELEGRAM_CHAT_ID=-1001234567890

BACKEND_API_URL=https://api.inmobiliariapremium.es/api

MCP_SERVERS=[{"name":"browser","command":"npx","args":["-y","@modelcontextprotocol/server-puppeteer"]}]

DEFAULT_LANG=es
TZ=Europe/Madrid
```

### Paso 2: Configurar el contexto de empresa

Rellenar `config/context/empresa.md` con los datos de la inmobiliaria:
- Descripción: agencia boutique de lujo en Madrid
- Keywords: "pisos de lujo Madrid", "viviendas exclusivas", "inmobiliaria premium"
- Tono: exclusivo, profesional, cercano pero formal
- Competidores: Lucas Fox, Engel & Völkers, Barnes

### Paso 3: Configurar el contexto de servicios

Rellenar `config/context/servicios.md` con:
- Servicio 1: Compraventa de viviendas de lujo (keywords: vender piso lujo Madrid, tasación vivienda lujo)
- Servicio 2: Alquiler premium larga temporada (keywords: alquilar piso lujo Madrid)
- Terminología específica: arras, nota simple, plusvalía,IBI, certificado energético
- FAQ sobre compraventa, tiempos, documentación, compradores extranjeros

### Paso 4: Ajustar reglas de contenido

Editar `config/context/reglas.md` para añadir reglas específicas del nicho inmobiliario:

```markdown
## Reglas Específicas para Inmobiliaria
- Incluir siempre superficie útil y construida en descripciones
- Mencionar orientación, estado de conservación y año de construcción
- Incluir información sobre la zona: transportes, colegios, servicios
- Para propiedades de lujo: destacar elementos únicos (piscina, vistas, seguridad)
- Usar vocabulario aspiracional pero honesto
- Incluir enlace a la ficha completa de la propiedad
- Añadir schema.org/Product con los datos de la propiedad
- Las descripciones deben ser únicas (nunca copiar de otros portales)
```

### Paso 5: Personalizar los prompts para el nicho inmobiliario

**En `prompts/content-creator.md` añadir:**

```markdown
## Reglas Específicas para Inmobiliario
- Las fichas de propiedad deben incluir: precio, superficie, habitaciones,
  baños, planta, orientación, año construcción, estado, extras
- Los artículos de blog sobre compraventa deben incluir: situación del mercado,
  consejos para compradores/vendedores, aspectos legales y fiscales
- Para guías de zonas: incluir precios medios, tipos de vivienda, transportes,
  colegios, servicios cercanos
- Tono: aspiracional pero realista, profesional y cercano
- Keywords de cola larga: "comprar ático con terraza Salamanca Madrid",
  "vender piso lujo Chamberí", "inmobiliaria especializada La Moraleja"
- Incluir siempre un CTA de contacto: "Solicita más información",
  "Visita esta propiedad", "Contacta con nuestro equipo"
```

**En `prompts/site-auditor.md` añadir:**

```markdown
## Reglas Específicas para Sitios Inmobiliarios
- Verificar que las fichas de propiedad tengan schema.org/Product con:
  name, description, url, image, offers (price, priceCurrency),
  additionalProperty (floorSize, numberOfRooms, bathroomNumber)
- Comprobar que las URLs de propiedades sean amigables: /venta/piso-salamanca-madrid-123
- Revisar que los filtros de búsqueda sean indexables (no solo JavaScript)
- Verificar que las imágenes tengan alt text descriptivo de la propiedad
- Asegurar que los mapas interactivos tengan fallback estático
- Revisar que los formularios de contacto tengan campos schema.org/ContactPoint
```

### Paso 6: Probar la configuración

```bash
# Cargar el entorno de la inmobiliaria y probar conexión
env $(cat inputs/.env-inmobiliaria | xargs) python scripts/orchestrator.py test-openrouter

# Ejecutar un ciclo de monitoreo completo
env $(cat inputs/.env-inmobiliaria | xargs) python scripts/orchestrator.py monitor

# Ver el reporte generado
cat outputs/$(ls -t outputs/ | head -1)
```

### Paso 7: Programar la ejecución automática

Añadir la inmobiliaria al multi-project runner o crear un servicio systemd específico:

```bash
# Opción A: Añadir al multi_project_runner.py
# Añadir a la lista de proyectos:
{"nombre": "Inmobiliaria Premium Madrid", "env": "inputs/.env-inmobiliaria"},

# Opción B: Servicio systemd dedicado
sudo nano /etc/systemd/system/seo-mcp-inmobiliaria.service
```

```ini
[Unit]
Description=SEO MCP Agent — Inmobiliaria Premium Madrid
After=network.target

[Service]
Type=simple
User=deploy
WorkingDirectory=/opt/seo-mcp-skill
ExecStart=/usr/bin/python3 scripts/orchestrator.py schedule
Restart=always
RestartSec=30
EnvironmentFile=/opt/seo-mcp-skill/inputs/.env-inmobiliaria

[Install]
WantedBy=multi-user.target
```

### Resumen de Archivos Modificados para la Inmobiliaria

| Archivo | Acción |
|---|---|
| `inputs/.env-inmobiliaria` | Crear nuevo (copia de template) |
| `config/context/empresa.md` | Sustituir contenido con datos reales |
| `config/context/servicios.md` | Sustituir contenido con servicios reales |
| `config/context/reglas.md` | Añadir sección específica inmobiliaria |
| `prompts/content-creator.md` | Añadir reglas para nicho inmobiliario |
| `prompts/site-auditor.md` | Añadir reglas de auditoría inmobiliaria |
| `scripts/multi_project_runner.py` | Añadir proyecto a la lista |

No se modificaron archivos compartidos (schemas JSON, orquestador, clientes), lo que demuestra la flexibilidad del sistema: **solo cambia la configuración y los prompts, no el núcleo**.

---

> **Documento de referencia para adaptación de proyectos** — SEO MCP Skill
> Creado: Junio 2026 — Última actualización: 20 Junio 2026
> Próxima revisión recomendada: cada 3 meses o al incorporar un nuevo cliente
