#!/usr/bin/env python3
"""
Cliente para la API de OpenRouter con soporte para Function Calling.

Este módulo proporciona una interfaz unificada para interactuar con modelos de
lenguaje a través de la plataforma OpenRouter (https://openrouter.ai), que da
acceso a múltiples proveedores (DeepSeek, OpenAI, Anthropic, Google, Meta, etc.)
desde una única API compatible con el formato de OpenAI.

PRERREQUISITOS:
- Python 3.12+
- Dependencias: openai, python-dotenv
- Archivo inputs/.env con OPENROUTER_API_KEY configurada

CONFIGURACIÓN:
1. Obtén una API key en https://openrouter.ai/keys
2. Agrégala a inputs/.env: OPENROUTER_API_KEY=tu_clave_aqui
3. Opcionalmente define el modelo por defecto en la instanciación.

MECANISMO DE FALLBACK:
El cliente implementa un sistema de reintento con lista ordenada de modelos.
Cuando el modelo principal falla (por límite de tasa, cuota agotada o error
del proveedor), se prueba automáticamente el siguiente modelo de la lista.
Esto garantiza robustez en entornos de producción donde algún proveedor
puede estar temporalmente no disponible. Los modelos de respaldo incluyen
DeepSeek Chat, GLM-4, Claude 3.5 Sonnet, Llama 3.1 70B, Gemini 2.5 Pro y GPT-4o,
ordenados por equilibrio entre capacidad de Function Calling, calidad y costo.

USO:
  from openrouter_client import OpenRouterClient

  client = OpenRouterClient()
  response = client.generate_content("Hola, ¿qué servicios ofrecen?")
  print(response["text"])

  # Con Function Calling
  schema = {...}
  response = client.generate_content(prompt, functions=[schema], function_call={"name": "mi_funcion"})

INTEGRACIÓN:
Este cliente es consumido por SEOOrchestrator (orchestrator.py) para ejecutar
skills SEO mediante Function Calling. También es usado por UniversalSEOAgent
(universal_seo_agent.py) como motor de lenguaje principal del agente autónomo.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../inputs/.env'))

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """
    Cliente para la API de OpenRouter con soporte de Function Calling.

    Utiliza la librería OpenAI como interfaz gracias a que OpenRouter es
    completamente compatible con el formato de la API de OpenAI.

    Attributes:
        api_key: Clave de API de OpenRouter.
        client: Instancia de OpenAI configurada con la base_url de OpenRouter.
        model: Identificador del modelo por defecto (ej: deepseek/deepseek-chat).
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "deepseek/deepseek-chat"):
        """
        Inicializa el cliente de OpenRouter.

        Args:
            api_key: Clave API de OpenRouter. Si no se provee, lee
                     OPENROUTER_API_KEY del archivo .env.
            model: Modelo a usar por defecto. Se recomienda deepseek/deepseek-chat
                   por su excelente relación calidad-precio y soporte de Function Calling.

        Raises:
            ValueError: Si no se encuentra la API key.
            ImportError: Si no está instalada la librería openai.
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY no encontrada. Configura el .env o pasa api_key.")

        try:
            from openai import OpenAI
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.api_key,
            )
            self.model = model
            logger.info(f"OpenRouterClient inicializado con modelo: {model}")
        except ImportError:
            raise ImportError("Instala openai: pip install openai")

    def generate_content(
        self,
        prompt: str,
        functions: Optional[List[Dict]] = None,
        function_call: Any = "auto"
    ) -> Dict[str, Any]:
        """
        Genera contenido usando OpenRouter, opcionalmente con Function Calling.

        Implementa un mecanismo de fallback: si el modelo configurado falla,
        prueba automáticamente con los modelos de respaldo en orden de preferencia.
        Los fallbacks están ordenados por equilibrio entre capacidad de Function
        Calling, calidad de respuesta y costo económico.

        Args:
            prompt: Texto de entrada para el modelo.
            functions: Lista de esquemas de función compatibles con OpenAI/OpenRouter.
            function_call: Control de llamada a funciones. Puede ser "auto", "none",
                          o un dict con {"name": "nombre_funcion"} para forzar una función.

        Returns:
            Diccionario con:
                - "text": Contenido textual de la respuesta.
                - "function_calls": Lista de llamadas a funciones detectadas.
                - "raw": Respuesta completa de la API (para depuración).

        Raises:
            Exception: Si todos los modelos de la lista de fallback fallan.
        """
        # Lista de modelos por orden de preferencia
        fallback_models = [
            self.model,
            "deepseek/deepseek-chat",
            "zhipu/glm-4",
            "anthropic/claude-3.5-sonnet",
            "meta-llama/llama-3.1-70b-instruct",
            "google/gemini-2.5-pro",
            "openai/gpt-4o"
        ]

        # Eliminar duplicados manteniendo el orden original
        models_to_try = []
        for m in fallback_models:
            if m not in models_to_try:
                models_to_try.append(m)

        last_error = None

        for current_model in models_to_try:
            try:
                logger.info(f"Intentando generar contenido con el modelo: {current_model}")

                messages = [{"role": "user", "content": prompt}]

                # Convertir los esquemas de función al formato tools de OpenAI
                tools = []
                if functions:
                    for f in functions:
                        tools.append({
                            "type": "function",
                            "function": f
                        })

                tool_choice = "auto"
                if isinstance(function_call, dict) and "name" in function_call:
                    tool_choice = {"type": "function", "function": {"name": function_call["name"]}}

                kwargs = {
                    "model": current_model,
                    "messages": messages,
                    "temperature": 0.7,
                    "top_p": 0.95,
                }

                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = tool_choice

                response = self.client.chat.completions.create(**kwargs)
                message = response.choices[0].message

                result = {
                    "text": message.content or "",
                    "function_calls": [],
                    "raw": response
                }

                # Extraer llamadas a funciones del formato tools (OpenAI nativo)
                if message.tool_calls:
                    for tc in message.tool_calls:
                        if tc.type == "function":
                            result["function_calls"].append({
                                "name": tc.function.name,
                                "args": json.loads(tc.function.arguments) if tc.function.arguments else {}
                            })
                # Compatibilidad con formato legacy function_call
                elif getattr(message, "function_call", None):
                    result["function_calls"].append({
                        "name": message.function_call.name,
                        "args": json.loads(message.function_call.arguments) if message.function_call.arguments else {}
                    })

                logger.info(f"Éxito con el modelo: {current_model}")
                return result

            except Exception as e:
                logger.warning(f"Error con el modelo {current_model}: {e}")
                last_error = e
                continue

        logger.error(f"Todos los modelos fallaron. Último error: {last_error}")
        raise last_error


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        client = OpenRouterClient()
        response = client.generate_content("Hola, ¿puedes decirme qué es una hipoteca fija?")
        print("Respuesta de OpenRouter:")
        print(response["text"])
    except Exception as e:
        print(f"Error: {e}")
        print("Asegúrate de configurar OPENROUTER_API_KEY en inputs/.env")
