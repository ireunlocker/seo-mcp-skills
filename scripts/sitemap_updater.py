#!/usr/bin/env python3
"""
Actualizador de sitemaps y contenido SEO para proyectos Next.js.

Este módulo proporciona funcionalidades para crear posts de blog, reconstruir
el frontend Next.js (regenerando el sitemap estático), notificar a Google
Search Console sobre cambios, y hacer Git push de las modificaciones.

PRERREQUISITOS:
- Python 3.12+
- Dependencias: python-dotenv
- Proyecto Next.js con estructura App Router
- (Opcional) gsc_client configurado para notificar a GSC
- (Opcional) git_auto_push configurado para control de versiones

CONFIGURACIÓN:
Configura en inputs/.env:
  PROJECT_PATH=/ruta/a/tu/proyecto
  FRONTEND_PATH=app/frontend  # Opcional: subdirectorio del frontend dentro del proyecto

Si no se define FRONTEND_PATH, se asume "app/frontend" como valor por defecto.

USO:
  from sitemap_updater import SitemapUpdater

  updater = SitemapUpdater()
  updater.add_blog_post("mi-post", "Título del Post", "# Contenido MDX")
  updater.rebuild_frontend()
  updater.submit_sitemap_to_gsc()

  # Ciclo completo
  results = updater.full_update_cycle([
      {"slug": "post-1", "title": "Post 1", "content_mdx": "# Hola"}
  ])

INTEGRACIÓN:
Puede ser invocado por SEOOrchestrator (orchestrator.py) dentro del ciclo de
monitoreo cuando se detecta la necesidad de crear nuevo contenido. También
puede usarse de forma independiente como script de línea de comandos.
"""

import os
import json
import subprocess
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../inputs/.env'))

logger = logging.getLogger(__name__)


