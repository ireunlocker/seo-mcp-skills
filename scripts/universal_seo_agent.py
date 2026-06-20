#!/usr/bin/env python3
"""
Agente SEO Universal basado en MCP (Model Context Protocol).

Este módulo implementa un agente autónomo de SEO que combina modelos de
lenguaje (via OpenRouter) con herramientas MCP para ejecutar auditorías,
scraping, análisis de competencia y correcciones en cualquier proyecto web.

El agente funciona de la siguiente manera:
1. Conecta con servidores MCP (navegador, GSC, etc.) que exponen herramientas.
2. Obtiene el esquema de todas las herramientas disponibles.
3. Envía un prompt al modelo de lenguaje junto con las herramientas.
4. El modelo decide qué herramientas invocar para completar la tarea.
5. El agente ejecuta las herramientas y devuelve los resultados al modelo.

PRERREQUISITOS:
- Python 3.12+
- Dependencias: openai, httpx, mcp, python-dotenv
- Un servidor MCP instalado (ej: npx @modelcontextprotocol/server-puppeteer)
- OPENROUTER_API_KEY configurada en inputs/.env o variable de entorno

CONFIGURACIÓN:
Configura OPENROUTER_API_KEY en inputs/.env o como variable de entorno.
Los servidores MCP y la ruta del proyecto se configuran en el código
o se pasan al constructor del agente.

USO:
  export RUN_UNIVERSAL_AGENT=1
  python3 scripts/universal_seo_agent.py

  # O desde código:
  agent = UniversalSEOAgent("/ruta/proyecto", mcp_servers)
  await agent.run_task("Analiza las keywords de la competencia")

INTEGRACIÓN:
Este es el agente más avanzado del sistema. Combina UniversalMCPBridge
(mcp_client_bridge.py) para las herramientas y OpenRouterClient
(openrouter_client.py) para el modelo de lenguaje. Puede reemplazar
al SEOOrchestrator (orchestrator.py) para tareas más complejas que
requieran interacción con páginas web externas.
"""

import asyncio
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

from mcp_client_bridge import UniversalMCPBridge
from openrouter_client import OpenRouterClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("UniversalSEOAgent")


class UniversalSEOAgent:
    """
    Agente SEO autónomo y agnóstico basado en MCP.

    Conecta modelos de lenguaje con herramientas MCP para realizar tareas
    SEO complejas: auditorías de páginas, análisis de competencia, scraping,
    consultas a Google Search Console, y modificación de archivos locales.

    El agente es agnóstico del proyecto: funciona con cualquier sitio web
    configurando los servidores MCP y la ruta del proyecto adecuados.
    """

    def __init__(self, target_project_path: str, mcp_servers: list):
        """
        Inicializa el agente SEO universal.

        Args:
            target_project_path: Ruta absoluta al proyecto web del cliente.
            mcp_servers: Lista de configuraciones de servidores MCP según
                        el formato de UniversalMCPBridge.
        """
        self.project_path = target_project_path
        self.mcp_servers = mcp_servers
        self.llm_client = OpenRouterClient()
        self.mcp_bridge = UniversalMCPBridge(mcp_servers)

    async def run_task(self, prompt: str):
        """
        Ejecuta una tarea SEO completa usando el modelo de lenguaje y MCP.

        Flujo de ejecución:
        1. Inicializa la conexión a todos los servidores MCP.
        2. Obtiene el listado de herramientas disponibles.
        3. Construye un payload de chat completion con las herramientas.
        4. Envía la petición a OpenRouter (API asíncrona via httpx).
        5. Si el modelo solicita ejecutar una herramienta, la ejecuta.
        6. Cierra las conexiones MCP al finalizar.

        Args:
            prompt: Instrucción en lenguaje natural para el agente
                   (ej: "Analiza las keywords del competidor X").
        """
        logger.info("=== INICIANDO TAREA SEO UNIVERSAL ===")

        await self.mcp_bridge.initialize()

        try:
            available_tools = await self.mcp_bridge.get_all_tools_for_llm()
            logger.info(f"Herramientas MCP disponibles cargadas: {len(available_tools)}")

            payload = {
                "model": "meta-llama/llama-3.1-70b-instruct",
                "messages": [
                    {"role": "system", "content": (
                        "Eres un Agente SEO Autónomo avanzado. "
                        "Usa las herramientas proporcionadas para navegar por la web, "
                        "auditar código, analizar datos de Google Search Console y "
                        "modificar archivos locales para mejorar el posicionamiento "
                        "del sitio web del cliente."
                    )},
                    {"role": "user", "content": prompt}
                ],
                "tools": available_tools,
                "tool_choice": "auto"
            }

            logger.info("Enviando petición a OpenRouter con herramientas MCP...")
            import httpx
            api_key = os.getenv("OPENROUTER_API_KEY")

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json=payload
                )

                response_data = response.json()

                message = response_data["choices"][0]["message"]
                if "tool_calls" in message and message["tool_calls"]:
                    for tool_call in message["tool_calls"]:
                        tool_name = tool_call["function"]["name"]
                        args = json.loads(tool_call["function"]["arguments"])

                        logger.info(f"🛠 La IA solicitó ejecutar MCP: {tool_name} con args: {args}")

                        resultado = await self.mcp_bridge.execute_tool(tool_name, args)
                        logger.info(f"✅ Resultado de MCP obtenido.")
                else:
                    logger.info("La IA respondió directamente sin usar herramientas.")
                    logger.info(message["content"])

        except Exception as e:
            logger.error(f"Error durante la ejecución del Agente Universal: {e}")
        finally:
            await self.mcp_bridge.close()


# Ejemplo de uso ejecutable (activado con variable de entorno)
async def main():
    """
    Ejemplo de configuración y ejecución del agente universal.

    Para ejecutar: export RUN_UNIVERSAL_AGENT=1
    """
    config_cliente = {
        "project_path": "/ruta/al/proyecto/del/cliente",
        "mcp_servers": [
            {
                "name": "browser",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
            }
        ]
    }

    agent = UniversalSEOAgent(
        config_cliente["project_path"],
        config_cliente["mcp_servers"]
    )
    await agent.run_task(
        "Busca en Google 'servicios económicos Madrid' usando el navegador, "
        "dime qué escriben los 3 primeros resultados, "
        "y sugiere cómo mejorar nuestro artículo."
    )

if __name__ == "__main__":
    if os.getenv("RUN_UNIVERSAL_AGENT"):
        asyncio.run(main())
    else:
        logger.info(
            "Agente universal preparado. "
            "Ejecuta: export RUN_UNIVERSAL_AGENT=1 && python3 scripts/universal_seo_agent.py"
        )
