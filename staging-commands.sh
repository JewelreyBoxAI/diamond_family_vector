#!/bin/bash
# 🚀 Staging Environment Commands for web-search branch testing

echo "🧪 JewelryBox AI - Staging Environment Manager"
echo "=============================================="

case "$1" in
    start)
        echo "🚀 Starting staging environment..."
        docker-compose -f docker-compose.staging.yml up -d
        echo ""
        echo "✅ Staging server running at: http://localhost:8001"
        echo "📋 Chat widget: http://localhost:8001/widget"
        echo "🔍 Health check: http://localhost:8001/"
        ;;
    
    stop)
        echo "🛑 Stopping staging environment..."
        docker-compose -f docker-compose.staging.yml down
        echo "✅ Staging environment stopped"
        ;;
    
    restart)
        echo "🔄 Restarting staging environment..."
        docker-compose -f docker-compose.staging.yml down
        docker-compose -f docker-compose.staging.yml up -d
        echo "✅ Staging environment restarted"
        ;;
    
    logs)
        echo "📜 Staging logs (Ctrl+C to exit):"
        docker-compose -f docker-compose.staging.yml logs -f
        ;;
    
    status)
        echo "📊 Staging environment status:"
        docker-compose -f docker-compose.staging.yml ps
        ;;
    
    build)
        echo "🔨 Rebuilding staging environment..."
        docker-compose -f docker-compose.staging.yml up -d --build
        echo "✅ Staging environment rebuilt and started"
        ;;
    
    test)
        echo "🧪 Running staging tests..."
        echo "🔍 Testing health endpoint..."
        curl -f http://localhost:8001/ && echo "✅ Health check passed" || echo "❌ Health check failed"
        echo ""
        echo "🔍 Testing widget endpoint..."
        curl -f http://localhost:8001/widget && echo "✅ Widget check passed" || echo "❌ Widget check failed"
        ;;
    
    *)
        echo "Usage: $0 {start|stop|restart|logs|status|build|test}"
        echo ""
        echo "Commands:"
        echo "  start   - Start staging environment on port 8001"
        echo "  stop    - Stop staging environment"
        echo "  restart - Restart staging environment"
        echo "  logs    - View staging logs"
        echo "  status  - Check staging container status"
        echo "  build   - Rebuild and start staging environment"
        echo "  test    - Run basic health checks"
        echo ""
        echo "Examples:"
        echo "  ./staging-commands.sh start   # Start staging"
        echo "  ./staging-commands.sh test    # Test endpoints"
        echo "  ./staging-commands.sh logs    # View logs"
        exit 1
        ;;
esac 