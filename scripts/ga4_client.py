#!/usr/bin/env python3
"""
Cliente para la API de Google Analytics 4 (GA4).

Este módulo permite obtener métricas y dimensiones de una propiedad de Google
Analytics 4 utilizando una cuenta de servicio. Proporciona métodos para
consultar reportes personalizados y métricas SEO clave como sesiones orgánicas,
páginas más visitadas y tasa de engagement.

PRERREQUISITOS:
- Python 3.12+
- Dependencias: google-analytics-data, google-auth-oauthlib, python-dotenv
- Una cuenta de servicio de Google Cloud con acceso a la propiedad GA4
- Archivo JSON de credenciales de la cuenta de servicio

CONFIGURACIÓN:
1. Crea una cuenta de servicio en Google Cloud Console y descarga su JSON.
2. Concede acceso a la cuenta de servicio en GA4 (Administrar > Accessos a la cuenta).
3. Configura en inputs/.env:
     GA4_CREDENTIALS_PATH=/ruta/al/archivo.json
     GA4_PROPERTY_ID=123456789

USO:
  from ga4_client import GA4Client

  client = GA4Client()
  metrics = client.get_seo_metrics(days_back=7)
  print(metrics["organic_sessions"])

  # Reporte personalizado
  report = client.get_report(
      start_date="7daysAgo",
      end_date="today",
      dimensions=["pagePath", "sessionSource"],
      metrics=["sessions", "screenPageViews"]
  )

INTEGRACIÓN:
Consumido por SEOOrchestrator (orchestrator.py) en el ciclo de monitoreo
automático. Las métricas obtenidas se pasan a la IA para generar reportes
y se envían a la plataforma web via TelegramNotifier.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../inputs/.env'))

try:
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import (
        RunReportRequest,
        DateRange,
        Dimension,
        Metric,
        OrderBy
    )
    from google.oauth2 import service_account
except ImportError:
    raise ImportError("Instala google-analytics-data: pip install google-analytics-data")

logger = logging.getLogger(__name__)


class GA4Client:
    """
    Cliente para la API de Google Analytics 4.

    Proporciona métodos para ejecutar reportes sobre una propiedad GA4
    usando credenciales de cuenta de servicio. Soporta dimensiones,
    métricas, filtros y ordenación personalizados.
    """

    def __init__(
        self,
        credentials_path: Optional[str] = None,
        property_id: Optional[str] = None
    ):
        """
        Inicializa el cliente de GA4.

        Args:
            credentials_path: Ruta al archivo JSON de la cuenta de servicio.
                              Si no se provee, usa GA4_CREDENTIALS_PATH del .env.
            property_id: ID numérico de la propiedad GA4.
                         Si no se provee, usa GA4_PROPERTY_ID del .env.

        Raises:
            FileNotFoundError: Si no se encuentran las credenciales.
            ValueError: Si no se configura el property_id.
        """
        self.credentials_path = credentials_path or os.getenv("GA4_CREDENTIALS_PATH")
        self.property_id = property_id or os.getenv("GA4_PROPERTY_ID")

        if not self.credentials_path or not os.path.exists(self.credentials_path):
            raise FileNotFoundError(f"Credenciales GA4 no encontradas en: {self.credentials_path}")
        if not self.property_id:
            raise ValueError("GA4_PROPERTY_ID no configurado en .env")

        credentials = service_account.Credentials.from_service_account_file(
            self.credentials_path,
            scopes=["https://www.googleapis.com/auth/analytics.readonly"]
        )
        self.client = BetaAnalyticsDataClient(credentials=credentials)
        self.property = f"properties/{self.property_id}"

        logger.info(f"GA4Client inicializado para propiedad: {self.property_id}")

    def get_report(
        self,
        start_date: str,
        end_date: str,
        dimensions: List[str],
        metrics: List[str],
        limit: int = 100,
        order_by: Optional[List[Dict]] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene un reporte personalizado de GA4.

        Args:
            start_date: Fecha de inicio (YYYY-MM-DD o "NdaysAgo").
            end_date: Fecha de fin (YYYY-MM-DD o "today").
            dimensions: Lista de nombres de dimensión (ej: ["pagePath", "sessionSource"]).
            metrics: Lista de nombres de métrica (ej: ["sessions", "screenPageViews"]).
            limit: Número máximo de filas a devolver.
            order_by: Opciones de ordenación. Lista de dicts con formato:
                     [{"field": {"metric": {"metricName": "..."}}, "desc": True}]

        Returns:
            Lista de diccionarios con los resultados, donde cada dict tiene
            como claves los nombres de dimensiones y métricas solicitadas.
        """
        request = RunReportRequest(
            property=self.property,
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimensions=[Dimension(name=d) for d in dimensions],
            metrics=[Metric(name=m) for m in metrics],
            limit=limit
        )

        if order_by:
            request.order_bys = [
                OrderBy(
                    metric=OrderBy.MetricOrderBy(metric_name=ob['field']['metric']['metricName']),
                    desc=ob.get('desc', False)
                ) for ob in order_by
            ]

        response = self.client.run_report(request)

        results = []
        for row in response.rows:
            item = {}
            for i, dim in enumerate(dimensions):
                item[dim] = row.dimension_values[i].value
            for i, met in enumerate(metrics):
                item[met] = row.metric_values[i].value
            results.append(item)

        return results

    def get_seo_metrics(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Obtiene métricas SEO clave para el período especificado.

        Incluye las páginas más visitadas y el total de sesiones orgánicas
        desglosadas por fuente de tráfico.

        Args:
            days_back: Días hacia atrás desde hoy para el reporte.

        Returns:
            Diccionario con:
                - "period": Período consultado.
                - "top_pages": Lista de páginas más vistas.
                - "organic_sessions": Total de sesiones orgánicas.
                - "organic_details": Desglose por fuente orgánica.
        """
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        top_pages = self.get_report(
            start_date=start_date,
            end_date=end_date,
            dimensions=['pagePath', 'pageTitle'],
            metrics=['screenPageViews', 'sessions', 'engagementRate'],
            limit=20,
            order_by=[{'field': {'metric': {'metricName': 'screenPageViews'}}, 'desc': True}]
        )

        organic_sessions = self.get_report(
            start_date=start_date,
            end_date=end_date,
            dimensions=['sessionSource'],
            metrics=['sessions'],
            limit=50
        )

        # Filtrar solo tráfico orgánico (Google y fuentes orgánicas)
        organic = [
            s for s in organic_sessions
            if 'google' in s.get('sessionSource', '').lower()
            or s.get('sessionSource', '') == 'organic'
        ]
        total_organic = sum(int(s['sessions']) for s in organic) if organic else 0

        return {
            'period': f"{start_date} a {end_date}",
            'top_pages': top_pages,
            'organic_sessions': total_organic,
            'organic_details': organic
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        client = GA4Client()
        print("Obteniendo métricas SEO de los últimos 7 días...")
        metrics = client.get_seo_metrics(days_back=7)
        print(json.dumps(metrics, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")
        print("Configura GA4_CREDENTIALS_PATH y GA4_PROPERTY_ID en inputs/.env")
