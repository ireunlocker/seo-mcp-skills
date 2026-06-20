#!/bin/bash
# Script de configuración inicial para SEO MCP Skill
# Uso: bash setup.sh

set -e

echo "=== Configurando SEO Skills ==="
echo ""

# 1. Verificar Python
echo "1. Verificando Python..."
python3 --version || { echo "Python3 no encontrado. Instálalo primero."; exit 1; }

# 2. Instalar dependencias
echo "2. Instalando dependencias Python..."
pip3 install -r requirements.txt || { echo "Error instalando dependencias."; exit 1; }

# 3. Configurar .env
if [ ! -f "inputs/.env" ]; then
    echo "3. Configurando variables de entorno..."
    cp inputs/.env.template inputs/.env
    echo "   ✏️  Edita inputs/.env con tus API keys reales"
    echo "   - GEMINI_API_KEY"
    echo "   - GA4_CREDENTIALS_PATH y GA4_PROPERTY_ID"
    echo "   - GSC_CREDENTIALS_PATH y GSC_SITE_URL"
else
    echo "3. inputs/.env ya existe, omitiendo..."
fi

# 4. Inicializar base de datos
echo "4. Inicializando base de datos SQLite..."
python3 -c "from scripts.history_client import SEOHistoryClient; SEOHistoryClient(); print('✓ DB inicializada')"

# 5. Hacer ejecutables los scripts
echo "5. Configurando permisos de scripts..."
chmod +x scripts/*.py
echo "   ✓ Scripts configurados"

# 6. Verificar estructura
echo "6. Verificando estructura..."
echo "   Directorios:"
ls -d */ 2>/dev/null || true
echo "   Scripts:"
ls scripts/*.py 2>/dev/null || true
echo "   Functions:"
ls functions/*.json 2>/dev/null || true

echo ""
echo "=== Configuración completada ==="
echo ""
echo "Próximos pasos:"
echo "1. Edita inputs/.env con tus API keys"
echo "2. Prueba la conexión con Gemini:"
echo "   python3 scripts/orchestrator.py test-openrouter"

  echo "3. Ejecuta un monitoreo de prueba:"
  echo "   python3 scripts/orchestrator.py monitor"
  echo "4. Inicia el monitoreo automático:"
  echo "   python3 scripts/orchestrator.py schedule"