class SitemapUpdater:
    """
    Gestiona la creación de contenido y actualización del sitemap.

    Proporciona métodos para crear posts de blog en formato MDX, reconstruir
    el frontend Next.js, notificar a Google Search Console y realizar el
    commit/push Git de los cambios realizados.
    """

    def __init__(self, project_path: Optional[str] = None):
        """
        Inicializa el actualizador de sitemap.

        La ruta del frontend se obtiene de la variable FRONTEND_PATH del .env
        (por defecto "app/frontend") y se combina con PROJECT_PATH.

        Args:
            project_path: Ruta absoluta al proyecto. Si no se provee,
                         usa PROJECT_PATH del .env.

        Raises:
            ValueError: Si la ruta del proyecto no es válida o no se encuentra
                       el directorio del frontend.
        """
        self.project_path = project_path or os.getenv("PROJECT_PATH")
        if not self.project_path or not os.path.exists(self.project_path):
            raise ValueError(f"Ruta del proyecto no válida: {self.project_path}")

        # FRONTEND_PATH es configurable via .env; por defecto "app/frontend"
        frontend_subpath = os.getenv("FRONTEND_PATH", "app/frontend")
        self.frontend_path = os.path.join(self.project_path, frontend_subpath)
        if not os.path.exists(self.frontend_path):
            raise ValueError(f"No se encontró frontend en: {self.frontend_path}")

        logger.info(f"SitemapUpdater inicializado para: {self.frontend_path}")

    def add_blog_post(self, slug: str, title: str, content_mdx: str = None, date: str = None, date_modified: str = None):
        """
        Crea un nuevo post de blog como archivo MDX en el sistema de archivos.

        Args:
            slug: Identificador único para la URL (ej: "mi-articulo").
            title: Título del post.
            content_mdx: Contenido en formato MDX. Si no se provee, se genera
                         un contenido por defecto.
            date: Fecha de publicación (YYYY-MM-DD). Por defecto: hoy.
            date_modified: Fecha de última modificación (YYYY-MM-DD).

        Returns:
            Diccionario con los datos del post creado (slug, title, date, dateModified).
        """
        date = date or datetime.now().strftime("%Y-%m-%d")
        date_modified = date_modified or date
        content_mdx = content_mdx or f"# {title}\n\nContenido generado automáticamente."

        post_data = {
            "slug": slug,
            "title": title,
            "date": date,
            "dateModified": date_modified
        }

        try:
            # Crear el directorio del blog siguiendo la convención Next.js App Router
            blog_dir = os.path.join(self.frontend_path, "app", "blog", slug)
            os.makedirs(blog_dir, exist_ok=True)

            # Escribir el archivo page.mdx
            mdx_path = os.path.join(blog_dir, "page.mdx")
            with open(mdx_path, "w", encoding="utf-8") as f:
                f.write(content_mdx)

            # Notificar creación via Telegram
            from telegram_notifier import TelegramNotifier
            notifier = TelegramNotifier()
            notifier.send_message(f"✅ <b>Nuevo Post Creado (Tiempo Real)</b>\n\n<b>Título:</b> {title}\n<b>Ruta:</b> /blog/{slug}")

            logger.info(f"Post creado y guardado en: {mdx_path}")
        except Exception as e:
            logger.error(f"Error creando el post físico: {e}")

        logger.info(f"Post registrado: {slug}")
        return post_data

    def rebuild_frontend(self):
        """
        Reconstruye el frontend Next.js para regenerar el sitemap estático.

        Ejecuta `pnpm build` (o `npm run build`) en el directorio del frontend.
        Esto es necesario si el sitemap se genera durante el build mediante
        next-sitemap o una estrategia similar.

        Returns:
            Diccionario con el resultado de la operación.
        """
        try:
            logger.info("Reconstruyendo frontend Next.js...")
            result = subprocess.run(
                ["pnpm", "build"],
                cwd=self.frontend_path,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                logger.info("Build exitoso - sitemap regenerado")
                return {"status": "success", "output": result.stdout}
            else:
                logger.error(f"Error en build: {result.stderr}")
                return {"status": "error", "error": result.stderr}

        except subprocess.TimeoutExpired:
            return {"status": "timeout", "error": "Build tardó más de 5 minutos"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def submit_sitemap_to_gsc(self, sitemap_url: str = None):
        """
        Verifica el estado de los sitemaps registrados en Google Search Console.

        Nota: La API de GSC no tiene un endpoint para "subir" sitemaps,
        pero permite listar los existentes para verificar que GSC los reconoce.

        Args:
            sitemap_url: URL del sitemap (no usado actualmente, mantenido
                         por compatibilidad futura).

        Returns:
            Diccionario con el resultado de la operación.
        """
        try:
            from gsc_client import GSCClient
            client = GSCClient()

            service = client.service
            site_url = client.site_url

            result = service.sitemaps().list(siteUrl=site_url).execute()

            sitemaps = result.get('sitemap', [])
            logger.info(f"GSC reconoce {len(sitemaps)} sitemaps")

            return {
                "status": "success",
                "sitemaps_count": len(sitemaps),
                "sitemaps": sitemaps
            }

        except ImportError:
            logger.warning("gsc_client no disponible, omitiendo notificación a GSC")
            return {"status": "skipped", "reason": "gsc_client not available"}
        except Exception as e:
            logger.error(f"Error notificando a GSC: {e}")
            return {"status": "error", "error": str(e)}

    def full_update_cycle(self, new_posts: List[Dict[str, Any]] = None):
        """
        Ejecuta el ciclo completo de actualización.

        Pasos:
        1. Crea los nuevos posts de blog (si se proporcionan).
        2. Reconstruye el frontend para regenerar el sitemap.
        3. Verifica los sitemaps en Google Search Console.
        4. Hace Git commit y push de todos los cambios.

        Args:
            new_posts: Lista de diccionarios con los datos de los posts a crear.
                      Cada dict debe contener las claves necesarias para add_blog_post().

        Returns:
            Diccionario con los resultados de cada paso del ciclo.
        """
        results = {}

        if new_posts:
            for post in new_posts:
                results[f"add_post_{post['slug']}"] = self.add_blog_post(**post)

        results["rebuild"] = self.rebuild_frontend()

        results["gsc_notification"] = self.submit_sitemap_to_gsc()

        try:
            from git_auto_push import GitAutoPush
            git = GitAutoPush(self.project_path)
            results["git_push"] = git.commit_and_push(
                f"auto: update sitemap {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
        except Exception as e:
            results["git_push"] = {"status": "error", "error": str(e)}

        return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        updater = SitemapUpdater()
        print("=== Actualización de Sitemap ===")

        example_post = {
            "slug": "ejemplo-guia-completa",
            "title": "Guía completa de ejemplo"
        }
        print(f"Agregando post: {example_post['slug']}")
        updater.add_blog_post(**example_post)

        print("Script listo. Ejecutar con datos reales cuando estés listo.")

    except Exception as e:
        print(f"Error: {e}")
