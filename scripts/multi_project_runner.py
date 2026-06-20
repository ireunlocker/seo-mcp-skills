#!/usr/bin/env python3
"""
Ejecutor Multi-Proyecto para SEO MCP Skill.

Este script permite ejecutar el orquestador SEO para múltiples proyectos
de forma secuencial, cargando diferentes configuraciones de entorno para
cada cliente.

Útil para agencias o freelancers que gestionan el SEO de varios sitios web.

USO:
  python scripts/multi_project_runner.py

CONFIGURACIÓN:
  Crear un archivo .env por proyecto en inputs/:
    inputs/.env-cliente-a
    inputs/.env-cliente-b
    inputs/.env-cliente-c

  Luego modificar la lista PROYECTOS en este script.

ESTRUCTURA DEL .env POR PROYECTO:
  PROJECT_PATH=/var/www/cliente-a
  OPENROUTER_API_KEY=sk-or-v1-...
  GSC_SITE_URL=https://cliente-a.com
  # ... demas variables

MODO MONITOREO:
  python scripts/multi_project_runner.py monitor   # Un ciclo por proyecto
  python scripts/multi_project_runner.py schedule  # Todos programados
  python scripts/multi_project_runner.py list      # Listar proyectos configurados
"""

import os
import sys
import json
import logging
import schedule
import time
from datetime import datetime
from typing import List, Dict, Any

from dotenv import load_dotenv

# Asegurar que el directorio raíz está en el path
_scripts_dir = os.path.dirname(os.path.abspath(__file__))
if _scripts_dir not in sys.path:
    sys.path.insert(0, os.path.dirname(_scripts_dir))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), '../outputs/multi_project.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# ============================================================
# LISTA DE PROYECTOS
# ============================================================
# Agrega aquí todos los proyectos que quieras monitorear.
# Cada proyecto debe tener su propio archivo .env en inputs/
# y una carpeta de contexto en config/context/<slug>/
# ============================================================

PROYECTOS = [
    {
        "nombre": "Mi Proyecto Web",
        "slug": "mi-web",
        "env_file": "inputs/.env",
        "context_dir": "config/context",
        "horario_monitoreo": "08:00",
        "horario_auditoria": "10:00",
        "activo": True
    },
    # Ejemplo: descomentar para agregar más proyectos
    # {
    #     "nombre": "Cliente A - E-commerce",
    #     "slug": "cliente-a",
    #     "env_file": "inputs/.env-cliente-a",
    #     "context_dir": "config/context/cliente-a",
    #     "horario_monitoreo": "08:30",
    #     "horario_auditoria": "10:30",
    #     "activo": True
    # },
    # {
    #     "nombre": "Cliente B - Seguros",
    #     "slug": "cliente-b",
    #     "env_file": "inputs/.env-cliente-b",
    #     "context_dir": "config/context/cliente-b",
    #     "horario_monitoreo": "09:00",
    #     "horario_auditoria": "11:00",
    #     "activo": True
    # },
]


