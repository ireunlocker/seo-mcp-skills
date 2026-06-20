#!/usr/bin/env python3
"""
Servidor Webhook para Git Pull Automático.

Este script ejecuta un servidor HTTP que escucha peticiones POST
desde GitHub (webhook) y ejecuta git pull en el proyecto especificado.
Ideal para desplegar cambios SEO automáticamente en producción.

PRERREQUISITOS:
- Python 3.8+
- Flask: pip install flask
- Configurar variable WEBHOOK_SECRET en inputs/.env
- Configurar PROJECT_PATH en inputs/.env

USO:
  python scripts/git_pull_webhook.py

  Por defecto corre en puerto 5000.
  Configurar en GitHub: Settings > Webhooks > Add webhook
  - Payload URL: http://tu-servidor:5000/webhook/git-pull
  - Content type: application/json
  - Secret: el mismo que WEBHOOK_SECRET en .env
  - Events: Push events

CONFIGURACIÓN EN .env:
  WEBHOOK_SECRET=tu_secreto_compartido
  PROJECT_PATH=/var/www/tu-proyecto
  GIT_BRANCH=main
  AUTO_REBUILD=true  # Ejecuta pnpm build tras el pull (opcional)
  FRONTEND_PATH=app/frontend  # Ruta al frontend dentro del proyecto
"""

import os
import sys
import hmac
import hashlib
import subprocess
import logging
from typing import Optional

from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv(os.path.join(os.path.dirname(__file__), '../inputs/.env'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GitPullWebhook:
    """
    Servidor webhook que ejecuta git pull automático al recibir
    una notificación de push desde GitHub.

    Características:
    - Verificación HMAC-SHA256 del payload (seguridad)
    - Solo reacciona a pushes en la rama configurada
    - Rebuild automático del frontend si hay cambios
    - Logging detallado de cada ejecución
    """

    def __init__(
        self,
        project_path: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        branch: str = "main",
        auto_rebuild: bool = False,
        frontend_path: Optional[str] = None
    ):
        self.project_path = project_path or os.getenv("PROJECT_PATH")
        self.webhook_secret = webhook_secret or os.getenv("WEBHOOK_SECRET", "")
        self.branch = branch or os.getenv("GIT_BRANCH", "main")
        self.auto_rebuild = auto_rebuild or os.getenv("AUTO_REBUILD", "false").lower() == "true"
        self.frontend_path = frontend_path or os.getenv("FRONTEND_PATH", "app/frontend")

        if not self.project_path or not os.path.exists(self.project_path):
            raise ValueError(f"PROJECT_PATH no válido o no existe: {self.project_path}")

        logger.info(f"Webhook inicializado para: {self.project_path}")
        logger.info(f"Rama: {self.branch} | Auto-rebuild: {self.auto_rebuild}")

    def verify_signature(self, payload_body: bytes, signature_header: str) -> bool:
        """
        Verifica que el payload venga de GitHub usando HMAC-SHA256.
        """
        if not self.webhook_secret:
            logger.warning("WEBHOOK_SECRET no configurado — saltando verificación")
            return True

        expected_signature = 'sha256=' + hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload_body,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature_header)

    def is_correct_branch(self, payload: dict) -> bool:
        """
        Verifica que el push sea en la rama configurada.
        """
        ref = payload.get("ref", "")
        expected_ref = f"refs/heads/{self.branch}"
        return ref == expected_ref

    def execute_git_pull(self) -> dict:
        """
        Ejecuta git pull en el proyecto.
        """
        try:
            logger.info("Ejecutando git pull...")
            result = subprocess.run(
                ["git", "pull", "origin", self.branch],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                logger.info(f"Git pull exitoso: {result.stdout[:200]}")
                return {
                    "status": "success",
                    "message": result.stdout.strip(),
                    "changes": "Already up to date." not in result.stdout
                }
            else:
                logger.error(f"Error en git pull: {result.stderr}")
                return {"status": "error", "message": result.stderr}

        except subprocess.TimeoutExpired:
            logger.error("Git pull timed out (60s)")
            return {"status": "error", "message": "Timeout"}
        except Exception as e:
            logger.error(f"Error inesperado en git pull: {e}")
            return {"status": "error", "message": str(e)}

    def rebuild_frontend(self) -> dict:
        """
        Reconstruye el frontend si hay cambios.
        """
        if not self.auto_rebuild:
            return {"status": "skipped", "message": "Auto-rebuild disabled"}

        frontend_dir = os.path.join(self.project_path, self.frontend_path)
        if not os.path.exists(frontend_dir):
            logger.warning(f"Frontend dir no encontrado: {frontend_dir}")
            return {"status": "skipped", "message": "Frontend path not found"}

        try:
            logger.info("Reconstruyendo frontend...")
            result = subprocess.run(
                ["pnpm", "build"],
                cwd=frontend_dir,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                logger.info("Build exitoso")
                return {"status": "success", "message": result.stdout[:200]}
            else:
                logger.error(f"Error en build: {result.stderr[:200]}")
                return {"status": "error", "message": result.stderr[:200]}

        except Exception as e:
            logger.error(f"Error en rebuild: {e}")
            return {"status": "error", "message": str(e)}

    def handle_webhook(self, payload: dict, signature: str = "") -> dict:
        """
        Maneja una petición webhook completa:
        1. Verifica firma
        2. Verifica rama
        3. Ejecuta git pull
        4. Rebuild si aplica
        """
        if not self.verify_signature(
            str(payload).encode('utf-8') if isinstance(payload, dict) else b'',
            signature
        ):
            logger.warning("Firma inválida — rechazando webhook")
            return {"status": "error", "message": "Invalid signature"}

        if not self.is_correct_branch(payload):
            logger.info(f"Push en rama diferente — ignorando. Ref: {payload.get('ref', 'unknown')}")
            return {"status": "skipped", "message": "Wrong branch"}

        pull_result = self.execute_git_pull()

        if pull_result["status"] == "success" and pull_result.get("changes"):
            rebuild_result = self.rebuild_frontend()
            pull_result["rebuild"] = rebuild_result

        return pull_result


def create_app():
    """
    Crea la aplicación Flask para el servidor webhook.
    """
    try:
        from flask import Flask, request, jsonify
    except ImportError:
        print("Error: Flask no está instalado. Ejecuta: pip install flask")
        sys.exit(1)

    app = Flask(__name__)
    webhook_handler = GitPullWebhook()

    @app.route("/webhook/git-pull", methods=["POST"])
    def webhook_git_pull():
        """
        Endpoint principal del webhook.
        Recibe POST desde GitHub con el payload del push.
        """
        # Verificar firma si existe
        signature = request.headers.get("X-Hub-Signature-256", "")
        payload = request.get_json()

        if not payload:
            return jsonify({"status": "error", "message": "No payload"}), 400

        result = webhook_handler.handle_webhook(payload, signature)

        status_code = 200 if result["status"] == "success" else 400
        return jsonify(result), status_code

    @app.route("/health", methods=["GET"])
    def health():
        """Health check para monitoreo."""
        return jsonify({
            "status": "ok",
            "project": webhook_handler.project_path,
            "branch": webhook_handler.branch
        })

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("WEBHOOK_PORT", "5000"))
    logger.info(f"Iniciando servidor webhook en puerto {port}...")
    app.run(host="0.0.0.0", port=port)
