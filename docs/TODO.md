# Pendientes para Automatización SEO 100% Autónoma

Este documento lista las tareas exactas que faltan para que el proyecto pueda ejecutarse de forma independiente, basado en datos reales y sin errores.

## 1. Credenciales de Google Search Console (El Cerebro)
Para que la IA no modifique textos a ciegas, necesita conectarse a tu panel de GSC.
**Acción requerida (Usuario):**
- Ir a Google Cloud Console.
- Crear una "Service Account" (Cuenta de Servicio).
- Descargar la clave privada en formato `.json` (ej: `credenciales-gsc.json`).
- Ir a tu panel de Google Search Console y añadir el correo de esa Service Account como "Lector" o "Propietario".
- Guardar el `.json` en el servidor VPS (ej: en la carpeta `inputs/`).

## 2. Conectar con el Backend (El Dashboard)
El script de Python intenta enviar un resumen de lo que hizo al panel de administración de tu proyecto.
**Acción requerida (Usuario):**
- Revisar que el backend de tu plataforma esté ejecutándose en el puerto configurado.
- Si están en contenedores Docker distintos, asegúrate de que el script de Python no apunte a `localhost:3001`, sino al nombre del contenedor (ej: `http://backend:3001/api/seo/reports`). Actualiza esto en tu `.env`.

## 3. IAs económicas y robustas (DeepSeek / GLM-4)
*✅ ESTE PASO YA FUE APLICADO EN EL CÓDIGO.*
El archivo `scripts/openrouter_client.py` ha sido modificado para que el orquestador intente usar `deepseek/deepseek-chat` por defecto, reduciendo drásticamente los costos de servidor mientras mantiene un excelente manejo de *Function Calling*.

## 4. Conectar el Cron Diario con el Motor Universal (MCP)
Hemos construido el `UniversalSEOAgent` con soporte para MCP.
**Acción requerida (Usuario cuando tengas las credenciales):**
- Configurar los servidores MCP en el archivo `.env` o en la configuración del agente.
- El agente Universal arrancará los servidores MCP y ejecutará el análisis cruzado y las modificaciones directas en tu proyecto de manera autónoma.

## 5. Agregar más sitios web al monitoreo
**Acción requerida (Usuario):**
- Crear archivos `.env` separados para cada cliente (ej: `inputs/.env-cliente-a`, `inputs/.env-cliente-b`).
- Usar el script `scripts/multi_project_runner.py` (próximamente) o ejecutar el orquestador con diferentes variables de entorno.

---
*Documento autogenerado para seguimiento - Actualizado: Junio 2026*
