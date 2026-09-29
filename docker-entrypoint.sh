#!/bin/bash
# Docker entrypoint for SEO MCP Skills
# Handles different run modes and configurations

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print banner
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          SEO MCP Skills - Docker Container                   ║"
echo "║          Model Context Protocol SEO Automation               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if .env exists
if [ ! -f /app/.env ] && [ ! -f /app/inputs/.env ]; then
    echo -e "${YELLOW}⚠️  No .env file found!${NC}"
    echo -e "   Copy .env.example to inputs/.env and configure your API keys"
    echo -e "   Or mount your config at /app/inputs/.env"
fi

# Function to run orchestrator commands
run_orchestrator() {
    local cmd="$1"
    shift
    echo -e "${GREEN}🚀 Running: python scripts/orchestrator.py $cmd $*${NC}"
    python scripts/orchestrator.py "$cmd" "$@"
}

# Function to run universal agent
run_universal_agent() {
    echo -e "${GREEN}🤖 Starting Universal SEO Agent with MCP...${NC}"
    export RUN_UNIVERSAL_AGENT=1
    python scripts/universal_seo_agent.py "$@"
}

# Function to run tests
run_tests() {
    echo -e "${GREEN}🧪 Running tests...${NC}"
    pytest tests/ -v
}

# Function to initialize database
init_db() {
    echo -e "${GREEN}🗄️  Initializing SQLite database...${NC}"
    python -c "from scripts.history_client import SEOHistoryClient; SEOHistoryClient(); print('✓ DB initialized')"
}

# Function to test AI connections
test_ai() {
    local provider="${1:-openrouter}"
    echo -e "${GREEN}🔍 Testing $provider connection...${NC}"
    run_orchestrator "test-$provider"
}

# Main command handling
case "${1:-schedule}" in
    schedule)
        echo -e "${GREEN}⏰ Starting scheduler (cron mode)...${NC}"
        run_orchestrator schedule
        ;;
    monitor)
        echo -e "${GREEN}📊 Running single monitoring cycle...${NC}"
        run_orchestrator monitor
        ;;
    test-openrouter)
        test_ai openrouter
        ;;
    test-gemini)
        test_ai gemini
        ;;
    universal)
        run_universal_agent "${@:2}"
        ;;
    init-db)
        init_db
        ;;
    test)
        run_tests
        ;;
    shell)
        echo -e "${GREEN}🐚 Starting interactive shell...${NC}"
        exec /bin/bash
        ;;
    python)
        shift
        exec python "$@"
        ;;
    *)
        # Pass through to orchestrator if it's a known command
        if python scripts/orchestrator.py --help 2>&1 | grep -q "usage:"; then
            echo -e "${GREEN}🔧 Running orchestrator command: $*${NC}"
            run_orchestrator "$@"
        else
            echo -e "${RED}❌ Unknown command: $1${NC}"
            echo ""
            echo "Available commands:"
            echo "  schedule       - Run scheduler (default)"
            echo "  monitor        - Run single monitoring cycle"
            echo "  test-openrouter - Test OpenRouter connection"
            echo "  test-gemini    - Test Gemini connection"
            echo "  universal      - Run Universal SEO Agent"
            echo "  init-db        - Initialize SQLite database"
            echo "  test           - Run pytest tests"
            echo "  shell          - Start interactive shell"
            echo "  python <cmd>   - Run Python command"
            exit 1
        fi
        ;;
esac