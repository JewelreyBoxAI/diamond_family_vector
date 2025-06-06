#!/bin/bash

# MCP Server & JewelryBox AI Application Health Monitoring
# Run this script to continuously monitor both services

# Configuration
MCP_PORT=${MCP_PORT:-8000}
APP_PORT=${APP_PORT:-10000}
CHECK_INTERVAL=${CHECK_INTERVAL:-30}  # seconds

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Service URLs
MCP_HEALTH_URL="http://localhost:$MCP_PORT/health"
APP_HEALTH_URL="http://localhost:$APP_PORT/health"
APP_MCP_STATUS_URL="http://localhost:$APP_PORT/debug/ghl-status"

log_with_time() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

check_service() {
    local url=$1
    local service_name=$2
    
    if curl -f "$url" >/dev/null 2>&1; then
        log_with_time "${GREEN}✅ $service_name: Healthy${NC}"
        return 0
    else
        log_with_time "${RED}❌ $service_name: Unhealthy${NC}"
        return 1
    fi
}

check_integration() {
    if curl -s "$APP_MCP_STATUS_URL" | grep -q '"ghl_mcp_client_available":true' 2>/dev/null; then
        log_with_time "${GREEN}🔗 MCP Integration: Working${NC}"
        return 0
    else
        log_with_time "${YELLOW}⚠️  MCP Integration: Not Available${NC}"
        return 1
    fi
}

show_detailed_status() {
    echo
    log_with_time "${BLUE}=== Detailed Status Check ===${NC}"
    
    # Check main app health
    if app_health=$(curl -s "$APP_HEALTH_URL" 2>/dev/null); then
        echo "$app_health" | python3 -m json.tool 2>/dev/null || echo "Raw response: $app_health"
    else
        log_with_time "${RED}❌ Unable to get app health details${NC}"
    fi
    
    echo
    
    # Check MCP status
    if mcp_status=$(curl -s "$APP_MCP_STATUS_URL" 2>/dev/null); then
        echo "$mcp_status" | python3 -m json.tool 2>/dev/null || echo "Raw response: $mcp_status"
    else
        log_with_time "${RED}❌ Unable to get MCP status details${NC}"
    fi
    
    echo
}

monitor_continuous() {
    log_with_time "${BLUE}🔍 Starting continuous monitoring (every ${CHECK_INTERVAL}s)${NC}"
    log_with_time "${BLUE}Press Ctrl+C to stop${NC}"
    echo
    
    while true; do
        # Check services
        mcp_healthy=$(check_service "$MCP_HEALTH_URL" "MCP Server"; echo $?)
        app_healthy=$(check_service "$APP_HEALTH_URL" "JewelryBox AI"; echo $?)
        integration_working=$(check_integration; echo $?)
        
        # Overall status
        if [ "$mcp_healthy" -eq 0 ] && [ "$app_healthy" -eq 0 ] && [ "$integration_working" -eq 0 ]; then
            log_with_time "${GREEN}🚀 All Systems: Operational${NC}"
        elif [ "$app_healthy" -eq 0 ]; then
            log_with_time "${YELLOW}⚠️  System Status: Degraded (App running, MCP issues)${NC}"
        else
            log_with_time "${RED}🚨 System Status: Critical (App down)${NC}"
        fi
        
        echo "$(log_with_time "Sleeping for ${CHECK_INTERVAL}s...")"
        echo "----------------------------------------"
        sleep "$CHECK_INTERVAL"
    done
}

run_once() {
    log_with_time "${BLUE}🔍 Running health check...${NC}"
    
    check_service "$MCP_HEALTH_URL" "MCP Server"
    check_service "$APP_HEALTH_URL" "JewelryBox AI"
    check_integration
    
    show_detailed_status
}

test_chat() {
    log_with_time "${BLUE}🧪 Testing chat functionality...${NC}"
    
    response=$(curl -s -X POST "http://localhost:$APP_PORT/chat" \
        -H "Content-Type: application/json" \
        -d '{"user_input": "Test message - are you working?", "history": []}' 2>/dev/null)
    
    if [ $? -eq 0 ] && echo "$response" | grep -q "reply"; then
        log_with_time "${GREEN}✅ Chat: Working${NC}"
        echo "Sample response: $(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['reply'][:100])" 2>/dev/null || echo "Unable to parse")"
    else
        log_with_time "${RED}❌ Chat: Not working${NC}"
    fi
}

show_logs() {
    echo
    log_with_time "${BLUE}📋 Recent Application Logs:${NC}"
    echo "=============================="
    docker logs --tail 20 jewelrybox-ai 2>/dev/null || echo "No JewelryBox AI logs available"
    
    echo
    log_with_time "${BLUE}📋 Recent MCP Server Logs:${NC}"
    echo "============================"
    docker logs --tail 20 ghl-mcp-server 2>/dev/null || echo "No MCP Server logs available"
}

case "${1:-once}" in
    continuous|monitor)
        monitor_continuous
        ;;
    once|check)
        run_once
        ;;
    test)
        run_once
        test_chat
        ;;
    logs)
        show_logs
        ;;
    status)
        run_once
        show_logs
        ;;
    *)
        echo "Usage: $0 {continuous|once|test|logs|status}"
        echo "  continuous: Monitor continuously (default for 'monitor')"
        echo "  once:      Run single health check (default)"
        echo "  test:      Run health check + test chat functionality"
        echo "  logs:      Show recent logs from both services"
        echo "  status:    Show health + logs"
        echo
        echo "Environment variables:"
        echo "  MCP_PORT=$MCP_PORT"
        echo "  APP_PORT=$APP_PORT"
        echo "  CHECK_INTERVAL=${CHECK_INTERVAL}s"
        exit 1
        ;;
esac 