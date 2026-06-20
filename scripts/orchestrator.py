#!/usr/bin/env python3
"""
Orquestador principal para SEO Skills.

Este módulo coordina todas las capacidades de automatización SEO: integración con
modelos de lenguaje (OpenRouter/Gemini), métricas de Google Analytics 4, datos de
Google Search Console, auto-aprendizaje mediante base de datos SQLite, control de
versiones Git, notificaciones vía Telegram y sincronización con una plataforma web.

PRERREQUISITOS:
- Python 3.12+
- Dependencias: openai, google-analytics-data, google-api-python-client, schedule,
  python-dotenv, httpx
- Archivo inputs/.env con las claves de API correspondientes:
  OPENROUTER_API_KEY, GA4_CREDENTIALS_PATH, GA4_PROPERTY_ID, GSC_CREDENTIALS_PATH,
  GSC_SITE_URL, PROJECT_PATH, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, BACKEND_API_URL

CONFIGURACIÓN:
1. Copia inputs/.env.template a inputs/.env y completa los valores.
2. Asegúrate de que PROJECT_PATH apunte a la raíz del proyecto web.
3. Ejecuta: python3 scripts/orchestrator.py test-openrouter

USO:
  python3 scripts/orchestrator.py monitor        # Un ciclo de monitoreo completo
  python3 scripts/orchestrator.py schedule       # Ejecuta el planificador (tareas programadas)
  python3 scripts/orchestrator.py test-openrouter # Prueba de conexión con OpenRouter
  python3 scripts/orchestrator.py test-gemini    # Alias de test-openrouter

INTEGRACIÓN:
- Los reportes se envían a la API del backend (BACKEND_API_URL) y se notifican
  por Telegram.
- Los cambios en archivos se registran con Git y se pushean automáticamente.
- El histórico de ejecuciones y keywords se almacena en outputs/seo_history.db
  para aprendizaje continuo.
"""

import os
import sys
import json
import logging
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Asegurar que el directorio de scripts esté en el path
_scripts_dir = os.path.dirname(os.path.abspath(__file__))
if _scripts_dir not in sys.path:
    sys.path.insert(0, os.path.dirname(_scripts_dir))

# Cargar variables de entorno
load_dotenv(os.path.join(os.path.dirname(__file__), '../inputs/.env'))

