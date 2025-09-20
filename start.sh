#!/bin/bash

# Voice Chat App - Simple Docker Startup
# Clean and reliable approach

set -e

echo "🚀 Voice Chat Application"
echo "========================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your OPENAI_API_KEY"
    echo "   File location: $(pwd)/.env"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Default to production mode
MODE=${1:-prod}

case $MODE in
    "start"|"prod"|"production"|"")
        echo "🐳 Starting Voice Chat Application..."
        echo "   - Frontend: http://localhost:3000"
        echo "   - Backend: http://localhost:8000"
        echo ""
        docker-compose up --build
        ;;
    "stop")
        echo "🛑 Stopping all services..."
        docker-compose down
        echo "✅ All services stopped"
        ;;
    "logs")
        echo "📋 Showing logs..."
        docker-compose logs -f
        ;;
    "restart")
        echo "🔄 Restarting services..."
        docker-compose down
        docker-compose up --build
        ;;
    *)
        echo "Usage: $0 [start|stop|logs|restart]"
        echo ""
        echo "Commands:"
        echo "  start    - Start the application (default)"
        echo "  stop     - Stop all services"
        echo "  logs     - Show container logs"
        echo "  restart  - Restart all services"
        echo ""
        echo "Examples:"
        echo "  ./start.sh           # Start the app"
        echo "  ./start.sh stop      # Stop everything"
        echo "  ./start.sh logs      # View logs"
        echo "  ./start.sh restart   # Restart services"
        echo ""
        echo "For debugging, run the backend locally:"
        echo "  cd backend && source venv/bin/activate && python main.py"
        exit 1
        ;;
esac
