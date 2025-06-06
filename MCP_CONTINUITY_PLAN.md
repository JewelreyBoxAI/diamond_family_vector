# MCP Server & JewelryBox AI Application Continuity Plan

## 🎯 Overview
This plan ensures seamless operation between the GoHighLevel MCP Server and the JewelryBox AI Application, with robust error handling, deployment coordination, and graceful degradation.

## 🏗️ Architecture Continuity

### Current State
- **JewelryBox AI App**: Production-ready with hardcoded calendar IDs
- **GHL MCP Server**: Standalone service at `ghl_mcp_server/` directory
- **Integration**: HTTP-based MCP protocol communication

### Required Services
1. **Primary**: JewelryBox AI Application (main chat interface)
2. **Secondary**: GHL MCP Server (appointment scheduling backend)
3. **Fallback**: Graceful degradation to expo demo mode

## 🔄 Deployment Strategy

### 1. Coordinated Deployment Process

```bash
# Step 1: Deploy MCP Server First
cd ghl_mcp_server/
docker build -t ghl-mcp-server .
docker run -d -p 8000:8000 ghl-mcp-server

# Step 2: Verify MCP Server Health
curl http://localhost:8000/health

# Step 3: Deploy Main Application with MCP_SERVER_URL
export GHL_MCP_SERVER_URL=http://localhost:8000
cd ../
docker build -t jewelrybox-ai .
docker run -d -p 10000:10000 -e GHL_MCP_SERVER_URL=$GHL_MCP_SERVER_URL jewelrybox-ai
```

### 2. Environment Configuration

#### Production Environment Variables
```bash
# Required for MCP Integration
GHL_MCP_SERVER_URL=https://your-mcp-server.onrender.com

# Optional (Application has fallbacks)
OPENAI_API_KEY=your_openai_key
ALLOWED_ORIGINS=https://yourdomain.com
PORT=10000
```

#### Development Environment Variables
```bash
# Local Development
GHL_MCP_SERVER_URL=http://localhost:8000

# For testing without MCP
# GHL_MCP_SERVER_URL=  # Leave empty to test expo mode
```

## 🛡️ Error Handling & Fallback Strategy

### 1. Application Startup
```python
# Current Implementation in src/app.py
try:
    if GHL_MCP_AVAILABLE and GHLMCPClient and os.getenv("GHL_MCP_SERVER_URL"):
        ghl_mcp_client = GHLMCPClient(os.getenv("GHL_MCP_SERVER_URL"))
        logger.info("✅ GHL MCP Client initialized successfully.")
    else:
        ghl_mcp_client = None
        logger.info("ℹ️ GHL MCP Client unavailable - appointment scheduling disabled.")
except Exception as e:
    logger.error(f"Failed to initialize GHL MCP Client: {e}")
    ghl_mcp_client = None
```

### 2. Runtime Resilience
- **MCP Server Down**: Application continues in expo demo mode
- **Network Timeouts**: 5-second timeout with graceful fallback
- **Invalid Responses**: Error conversion to demo opportunities

### 3. Graceful Degradation Messages
```python
# Examples from current implementation
"Perfect timing! You're seeing exactly what Anthony Haddad means by 'AI Marketing Genius'—imagine when our GHL integration is fully live..."

"Ha! Even AI assistants have their expo moments. This technical glitch actually highlights what makes Diamond Family special..."
```

## 🔍 Health Monitoring

### 1. Application Health Checks

#### Main Application Endpoints
- `GET /` - Main widget interface
- `GET /debug/ghl-status` - MCP integration status
- `GET /debug/events-promotions` - Events configuration
- `POST /chat` - Core chat functionality

#### MCP Server Health Check
```python
# Add to src/app.py
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "mcp_available": ghl_mcp_client is not None,
        "mcp_server": os.getenv("GHL_MCP_SERVER_URL"),
        "timestamp": datetime.utcnow().isoformat()
    }
```

### 2. Monitoring Strategy
```bash
# Health check script
#!/bin/bash
echo "Checking JewelryBox AI Application..."
curl -f http://localhost:10000/health || echo "❌ Main app down"

echo "Checking MCP Server..."
curl -f http://localhost:8000/health || echo "❌ MCP server down"

echo "Testing integration..."
curl -X POST http://localhost:10000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_input": "Schedule appointment", "history": []}' \
  | grep -q "appointment" && echo "✅ Integration working" || echo "⚠️ Integration issue"
```

