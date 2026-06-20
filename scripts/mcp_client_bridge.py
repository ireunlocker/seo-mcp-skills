#!/usr/bin/env python3
"""
Puente universal para el Model Context Protocol (MCP) en SEO.

Este módulo implementa un cliente MCP (Model Context Protocol) que permite
conectar modelos de lenguaje con herramientas externas (navegador web,
Google Search Console, análisis de URLs, etc.) mediante el protocolo
estándar de contexto. El puente traduce automáticamente las herramientas
MCP al formato de Function Calling de OpenAI/OpenRouter, permitiendo que
cualquier modelo de lenguaje las utilice de forma nativa.

¿QUÉ ES MCP?
MCP (Model Context Protocol) es un protocolo abierto desarrollado por
Anthropic que estandariza cómo los modelos de lenguaje pueden interactuar
con herramientas y fuentes de datos externas. Cada servidor MCP expone
herramientas que el modelo puede invocar, similar a las funciones en
OpenAI Function Calling.

PRERREQUISITOS:
- Python 3.12+
- Dependencias: mcp (pip install mcp), httpx, python-dotenv
- Servidores MCP instalados (ej: @modelcontextprotocol/server-puppeteer)

USO:
  servers = [
      {"name": "browser", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-puppeteer"]}
  ]
  bridge = UniversalMCPBridge(servers)
  await bridge.initialize()
  tools = await bridge.get_all_tools_for_llm()
  result = await bridge.execute_tool("browser__navigate", {"url": "https://ejemplo.com"})
  await bridge.close()

INTEGRACIÓN:
Usado por UniversalSEOAgent (universal_seo_agent.py) como capa de conexión
entre el modelo de lenguaje (OpenRouter) y las herramientas MCP. El agente
obtiene las herramientas disponibles, las pasa al modelo, y ejecuta las
llamadas a herramientas que el modelo decida realizar.
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, List

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UniversalMCPBridge:
    """
    Puente universal para conectar modelos de lenguaje con servidores MCP.

    Gestiona la conexión, inicialización y comunicación con múltiples
    servidores MCP simultáneamente. Proporciona métodos para listar
    herramientas disponibles y ejecutarlas bajo demanda.
    """

    def __init__(self, mcp_servers_config: List[Dict[str, Any]]):
        """
        Inicializa el puente con la configuración de servidores MCP.

        Args:
            mcp_servers_config: Lista de diccionarios, cada uno con:
                - "name": Nombre identificador del servidor.
                - "command": Comando para iniciar el servidor.
                - "args": Lista de argumentos del comando.
                - "env" (opcional): Variables de entorno para el servidor.
        """
        self.server_configs = mcp_servers_config
        self.sessions = {}
        self.exit_stack = None

    async def initialize(self):
        """
        Inicializa todos los servidores MCP configurados.

        Para cada servidor en la configuración:
        1. Crea los parámetros de conexión (StdioServerParameters).
        2. Inicia el proceso del servidor via stdio_client.
        3. Crea una sesión MCP y la inicializa.
        4. Almacena la sesión para uso posterior.

        Todas las conexiones se gestionan con AsyncExitStack para
        garantizar la limpieza incluso si ocurre un error.
        """
        from contextlib import AsyncExitStack
        self.exit_stack = AsyncExitStack()

        for config in self.server_configs:
            server_name = config["name"]
            command = config["command"]
            args = config["args"]
            env = config.get("env", None)

            logger.info(f"Conectando al servidor MCP: {server_name}...")
            server_params = StdioServerParameters(command=command, args=args, env=env)

            # Iniciar proceso del servidor MCP
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            read, write = stdio_transport

            # Crear y inicializar sesión MCP
            session = await self.exit_stack.enter_async_context(ClientSession(read, write))
            await session.initialize()

            self.sessions[server_name] = session
            logger.info(f"Servidor MCP {server_name} conectado exitosamente.")

    async def get_all_tools_for_llm(self) -> List[Dict[str, Any]]:
        """
        Obtiene todas las herramientas de todos los servidores MCP conectados
        y las convierte al formato de Function Calling de OpenAI/OpenRouter.

        Cada herramienta recibe un prefijo con el nombre del servidor
        (ej: "browser__navigate") para que el modelo pueda identificar
        qué servidor debe ejecutar la herramienta.

        Returns:
            Lista de herramientas en formato OpenAI tool (type: "function").
        """
        all_tools = []
        for server_name, session in self.sessions.items():
            result = await session.list_tools()
            for tool in result.tools:
                openrouter_tool = {
                    "type": "function",
                    "function": {
                        "name": f"{server_name}__{tool.name}",
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                }
                all_tools.append(openrouter_tool)
        return all_tools

    async def execute_tool(self, tool_name_with_prefix: str, arguments: Dict[str, Any]) -> Any:
        """
        Ejecuta una herramienta en el servidor MCP correspondiente.

        El nombre de la herramienta debe incluir el prefijo del servidor
        (formato: "server_name__tool_name"), que es como se entregan al
        modelo de lenguaje.

        Args:
            tool_name_with_prefix: Nombre completo con prefijo (ej: "browser__navigate").
            arguments: Diccionario con los argumentos de la herramienta.

        Returns:
            Resultado de la ejecución de la herramienta.

        Raises:
            ValueError: Si el formato del nombre es inválido o el servidor
                       no está conectado.
        """
        parts = tool_name_with_prefix.split("__", 1)
        if len(parts) != 2:
            raise ValueError(f"Nombre de herramienta inválido: {tool_name_with_prefix}")

        server_name, tool_name = parts

        if server_name not in self.sessions:
            raise ValueError(f"Servidor MCP no encontrado: {server_name}")

        session = self.sessions[server_name]
        logger.info(f"Ejecutando herramienta {tool_name} en {server_name}...")

        result = await session.call_tool(tool_name, arguments)
        return result

    async def close(self):
        """
        Cierra todas las conexiones MCP activas de forma segura.

        Usa el AsyncExitStack para garantizar que todos los contextos
        abiertos (procesos y sesiones) se cierren correctamente,
        liberando los recursos del sistema.
        """
        if self.exit_stack:
            await self.exit_stack.aclose()
            logger.info("Conexiones MCP cerradas.")


# Ejemplo de uso ejecutable (descomentado pero guardado con condición)
async def main():
    """
    Ejemplo de uso del UniversalMCPBridge.

    Conecta un servidor Puppeteer, lista sus herramientas disponibles
    y las muestra en formato JSON.
    """
    servers = [
        {"name": "puppeteer", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-puppeteer"]},
    ]
    bridge = UniversalMCPBridge(servers)
    await bridge.initialize()
    tools = await bridge.get_all_tools_for_llm()
    print(json.dumps(tools, indent=2))
    await bridge.close()

if __name__ == "__main__":
    asyncio.run(main())
