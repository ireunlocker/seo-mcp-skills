#!/usr/bin/env python3
"""
Notificador vía Telegram para el sistema de automatización SEO.

Este módulo proporciona una interfaz para enviar notificaciones a través de
Telegram Bot API y enviar datos a una API backend. Cubre notificaciones de
monitoreo SEO completado, solicitudes de aprobación de contenido, y envío
de reportes y métricas a la plataforma web.

PRERREQUISITOS:
- Python 3.12+
- Dependencias: requests, python-dotenv
- Un bot de Telegram creado via @BotFather y su token
- El chat ID del grupo o usuario donde se recibirán las notificaciones

CONFIGURACIÓN:
Configura en inputs/.env:
  TELEGRAM_BOT_TOKEN=tu_token_del_bot
  TELEGRAM_CHAT_ID=id_del_chat_grupo
  BACKEND_API_URL=http://localhost:3001/api  # URL de la API backend

USO:
  from telegram_notifier import TelegramNotifier

  notifier = TelegramNotifier()
  notifier.send_message("Hola, mundo!")
  notifier.notify_monitoring_complete("/ruta/reporte.md", {"status": "success"})

  # Enviar datos a la plataforma
  notifier.push_report_to_platform({"title": "Reporte", ...})
  notifier.push_metrics_to_platform({"organic_sessions": 150, ...})

INTEGRACIÓN:
Consumido por SEOOrchestrator (orchestrator.py) para notificar resultados
de monitoreo y enviar reportes/métricas a la API del backend. También usado
por SitemapUpdater (sitemap_updater.py) para notificar creación de posts.
"""

import os
import sys
import json
import logging
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

_scripts_dir = os.path.dirname(os.path.abspath(__file__))
if _scripts_dir not in sys.path:
    sys.path.insert(0, os.path.dirname(_scripts_dir))

load_dotenv(os.path.join(os.path.dirname(__file__), '../inputs/.env'))

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """
    Cliente para notificaciones Telegram y comunicación con API backend.

    Proporciona métodos para enviar mensajes a Telegram, notificar eventos
    de monitoreo SEO, solicitar aprobaciones de contenido, y enviar reportes
    y métricas a una plataforma web via HTTP.
    """

    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        """
        Inicializa el notificador Telegram.

        Args:
            bot_token: Token del bot de Telegram. Si no se provee,
                       usa TELEGRAM_BOT_TOKEN del .env.
            chat_id: ID del chat de Telegram. Si no se provee,
                     usa TELEGRAM_CHAT_ID del .env.
        """
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None
        self.backend_api_url = os.getenv("BACKEND_API_URL", "http://localhost:3001/api")

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """
        Envía un mensaje de texto al chat de Telegram configurado.

        Args:
            text: Contenido del mensaje.
            parse_mode: Modo de parseo del mensaje ("HTML" o "Markdown").

        Returns:
            True si el mensaje se envió correctamente, False en caso contrario.
        """
        if not self.api_url:
            logger.warning("TELEGRAM_BOT_TOKEN no configurado")
            return False
        try:
            resp = requests.post(
                f"{self.api_url}/sendMessage",
                json={"chat_id": self.chat_id, "text": text, "parse_mode": parse_mode},
                timeout=10
            )
            return resp.ok
        except Exception as e:
            logger.error(f"Error enviando Telegram: {e}")
            return False

    def send_approval_request(self, title: str, content: str, approval_id: str) -> bool:
        """
        Envía una solicitud de aprobación de contenido SEO por Telegram.

        Incluye un resumen del contenido y un ID único que puede usarse
        para aprobar o rechazar desde el panel de control.

        Args:
            title: Título del contenido a aprobar.
            content: Contenido o resumen del contenido (máx 800 caracteres).
            approval_id: Identificador único para la solicitud.

        Returns:
            True si se envió correctamente.
        """
        text = (
            f"<b>🔍 Solicitud de Aprobación SEO</b>\n\n"
            f"<b>{title}</b>\n\n"
            f"{content[:800]}...\n\n"
            f"<b>ID:</b> {approval_id}\n"
            f"Responde en el panel o usa /approve_{approval_id} o /reject_{approval_id}"
        )
        return self.send_message(text)

    def notify_monitoring_complete(self, report_path: str, summary: Dict[str, Any]) -> bool:
        """
        Notifica que el ciclo de monitoreo SEO ha completado.

        Args:
            report_path: Ruta al archivo de reporte generado.
            summary: Diccionario con resumen del monitoreo (status,
                    organic_sessions, keywords_count, error).

        Returns:
            True si se notificó correctamente.
        """
        status_emoji = "✅" if summary.get("status") == "success" else "❌"
        text = (
            f"{status_emoji} <b>Monitoreo SEO Completado</b>\n\n"
            f"<b>Estado:</b> {summary.get('status', 'unknown')}\n"
            f"<b>Reporte:</b> {report_path}\n"
        )
        if summary.get("organic_sessions") is not None:
            text += f"<b>Sesiones orgánicas:</b> {summary['organic_sessions']}\n"
        if summary.get("keywords_count") is not None:
            text += f"<b>Keywords registradas:</b> {summary['keywords_count']}\n"
        if summary.get("error"):
            text += f"\n<b>Error:</b> {summary['error']}"
        return self.send_message(text)

    def send_to_backend(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict]:
        """
        Envía datos a un endpoint de la API backend.

        Args:
            endpoint: Ruta del endpoint (ej: "seo/reports").
            data: Datos a enviar en el cuerpo de la petición.

        Returns:
            Respuesta JSON del backend, o None si hubo error.
        """
        try:
            resp = requests.post(
                f"{self.backend_api_url}/{endpoint}",
                json=data,
                headers={"Content-Type": "application/json", "X-SEO-Source": "python-orchestrator"},
                timeout=15
            )
            return resp.json() if resp.ok else None
        except Exception as e:
            logger.error(f"Error enviando a backend {endpoint}: {e}")
            return None

    def push_report_to_platform(self, report_data: Dict[str, Any]) -> Optional[Dict]:
        """
        Envía un reporte SEO a la plataforma web.

        Args:
            report_data: Diccionario con los datos del reporte.

        Returns:
            Respuesta del backend o None.
        """
        return self.send_to_backend("seo/reports", report_data)

    def push_metrics_to_platform(self, metrics_data: Dict[str, Any]) -> Optional[Dict]:
        """
        Envía métricas SEO a la plataforma web.

        Args:
            metrics_data: Diccionario con las métricas a enviar.

        Returns:
            Respuesta del backend o None.
        """
        return self.send_to_backend("seo/metrics", metrics_data)

    def push_content_for_approval(self, content_data: Dict[str, Any]) -> Optional[Dict]:
        """
        Envía contenido para aprobación a la plataforma web.

        Args:
            content_data: Diccionario con los datos del contenido.

        Returns:
            Respuesta del backend o None.
        """
        return self.send_to_backend("seo/content-queue", content_data)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    notifier = TelegramNotifier()
    print(f"API URL: {notifier.api_url}")
    print(f"Chat ID: {notifier.chat_id}")
    print(f"Backend URL: {notifier.backend_api_url}")
    if notifier.api_url:
        notifier.send_message("🧪 <b>Prueba</b>: Notificador SEO conectado correctamente.")