class MultiProjectRunner:
    """
    Ejecuta el orquestador SEO para múltiples proyectos de forma secuencial.

    Para cada proyecto:
    1. Carga su archivo .env específico
    2. Sobrescribe las variables de entorno
    3. Crea una instancia del orquestador con la configuración cargada
    4. Ejecuta monitoreo o auditoría según el comando
    5. Registra resultados en el log del proyecto correspondiente
    """

    def __init__(self, proyectos: List[Dict[str, Any]]):
        self.proyectos = [p for p in proyectos if p.get("activo", True)]
        logger.info(f"MultiProjectRunner inicializado con {len(self.proyectos)} proyectos activos")

    def cargar_env_proyecto(self, proyecto: Dict[str, Any]):
        """
        Carga las variables de entorno de un proyecto específico.
        Usa override=True para asegurar que las variables se sobrescriban.
        """
        env_path = os.path.join(os.path.dirname(__file__), '..', proyecto["env_file"])

        if not os.path.exists(env_path):
            logger.error(f"Archivo .env no encontrado para {proyecto['nombre']}: {env_path}")
            return False

        # Limpiar variables anteriores del orquestador
        for key in ["PROJECT_PATH", "REPO_REMOTE", "GSC_SITE_URL", "GA4_PROPERTY_ID",
                     "OPENROUTER_API_KEY", "GEMINI_API_KEY", "BACKEND_API_URL",
                     "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "FRONTEND_PATH"]:
            if key in os.environ:
                del os.environ[key]

        # Cargar el .env del proyecto
        load_dotenv(env_path, override=True)
        logger.info(f"Variables cargadas para: {proyecto['nombre']} desde {env_path}")
        return True

    def ejecutar_monitoreo(self, proyecto: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta un ciclo de monitoreo completo para un proyecto.
        """
        from scripts.orchestrator import SEOOrchestrator

        if not self.cargar_env_proyecto(proyecto):
            return {"proyecto": proyecto["nombre"], "status": "error", "error": "Env no encontrado"}

        try:
            logger.info(f"=== Ejecutando monitoreo para: {proyecto['nombre']} ===")
            orch = SEOOrchestrator()
            resultado = orch.automated_seo_monitoring()
            logger.info(f"Monitoreo completado para {proyecto['nombre']}: {resultado.get('status')}")
            return {
                "proyecto": proyecto["nombre"],
                "status": resultado.get("status", "unknown"),
                "report_path": resultado.get("report_path", ""),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error en monitoreo de {proyecto['nombre']}: {e}")
            return {"proyecto": proyecto["nombre"], "status": "error", "error": str(e)}

    def ejecutar_auditoria(self, proyecto: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta auditoría SEO por página para un proyecto.
        """
        from scripts.orchestrator import SEOOrchestrator

        if not self.cargar_env_proyecto(proyecto):
            return {"proyecto": proyecto["nombre"], "status": "error", "error": "Env no encontrado"}

        try:
            logger.info(f"=== Ejecutando auditoría para: {proyecto['nombre']} ===")
            orch = SEOOrchestrator()
            orch.automated_seo_monitoring_per_page()
            logger.info(f"Auditoría completada para {proyecto['nombre']}")
            return {
                "proyecto": proyecto["nombre"],
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error en auditoría de {proyecto['nombre']}: {e}")
            return {"proyecto": proyecto["nombre"], "status": "error", "error": str(e)}

    def ejecutar_todos(self, comando: str = "monitor") -> List[Dict[str, Any]]:
        """
        Ejecuta un comando en todos los proyectos activos.
        """
        resultados = []
        logger.info(f"Ejecutando '{comando}' en {len(self.proyectos)} proyectos...")

        for proyecto in self.proyectos:
            if comando == "monitor":
                resultado = self.ejecutar_monitoreo(proyecto)
            elif comando == "audit":
                resultado = self.ejecutar_auditoria(proyecto)
            else:
                resultado = {"proyecto": proyecto["nombre"], "status": "error", "error": f"Comando desconocido: {comando}"}

            resultados.append(resultado)

        return resultados

    def listar_proyectos(self):
        """Muestra los proyectos configurados."""
        print(f"\n{'='*60}")
        print(f"  PROYECTOS CONFIGURADOS ({len(self.proyectos)} activos)")
        print(f"{'='*60}")
        for p in self.proyectos:
            print(f"  📁 {p['nombre']}")
            print(f"     Env: {p['env_file']}")
            print(f"     Monitoreo: {p.get('horario_monitoreo', 'N/A')}")
            print(f"     Auditoría: {p.get('horario_auditoria', 'N/A')}")
            print()
        print(f"{'='*60}\n")

    def programar_tareas(self):
        """Programa tareas para todos los proyectos."""
        for proyecto in self.proyectos:
            if proyecto.get("horario_monitoreo"):
                schedule.every().day.at(proyecto["horario_monitoreo"]).do(
                    self.ejecutar_monitoreo, proyecto
                )
                logger.info(f"Monitoreo programado para {proyecto['nombre']} a las {proyecto['horario_monitoreo']}")

            if proyecto.get("horario_auditoria"):
                schedule.every().day.at(proyecto["horario_auditoria"]).do(
                    self.ejecutar_auditoria, proyecto
                )
                logger.info(f"Auditoría programada para {proyecto['nombre']} a las {proyecto['horario_auditoria']}")

    def run_scheduler(self):
        """Ejecuta el planificador multi-proyecto."""
        self.programar_tareas()
        logger.info("Iniciando planificador multi-proyecto... (Ctrl+C para detener)")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Planificador detenido por el usuario")


if __name__ == "__main__":
    runner = MultiProjectRunner(PROYECTOS)

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "monitor":
            resultados = runner.ejecutar_todos("monitor")
            print(json.dumps(resultados, indent=2, ensure_ascii=False))

        elif command == "audit":
            resultados = runner.ejecutar_todos("audit")
            print(json.dumps(resultados, indent=2, ensure_ascii=False))

        elif command == "schedule":
            runner.run_scheduler()

        elif command == "list":
            runner.listar_proyectos()

        else:
            print(f"Comando desconocido: {command}")
            print("Comandos: monitor, audit, schedule, list")
    else:
        print("Uso: python scripts/multi_project_runner.py [monitor|audit|schedule|list]")
        print("\nPrimero configura los proyectos en la variable PROYECTOS de este script.")
