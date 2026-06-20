#!/usr/bin/env python3
"""
Cliente para la API de Google Search Console (GSC).

Este módulo permite consultar datos de rendimiento de búsqueda de Google:
keywords, posiciones, clics, impresiones y CTR. También proporciona métodos
para leer el sitemap local y verificar el estado de indexación.

PRERREQUISITOS:
- Python 3.12+
- Dependencias: google-api-python-client, google-auth-oauthlib, python-dotenv
- Una cuenta de servicio de Google Cloud con acceso al sitio verificado en GSC
- Archivo JSON de credenciales de la cuenta de servicio

CONFIGURACIÓN:
1. Crea una cuenta de servicio en Google Cloud Console y descarga su JSON.
2. Verifica la propiedad del sitio en Google Search Console.
3. Concede acceso a la cuenta de servicio en GSC (Configuración > Usuarios).
4. Configura en inputs/.env:
     GSC_CREDENTIALS_PATH=/ruta/al/archivo.json
     GSC_SITE_URL=https://tudominio.com/

USO:
  from gsc_client import GSCClient

  client = GSCClient()
  keywords = client.get_top_keywords(days_back=7, limit=20)
  for kw in keywords:
      print(f"{kw['query']}: {kw['clicks']} clics, posición {kw['position']}")

INTEGRACIÓN:
Consumido por SEOOrchestrator (orchestrator.py) para obtener datos de
rendimiento de búsqueda que alimentan los reportes generados por IA.
También usado por SitemapUpdater (sitemap_updater.py) para verificar
sitemaps registrados en GSC.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../inputs/.env'))

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
except ImportError:
    raise ImportError("Instala google-api-python-client: pip install google-api-python-client")

logger = logging.getLogger(__name__)


class GSCClient:
    """
    Cliente para la API de Google Search Console.

    Proporciona acceso a los datos de Search Analytics: consultas de búsqueda,
    páginas, países, dispositivos y métricas asociadas (clics, impresiones,
    CTR, posición media). También incluye métodos auxiliares para leer el
    sitemap local y verificar el estado de indexación.
    """

    def __init__(
        self,
        credentials_path: Optional[str] = None,
        site_url: Optional[str] = None
    ):
        """
        Inicializa el cliente de GSC.

        Args:
            credentials_path: Ruta al JSON de la cuenta de servicio.
                              Si no se provee, usa GSC_CREDENTIALS_PATH del .env.
            site_url: URL del sitio verificada en GSC.
                      Si no se provee, usa GSC_SITE_URL del .env.

        Raises:
            FileNotFoundError: Si no se encuentran las credenciales.
            ValueError: Si no se configura la URL del sitio.
        """
        self.credentials_path = credentials_path or os.getenv("GSC_CREDENTIALS_PATH")
        self.site_url = site_url or os.getenv("GSC_SITE_URL")

        if not self.credentials_path or not os.path.exists(self.credentials_path):
            raise FileNotFoundError(f"Credenciales GSC no encontradas en: {self.credentials_path}")
        if not self.site_url:
            raise ValueError("GSC_SITE_URL no configurado en .env")

        credentials = service_account.Credentials.from_service_account_file(
            self.credentials_path,
            scopes=["https://www.googleapis.com/auth/webmasters.readonly"]
        )
        self.service = build('webmasters', 'v3', credentials=credentials)
        logger.info(f"GSCClient inicializado para sitio: {self.site_url}")

    def get_search_analytics(
        self,
        start_date: str,
        end_date: str,
        dimensions: List[str],
        metrics: List[str] = None,
        row_limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Obtiene datos de Search Analytics de Google Search Console.

        Args:
            start_date: Fecha de inicio en formato YYYY-MM-DD.
            end_date: Fecha de fin en formato YYYY-MM-DD.
            dimensions: Dimensiones a incluir (["query"], ["page"], ["country", "device"]).
            metrics: Métricas a incluir. Por defecto: clicks, impressions, ctr, position.
            row_limit: Número máximo de filas a devolver (máximo 25000).

        Returns:
            Lista de diccionarios, cada uno con las dimensiones y métricas solicitadas.
        """
        if metrics is None:
            metrics = ['clicks', 'impressions', 'ctr', 'position']

        request_body = {
            'startDate': start_date,
            'endDate': end_date,
            'dimensions': dimensions,
            'metrics': [{'expression': m} for m in metrics],
            'rowLimit': row_limit
        }

        response = self.service.searchanalytics().query(
            siteUrl=self.site_url,
            body=request_body
        ).execute()

        results = []
        if 'rows' in response:
            for row in response['rows']:
                item = {}
                for i, dim in enumerate(dimensions):
                    item[dim] = row['keys'][i]
                for met in metrics:
                    item[met] = row.get(met, 0)
                results.append(item)

        return results

    def get_top_keywords(self, days_back: int = 30, limit: int = 50) -> List[Dict]:
        """
        Obtiene las keywords principales ordenadas por clics.

        Args:
            days_back: Días hacia atrás para el análisis.
            limit: Número máximo de keywords a devolver.

        Returns:
            Lista de diccionarios con query, clicks, impressions, ctr, position.
        """
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        return self.get_search_analytics(
            start_date=start_date,
            end_date=end_date,
            dimensions=['query'],
            row_limit=limit
        )

    def get_indexed_pages(self) -> List[str]:
        """
        Obtiene la lista de URLs indexadas leyendo el sitemap.xml local.

        GSC API no tiene un endpoint directo para listar todas las URLs
        indexadas, por lo que se lee el sitemap.xml del proyecto.

        Returns:
            Lista de URLs encontradas en el sitemap, o lista vacía si no existe.
        """
        project_path = os.getenv("PROJECT_PATH")
        sitemap_path = os.path.join(project_path, "public", "sitemap.xml") if project_path else None

        if sitemap_path and os.path.exists(sitemap_path):
            import xml.etree.ElementTree as ET
            tree = ET.parse(sitemap_path)
            root = tree.getroot()
            ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            return [loc.text for loc in root.findall('ns:url/ns:loc', ns)]

        return []

    def submit_url_for_indexing(self, url: str) -> Dict[str, Any]:
        """
        Verifica el estado de una URL en GSC.

        Nota: La API de GSC no permite forzar la indexación, pero permite
        consultar el estado de rastreo y errores asociados a una URL.

        Args:
            url: URL completa a verificar.

        Returns:
            Diccionario con el resultado de la operación.
        """
        try:
            response = self.service.urlcrawlerrors().list(
                siteUrl=self.site_url
            ).execute()
            return {"url": url, "status": "consultado", "details": response}
        except Exception as e:
            return {"url": url, "status": "error", "error": str(e)}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        client = GSCClient()
        print("Obteniendo top keywords de los últimos 7 días...")
        keywords = client.get_top_keywords(days_back=7, limit=10)
        print(json.dumps(keywords, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")
        print("Configura GSC_CREDENTIALS_PATH y GSC_SITE_URL en inputs/.env")
