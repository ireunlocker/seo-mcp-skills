#!/usr/bin/env python3
"""
Sistema de auto-aprendizaje basado en SQLite para SEO Skills.

Este módulo implementa un historial persistente de ejecuciones de skills SEO,
keywords rastreadas y métricas de rendimiento. Los datos almacenados se utilizan
para generar contexto de adaptación que permite a la IA ajustar sus estrategias
futuras basándose en resultados pasados, evitando repetir errores y potenciando
lo que funcionó.

PRERREQUISITOS:
- Python 3.12+
- No requiere dependencias externas (usa sqlite3 de la stdlib).

CONFIGURACIÓN:
- La base de datos se crea automáticamente en outputs/seo_history.db.
- No requiere configuración manual.

ESQUEMA SQLITE:
- executions: Almacena cada ejecución de skill con timestamp, inputs, outputs,
  métricas, puntuación de rendimiento y notas.
- keywords: Almacena las keywords asociadas a cada ejecución, incluyendo
  posición, clics, impresiones y CTR, vinculadas por execution_id.

USO:
  from history_client import SEOHistoryClient

  client = SEOHistoryClient()
  exec_id = client.log_execution("seo_dashboard", {"periodo": "7d"})
  client.log_keywords(exec_id, [{"query": "hipoteca", "clicks": 10}], "2026-01-01")
  context = client.get_adaptation_context({"skill_name": "seo_dashboard"})

INTEGRACIÓN:
Consumido por SEOOrchestrator (orchestrator.py) para registrar cada ejecución
de skill y obtener contexto de adaptación que se inyecta en los prompts de la IA.
La tabla keywords es alimentada por los datos de GSC durante el monitoreo automático.
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), '../outputs/seo_history.db')


class SEOHistoryClient:
    """
    Cliente de auto-aprendizaje para SEO Skills.

    Almacena y consulta el historial de ejecuciones y keywords en una base
    de datos SQLite local. Proporciona contexto histórico a la IA para mejorar
    la calidad de las estrategias generadas con el tiempo.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Inicializa el cliente y crea la base de datos si no existe.

        Args:
            db_path: Ruta al archivo SQLite. Si no se provee, usa
                     outputs/seo_history.db dentro del directorio del proyecto.
        """
        self.db_path = db_path or DB_PATH
        self._init_db()

    def _init_db(self):
        """
        Crea las tablas executions y keywords si no existen.

        La tabla executions almacena el registro de cada skill ejecutada,
        mientras que keywords guarda las palabras clave asociadas a cada
        ejecución con sus métricas de rendimiento.
        """
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    skill_name TEXT NOT NULL,
                    inputs TEXT NOT NULL,
                    outputs TEXT,
                    metrics TEXT,
                    performance_score REAL,
                    notes TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS keywords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id INTEGER NOT NULL,
                    keyword TEXT NOT NULL,
                    position REAL,
                    clicks INTEGER,
                    impressions INTEGER,
                    ctr REAL,
                    date TEXT NOT NULL,
                    FOREIGN KEY (execution_id) REFERENCES executions(id)
                )
            ''')
            conn.commit()

    def log_execution(
        self,
        skill_name: str,
        inputs: Dict[str, Any],
        outputs: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        performance_score: Optional[float] = None,
        notes: Optional[str] = None
    ) -> int:
        """
        Registra una ejecución de skill en el histórico.

        Args:
            skill_name: Nombre de la skill ejecutada.
            inputs: Diccionario con los parámetros de entrada.
            outputs: Diccionario con los resultados de la ejecución.
            metrics: Métricas asociadas (sesiones, keywords, etc.).
            performance_score: Puntuación de rendimiento (0.0 a 1.0).
            notes: Notas adicionales sobre la ejecución.

        Returns:
            ID autoincremental de la ejecución registrada.
        """
        timestamp = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                INSERT INTO executions
                (timestamp, skill_name, inputs, outputs, metrics, performance_score, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                timestamp,
                skill_name,
                json.dumps(inputs, ensure_ascii=False),
                json.dumps(outputs, ensure_ascii=False) if outputs else None,
                json.dumps(metrics, ensure_ascii=False) if metrics else None,
                performance_score,
                notes
            ))
            conn.commit()
            return cursor.lastrowid

    def log_keywords(self, execution_id: int, keywords: List[Dict[str, Any]], date: str):
        """
        Registra las keywords asociadas a una ejecución.

        Cada keyword puede incluir posición, clics, impresiones y CTR.
        Todas se vinculan al execution_id proporcionado.

        Args:
            execution_id: ID de la ejecución a la que pertenecen.
            keywords: Lista de diccionarios con datos de keywords.
            date: Fecha del registro en formato YYYY-MM-DD.
        """
        with sqlite3.connect(self.db_path) as conn:
            for kw in keywords:
                conn.execute('''
                    INSERT INTO keywords
                    (execution_id, keyword, position, clicks, impressions, ctr, date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    execution_id,
                    kw.get('query', kw.get('keyword', '')),
                    kw.get('position', None),
                    kw.get('clicks', None),
                    kw.get('impressions', None),
                    kw.get('ctr', None),
                    date
                ))
            conn.commit()

    def get_past_strategies(self, skill_name: str, limit: int = 10) -> List[Dict]:
        """
        Obtiene las ejecuciones pasadas de una skill específica.

        Args:
            skill_name: Nombre de la skill a consultar.
            limit: Número máximo de ejecuciones a devolver.

        Returns:
            Lista de diccionarios con los registros de ejecuciones,
            ordenados por timestamp descendente.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM executions
                WHERE skill_name = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (skill_name, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_best_performing_keywords(self, min_position: float = 10.0, limit: int = 50) -> List[Dict]:
        """
        Obtiene las keywords con mejor posición promedio.

        Útil para identificar qué términos están funcionando bien y
        poder replicar las estrategias que llevaron a esas posiciones.

        Args:
            min_position: Posición máxima para considerar (menor número = mejor).
            limit: Número máximo de keywords a devolver.

        Returns:
            Lista de diccionarios con keyword, avg_position y total_clicks.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT keyword, AVG(position) as avg_position, SUM(clicks) as total_clicks
                FROM keywords
                WHERE position <= ?
                GROUP BY keyword
                ORDER BY avg_position ASC
                LIMIT ?
            ''', (min_position, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_adaptation_context(self, current_inputs: Dict[str, Any]) -> str:
        """
        Genera un contexto de adaptación basado en ejecuciones pasadas.

        Este texto se inyecta en el prompt de la IA para que pueda ajustar
        sus estrategias según lo aprendido previamente. Si no hay histórico,
        devuelve un mensaje indicando que es la primera ejecución.

        Args:
            current_inputs: Diccionario que debe contener la clave "skill_name"
                           para identificar qué skill consultar.

        Returns:
            String con el contexto formateado para el prompt de la IA.
        """
        skill_name = current_inputs.get('skill_name', '')
        past = self.get_past_strategies(skill_name, limit=5)

        if not past:
            return "No hay histórico previo para esta skill. Es la primera ejecución."

        context = "=== HISTÓRICO DE EJECUCIONES PASADAS ===\n"
        for p in past:
            context += f"\nFecha: {p['timestamp']}\n"
            context += f"Inputs: {p['inputs']}\n"
            if p['outputs']:
                context += f"Outputs: {p['outputs'][:500]}...\n"
            if p['performance_score']:
                context += f"Performance Score: {p['performance_score']}\n"
            context += "---\n"

        context += "\n=== ADAPTACIÓN REQUERIDA ===\n"
        context += "Basado en el histórico, ajusta la estrategia actual para mejorar resultados previos.\n"
        context += "Evita repetir errores pasados y potencia lo que funcionó.\n"

        return context


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    client = SEOHistoryClient()
    print(f"Base de datos inicializada en: {client.db_path}")

    # Insertar dato de prueba
    test_id = client.log_execution(
        skill_name="seo_agressive_strategy",
        inputs={"nicho": "intermediación hipotecaria", "mercado": "Madrid"},
        outputs={"keywords": ["hipoteca Madrid", "préstamo vivienda Madrid"]},
        performance_score=0.85
    )
    print(f"Ejecución de prueba registrada con ID: {test_id}")

    past = client.get_past_strategies("seo_agressive_strategy")
    print(f"Ejecuciones pasadas: {len(past)}")