## 🚀 Production Deployment Plan

### Phase 1: MCP Server Deployment
1. **Deploy MCP Server** to cloud platform (Render, Railway, etc.)
2. **Configure GHL credentials** in MCP server environment
3. **Test MCP endpoints** independently
4. **Document MCP server URL** for main app configuration

### Phase 2: Main Application Update
1. **Set GHL_MCP_SERVER_URL** to production MCP server
2. **Deploy updated application** 
3. **Verify integration** via `/debug/ghl-status`
4. **Test end-to-end** appointment scheduling flow

### Phase 3: Monitoring & Optimization
1. **Set up logging** for both services
2. **Monitor error rates** and response times
3. **Optimize timeout values** based on production performance
4. **Document troubleshooting** procedures

## 🔧 Configuration Management

### 1. Calendar Configuration
```python
# Current hardcoded configuration (no env vars needed)
CALENDAR_MAPPINGS = {
    "demo": "1a2FZj1zqXPbPnrElQD1",
    "custom_jewelry": "1c0RCj9LXQr9iDQaDTn9", 
    "appraisals": "7pRF2Il5lcRZIMBdSkBx",
    "campaign": "CuOcD0x88h7NPvfub9"
}
```

### 2. Environment Variable Migration
```bash
# OLD (removed in recent update)
GHL_DEFAULT_CALENDAR_ID=xxx
GHL_CALENDAR_JEWELLER_ID=xxx
GHL_CALENDAR_AUDIT_ID=xxx
GHL_CALENDAR_BOOKCALL_ID=xxx

# NEW (current implementation)
GHL_MCP_SERVER_URL=https://your-mcp-server.onrender.com
```

## 🧪 Testing Strategy

### 1. Integration Tests
```python
# test_mcp_integration.py
def test_mcp_availability():
    """Test MCP server is reachable"""
    
def test_appointment_scheduling():
    """Test end-to-end appointment flow"""
    
def test_graceful_degradation():
    """Test behavior when MCP is unavailable"""
```

### 2. Manual Testing Checklist
- [ ] Chat works without MCP server
- [ ] Chat works with MCP server running
- [ ] Appointment scheduling creates contacts
- [ ] Calendar selection logic works
- [ ] Error messages are user-friendly
- [ ] Events and promotions display correctly

## 🚨 Troubleshooting Guide

### Common Issues

#### 1. "MCP Server Connection Failed"
```bash
# Check MCP server status
curl http://your-mcp-server-url/health

# Check network connectivity
ping your-mcp-server-domain

# Verify environment variable
echo $GHL_MCP_SERVER_URL
```

#### 2. "Appointment Scheduling Unavailable"
- Verify GHL_MCP_SERVER_URL is set correctly
- Check MCP server logs for GHL API issues
- Test individual MCP tools via debug endpoint

#### 3. "Calendar Selection Not Working"
- Check hardcoded calendar IDs in `ghl_mcp_client.py`
- Verify calendar IDs are active in GHL account
- Test calendar mapping logic

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] MCP server deployed and healthy
- [ ] GHL credentials configured in MCP server
- [ ] Main app environment variables set
- [ ] Both services accessible via health checks

### Post-Deployment
- [ ] Integration test passes
- [ ] Error logs reviewed
- [ ] Performance metrics checked
- [ ] User acceptance testing completed

### Rollback Plan
1. **Immediate**: Set `GHL_MCP_SERVER_URL=""` to disable MCP
2. **Graceful**: Application continues in expo demo mode
3. **Fix**: Address MCP server issues offline
4. **Restore**: Re-enable MCP when stable

## 🔮 Future Enhancements

### 1. Advanced Health Monitoring
- Prometheus metrics
- Grafana dashboards  
- Automated alerting

### 2. Enhanced Error Recovery
- Automatic retry logic
- Circuit breaker patterns
- MCP server failover

### 3. Performance Optimization
- Connection pooling
- Response caching
- Load balancing

## 📞 Support Contacts

**Development Team**: AI_src team
**Platform**: Render.com / Railway (as applicable)
**Monitoring**: Application logs + MCP server logs
**Escalation**: Technical lead for integration issues

---

*This plan ensures robust, production-ready operation between the MCP Server and JewelryBox AI Application with comprehensive error handling and monitoring.* 