# Configurar logging: archivo + consola
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), '../outputs/seo_orchestrator.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class SEOOrchestrator:
    """
    Orquestador principal de automatización SEO.

    Gestiona la ejecución de skills mediante modelos de lenguaje (OpenRouter),
    la recolección de métricas de GA4 y GSC, el auto-aprendizaje histórico,
    el control de versiones Git y las notificaciones vía Telegram.

    Los clientes (OpenRouter, GA4, GSC, histórico, Git, Telegram) se inicializan
    de forma diferida (lazy loading) mediante propiedades, lo que permite que el
    orquestador se construya rápidamente sin depender de servicios externos hasta
    que realmente se necesiten.
    """

    def __init__(self):
        """Inicializa el orquestador con la ruta del proyecto y las rutas base."""
        self.project_path = os.getenv("PROJECT_PATH")
        self.skills_path = os.path.join(os.path.dirname(__file__), '../skills')
        self.scripts_path = os.path.join(os.path.dirname(__file__))

        # Clientes internos (lazy loading, se inicializan bajo demanda)
        self._gemini_client = None
        self._ga4_client = None
        self._gsc_client = None
        self._history_client = None
        self._git_client = None
        self._telegram = None

        logger.info("SEOOrchestrator inicializado")

    @property
    def gemini(self):
        """Cliente OpenRouter (inicialización diferida)."""
        if self._gemini_client is None:
            from openrouter_client import OpenRouterClient
            self._gemini_client = OpenRouterClient()
        return self._gemini_client

    @property
    def ga4(self):
        """Cliente GA4 (actualmente deshabilitado por solicitud del usuario)."""
        return None

    @property
    def gsc(self):
        """Cliente GSC (actualmente deshabilitado por solicitud del usuario)."""
        return None

    @property
    def history(self):
        """Cliente de histórico SQLite (inicialización diferida)."""
        if self._history_client is None:
            from history_client import SEOHistoryClient
            self._history_client = SEOHistoryClient()
        return self._history_client

    @property
    def git(self):
        """Cliente Git (inicialización diferida)."""
        if self._git_client is None:
            from git_auto_push import GitAutoPush
            self._git_client = GitAutoPush(self.project_path)
        return self._git_client

    @property
    def telegram(self):
        """Cliente Telegram (inicialización diferida)."""
        if self._telegram is None:
            from telegram_notifier import TelegramNotifier
            self._telegram = TelegramNotifier()
        return self._telegram

    def load_function_schema(self, skill_name: str) -> Dict:
        """
        Carga el esquema de función (Function Calling) desde un archivo JSON.

        Args:
            skill_name: Nombre de la skill (ej: seo_dashboard, seo_site_auditor).

        Returns:
            Diccionario con el esquema de la función compatible con OpenRouter.

        Raises:
            FileNotFoundError: Si no existe el archivo JSON en ../skills/.
        """
        # Buscar el JSON en el directorio de skills
        json_path = os.path.join(self.skills_path, f"{skill_name}.json")
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"Schema no encontrado: {json_path}")

        with open(json_path, 'r') as f:
            return json.load(f)

    def execute_skill_with_gemini(
        self,
        skill_name: str,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ejecuta una skill usando Function Calling del modelo de lenguaje.

        El flujo es:
        1. Carga el esquema JSON de la skill.
        2. Obtiene el contexto de adaptación desde el histórico.
        3. Construye un prompt con el contexto y los inputs.
        4. Llama al modelo forzando el Function Call hacia la skill.
        5. Registra la ejecución en el histórico.

        Args:
            skill_name: Nombre de la skill (ej: seo_dashboard).
            inputs: Diccionario con los argumentos de entrada para la skill.

        Returns:
            Diccionario con execution_id, skill_name, response_text y function_calls.
        """
        logger.info(f"Ejecutando skill: {skill_name}")

        # Cargar esquema de la función desde el JSON
        function_schema = self.load_function_schema(skill_name)

        # Obtener contexto de auto-aprendizaje (ejecuciones previas similares)
        adaptation_context = self.history.get_adaptation_context({
            "skill_name": skill_name,
            **inputs
        })

        # Construir prompt enriquecido con el contexto histórico
        prompt = f"""
Ejecutar la skill {skill_name} con los siguientes inputs:
{json.dumps(inputs, ensure_ascii=False, indent=2)}

CONTEXTO DE ADAPTACIÓN (auto-aprendizaje):
{adaptation_context}

Genera el output esperado por la skill basándote en el contexto y los inputs.
"""

        # Llamar al modelo forzando el Function Call
        response = self.gemini.generate_content(
            prompt=prompt,
            functions=[function_schema],
            function_call={"name": skill_name}
        )

        # Registrar la ejecución en la base de datos histórica
        execution_id = self.history.log_execution(
            skill_name=skill_name,
            inputs=inputs,
            outputs={"response": response["text"], "function_calls": response["function_calls"]}
        )

        return {
            "execution_id": execution_id,
            "skill_name": skill_name,
            "response_text": response["text"],
            "function_calls": response["function_calls"]
        }

    def automated_seo_monitoring(self):
        """
        Ciclo completo de monitoreo SEO automatizado.

        Pasos:
        1. Obtiene métricas de GA4 (sesiones orgánicas, páginas top).
        2. Obtiene keywords de GSC.
        3. Genera un reporte con la IA usando la skill seo_dashboard.
        4. Guarda el reporte en outputs/ como Markdown.
        5. Registra las keywords en el histórico.
        6. Envía el reporte y métricas a la plataforma vía API.
        7. Hace commit y push Git si hay cambios.
        8. Notifica por Telegram el resultado del monitoreo.
        """
        logger.info("=== INICIANDO MONITOREO AUTOMÁTICO SEO ===")

        try:
            # 1. Obtener métricas de GA4 (si está habilitado)
            ga4_metrics = {}
            if self.ga4:
                ga4_metrics = self.ga4.get_seo_metrics(days_back=7)
                logger.info(f"Métricas GA4 obtenidas: {ga4_metrics.get('organic_sessions', 0)} sesiones orgánicas")

            # 2. Obtener keywords desde GSC (si está habilitado)
            gsc_keywords = []
            if self.gsc:
                gsc_keywords = self.gsc.get_top_keywords(days_back=7, limit=50)
                logger.info(f"Keywords GSC obtenidas: {len(gsc_keywords)} keywords")

            # 3. Generar reporte usando la IA
            dashboard_inputs = {
                "periodo_desde": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                "periodo_hasta": datetime.now().strftime("%Y-%m-%d"),
                "include_gsc": True,
                "include_ga4": True,
                "top_n_keywords": 20,
                "top_n_pages": 10,
                "ga4_data": ga4_metrics,
                "gsc_keywords": gsc_keywords
            }

            result = self.execute_skill_with_gemini(
                "seo_dashboard",
                dashboard_inputs
            )

            # 4. Guardar reporte en disco como Markdown
            report_path = os.path.join(
                os.path.dirname(__file__), '../outputs',
                f"{datetime.now().strftime('%Y%m%d')}_reporte_automatico.md"
            )
            report_content = result.get("response_text", "")
            # Si la IA devolvió argumentos estructurados, reconstruir el reporte
            if not report_content and result.get("function_calls"):
                args = result["function_calls"][0].get("args", {})
                if "report_markdown" in args:
                    report_content = args["report_markdown"]
                    if "suggested_actions" in args and args["suggested_actions"]:
                        report_content += "\n\n### Acciones Sugeridas:\n"
                        for acc in args["suggested_actions"]:
                            report_content += f"- {acc}\n"
                else:
                    import json
                    report_content = "### Resultados generados por IA:\n```json\n" + json.dumps(args, indent=2, ensure_ascii=False) + "\n```\n"

            with open(report_path, 'w') as f:
                f.write(report_content)

            logger.info(f"Reporte guardado en: {report_path}")

            # 5. Registrar keywords en el histórico
            if gsc_keywords:
                self.history.log_keywords(
                    execution_id=result["execution_id"],
                    keywords=gsc_keywords,
                    date=datetime.now().strftime("%Y-%m-%d")
                )

            # 6. Enviar reporte a la plataforma web
            report_data = {
                "title": f"Reporte SEO {datetime.now().strftime('%Y-%m-%d')}",
                "period_start": dashboard_inputs["periodo_desde"],
                "period_end": dashboard_inputs["periodo_hasta"],
                "summary": result["response_text"][:2000],
                "full_report_path": report_path,
                "skills_executed": ["seo_dashboard"],
                "ga4_organic_sessions": ga4_metrics.get("organic_sessions", 0),
                "gsc_keywords_count": len(gsc_keywords),
                "execution_id": result["execution_id"],
                "status": "success"
            }
            self.telegram.push_report_to_platform(report_data)

            # 7. Enviar métricas a la plataforma
            if ga4_metrics:
                self.telegram.push_metrics_to_platform(ga4_metrics)
            if gsc_keywords:
                keyword_summary = [
                    {"keyword": k["query"], "clicks": k.get("clicks", 0),
                     "impressions": k.get("impressions", 0), "position": k.get("position", 0)}
                    for k in gsc_keywords[:20]
                ]
                self.telegram.push_metrics_to_platform({
                    "type": "gsc_keywords",
                    "period_start": dashboard_inputs["periodo_desde"],
                    "period_end": dashboard_inputs["periodo_hasta"],
                    "keywords": keyword_summary
                })

            # 8. Git commit & push si hay cambios en el repositorio
            git_status = self.git.get_status()
            if git_status:
                self.git.commit_and_push(f"auto: SEO monitoring report {datetime.now().strftime('%Y-%m-%d')}")

            # 9. Enviar notificación por Telegram
            summary = {
                "status": "success",
                "organic_sessions": ga4_metrics.get("organic_sessions", 0),
                "keywords_count": len(gsc_keywords)
            }
            self.telegram.notify_monitoring_complete(report_path, summary)

            return {"status": "success", "report_path": report_path}

        except Exception as e:
            logger.error(f"Error en monitoreo automático: {e}")
            return {"status": "error", "error": str(e)}

    def automated_seo_monitoring_per_page(self):
        """
        Monitoreo SEO por página individual y blog.

        Se ejecuta 2 veces al día (10:00 y 22:00). Para cada URL del sitio:
        1. Localiza el archivo físico (TSX o MDX) en el proyecto.
        2. Pasa el contenido actual a la skill seo_site_auditor.
        3. Si la IA devuelve contenido mejorado, sobreescribe el archivo.
        4. Envía un reporte a la plataforma.
        5. Al final, hace Git push de todos los cambios realizados.
        """
        logger.info("=== INICIANDO MONITOREO SEO POR PÁGINA Y BLOG ===")

        try:
            # Lista genérica de páginas principales del sitio
            pages = [
                "/",
                "/servicios",
                "/nosotros",
                "/contacto",
                "/faq",
                "/blog"
            ]

            # Extraer slugs de blog desde posts.ts
            blogs = []
            import re
            posts_ts_path = os.path.join(self.project_path, "app/frontend/posts.ts")
            if os.path.exists(posts_ts_path):
                with open(posts_ts_path, 'r') as f:
                    content = f.read()
                    slugs = re.findall(r'slug:\s*["\'](.*?)["\']', content)
                    blogs = [f"/blog/{slug}" for slug in slugs]

            all_urls = pages + blogs
            logger.info(f"Se analizarán {len(all_urls)} URLs: {all_urls}")

            for url in all_urls:
                logger.info(f"Analizando URL: {url}")

                # 1. Determinar la ruta del archivo físico según el tipo de URL
                file_path = None
                if url.startswith("/blog/"):
                    slug = url.replace("/blog/", "")
                    file_path = os.path.join(self.project_path, "app/frontend/app/blog", slug, "page.mdx")
                elif url == "/":
                    file_path = os.path.join(self.project_path, "app/frontend/app/page.tsx")
                else:
                    folder = url.strip("/")
                    file_path = os.path.join(self.project_path, "app/frontend/app", folder, "page.tsx")
                    if not os.path.exists(file_path):
                        file_path = os.path.join(self.project_path, "app/frontend/app", folder, "page.mdx")

                current_content = ""
                if file_path and os.path.exists(file_path):
                    with open(file_path, "r", encoding="utf-8") as f:
                        current_content = f.read()
                else:
                    logger.warning(f"No se encontró archivo físico para {url}. Saltando...")
                    continue

                # 2. Ejecutar skill de auditoría SEO pasando el contenido actual
                inputs = {
                    "url_sitio": url,
                    "plataforma_web": "Next.js (App Router) con Tailwind y MDX",
                    "contenido_actual": current_content,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                result = self.execute_skill_with_gemini("seo_site_auditor", inputs)

                # 3. Aplicar cambios reales si la IA devolvió contenido mejorado
                report_text = result.get("response_text", "")
                if result.get("function_calls"):
                    args = result["function_calls"][0].get("args", {})
                    updated_content = args.get("updated_mdx_content")
                    summary = args.get("summary_of_changes", "Auditoría aplicada.")

                    if updated_content:
                        logger.info(f"¡IA sugirió cambios para {url}! Sobreescribiendo archivo...")
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(updated_content)
                        report_text = f"## Resumen de Cambios:\n{summary}"

                # 4. Enviar reporte al dashboard
                report_data = {
                    "title": f"Análisis y Cambios SEO aplicados en {url}",
                    "period_start": datetime.now().strftime("%Y-%m-%d"),
                    "period_end": datetime.now().strftime("%Y-%m-%d"),
                    "summary": f"Auditoría ejecutada en tiempo real. Se ha modificado el archivo físico para {url}.",
                    "full_report_text": f"## Reporte de modificaciones para {url}\n\n{report_text}",
                    "skills_executed": ["seo_site_auditor"],
                    "execution_id": result["execution_id"],
                    "status": "success"
                }

                self.telegram.push_report_to_platform(report_data)
                time.sleep(5)

            # 5. Si hubo cambios, hacer Git push al final
            if self.git.get_status():
                self.git.commit_and_push(f"auto: SEO Auto-corrector aplicó mejoras en páginas ({datetime.now().strftime('%Y-%m-%d')})")

            logger.info("=== MONITOREO SEO POR PÁGINA COMPLETADO ===")

        except Exception as e:
            logger.error(f"Error en monitoreo por página: {e}")

    def schedule_automated_tasks(self):
        """
        Configura las tareas automáticas en el planificador.

        Horarios:
        - Monitoreo global: una vez al día a las 08:00.
        - Monitoreo por página: dos veces al día (10:00 y 22:00).
        - Reporte semanal: los lunes a las 09:00.
        """
        schedule.every().day.at("08:00").do(self.automated_seo_monitoring)
        schedule.every().day.at("10:00").do(self.automated_seo_monitoring_per_page)
        schedule.every().day.at("22:00").do(self.automated_seo_monitoring_per_page)
        schedule.every().monday.at("09:00").do(self.weekly_seo_report)

        logger.info("Tareas automáticas programadas (Global 1 vez, Páginas 2 veces al día)")

    def weekly_seo_report(self):
        """
        Genera un reporte semanal más detallado.

        Por ahora ejecuta el monitoreo global con un rango de 30 días
        para obtener una visión más amplia del rendimiento SEO.
        """
        logger.info("Generando reporte semanal...")
        if self.gsc:
            keywords = self.gsc.get_top_keywords(days_back=30, limit=100)
            logger.info(f"Keywords mensuales: {len(keywords)}")
        return {"status": "success", "type": "weekly"}

    def run_scheduler(self):
        """
        Ejecuta el planificador de tareas (bloqueante).

        Inicia el bucle infinito que revisa cada 60 segundos si hay
        tareas pendientes de ejecutar según el horario configurado.
        """
        self.schedule_automated_tasks()
        logger.info("Iniciando bucle de monitoreo automático... (Ctrl+C para detener)")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Monitoreo detenido por el usuario")


if __name__ == "__main__":
    orchestrator = SEOOrchestrator()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "monitor":
            result = orchestrator.automated_seo_monitoring()
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif command == "schedule":
            orchestrator.run_scheduler()

        elif command == "test-openrouter" or command == "test-gemini":
            try:
                response = orchestrator.gemini.generate_content(
                    "Hola, ¿qué es una hipoteca fija?"
                )
                print("Respuesta de OpenRouter:")
                print(response["text"])
            except Exception as e:
                print(f"Error: {e}")

        else:
            print(f"Comando desconocido: {command}")
            print("Comandos disponibles: monitor, schedule, test-openrouter")
    else:
        print("Uso: python orchestrator.py [monitor|schedule|test-openrouter]")
