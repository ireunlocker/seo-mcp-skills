#!/usr/bin/env python3
"""
Script de automatización Git para proyectos web.

Este módulo proporciona una clase que automatiza el flujo de trabajo Git:
add, commit y push al repositorio remoto. Está diseñado para ser usado por
el orquestador SEO tras realizar cambios automatizados en los archivos del
proyecto (ej: mejoras SEO en páginas, actualización de sitemaps).

PRERREQUISITOS:
- Python 3.12+
- Git instalado y configurado en el sistema.
- El directorio del proyecto debe ser un repositorio Git válido.
- Dependencias: python-dotenv

CONFIGURACIÓN DEL REMOTO:
El repositorio remoto se configura en inputs/.env:
  PROJECT_PATH=/ruta/a/tu/proyecto
  REPO_REMOTE=https://github.com/usuario/repo.git

Opcionalmente se puede pasar la ruta, URL remota y rama directamente
al constructor.

USO:
  from git_auto_push import GitAutoPush

  git = GitAutoPush("/ruta/al/proyecto")
  status = git.get_status()
  if status:
      result = git.commit_and_push("auto: mejora SEO aplicada")
      print(result)

INTEGRACIÓN:
Consumido por SEOOrchestrator (orchestrator.py) y SitemapUpdater
(sitemap_updater.py) para registrar automáticamente los cambios realizados
durante los ciclos de monitoreo y actualización SEO.
"""

import os
import subprocess
import logging
from typing import Dict, Any
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../inputs/.env'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GitAutoPush:
    """
    Automatiza el flujo Git: add, commit y push.

    Gestiona el ciclo completo de control de versiones para cambios
    automatizados, con manejo de errores y mensajes de commit
    generados automáticamente si no se proporcionan.
    """

    def __init__(self, project_path: str = None, remote_url: str = None, branch: str = "main"):
        """
        Inicializa el cliente Git.

        Args:
            project_path: Ruta absoluta al repositorio local.
                          Si no se provee, usa PROJECT_PATH del .env.
            remote_url: URL del repositorio remoto.
                        Si no se provee, usa REPO_REMOTE del .env.
            branch: Nombre de la rama (por defecto "main").

        Raises:
            ValueError: Si la ruta del proyecto no es válida o no es un repo Git.
        """
        self.project_path = project_path or os.getenv("PROJECT_PATH")
        self.remote_url = remote_url or os.getenv("REPO_REMOTE")
        self.branch = branch

        if not self.project_path or not os.path.exists(self.project_path):
            raise ValueError(f"Ruta del proyecto no válida: {self.project_path}")

        git_dir = os.path.join(self.project_path, ".git")
        if not os.path.exists(git_dir):
            raise ValueError(f"El directorio {self.project_path} no es un repositorio Git")

        logger.info(f"GitAutoPush inicializado para: {self.project_path}")
        logger.info(f"Remote: {self.remote_url}, Branch: {self.branch}")

    def get_status(self) -> str:
        """
        Obtiene el estado del repositorio Git (archivos modificados).

        Ejecuta `git status --porcelain` y devuelve la salida. Si no hay
        cambios, devuelve una cadena vacía.

        Returns:
            String con los cambios detectados, o vacío si no hay cambios.
        """
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.project_path,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()

    def commit_and_push(self, commit_message: str = None) -> Dict[str, Any]:
        """
        Realiza git add ., commit y push al remoto.

        El flujo es:
        1. Verifica si hay cambios con get_status().
        2. Si no hay cambios, retorna inmediatamente.
        3. Ejecuta git add . para stagear todos los cambios.
        4. Ejecuta git commit con el mensaje proporcionado o uno automático.
        5. Ejecuta git push a origin/{branch}.

        Args:
            commit_message: Mensaje para el commit. Si no se provee,
                           se genera uno automático con la fecha actual.

        Returns:
            Diccionario con estado de la operación:
                - status: "no_changes", "success", "push_failed", o "error".
                - commit_message: Mensaje usado.
                - push_output/stdout: Salida del push (si fue exitoso).
                - error: Mensaje de error (si falló).
        """
        status = self.get_status()
        if not status:
            logger.info("No hay cambios para commitear")
            return {"status": "no_changes"}

        if not commit_message:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_message = f"auto: actualización SEO {timestamp}"

        try:
            # Git add . — stagea todos los cambios del repositorio
            subprocess.run(["git", "add", "."], cwd=self.project_path, check=True)
            logger.info("✓ git add . completado")

            # Git commit con el mensaje
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=self.project_path,
                check=True
            )
            logger.info(f"✓ git commit: {commit_message}")

            # Git push a la rama remota
            push_result = subprocess.run(
                ["git", "push", "origin", self.branch],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )

            if push_result.returncode == 0:
                logger.info(f"✓ git push exitoso a {self.branch}")
                return {
                    "status": "success",
                    "commit_message": commit_message,
                    "push_output": push_result.stdout
                }
            else:
                logger.error(f"✗ Error en git push: {push_result.stderr}")
                return {
                    "status": "push_failed",
                    "error": push_result.stderr
                }

        except subprocess.CalledProcessError as e:
            logger.error(f"✗ Error en Git: {e}")
            return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    try:
        git = GitAutoPush()
        print("Estado actual:")
        status = git.get_status()
        print(status if status else "No hay cambios")

        if status:
            print("\nHaciendo commit y push automático...")
            result = git.commit_and_push()
            print(f"Resultado: {result}")
    except Exception as e:
        print(f"Error: {e}")
