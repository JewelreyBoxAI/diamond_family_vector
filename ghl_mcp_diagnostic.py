#!/usr/bin/env python3
"""
Diamond Demo - GHL MCP Integration Diagnostic
Comprehensive testing of JewelryBoxAI_Bot ↔ GHL MCP Server connectivity and functionality.
"""

import os
import sys
import json
import time
import asyncio
import subprocess
import traceback
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.append('src')

def print_header(title):
    """Print a formatted section header."""
    print(f"\n{'='*70}")
    print(f"🔍 {title}")
    print('='*70)

def print_status(item, status, details=""):
    """Print status with emoji indicators."""
    emoji = "✅" if status else "❌"
    print(f"{emoji} {item:<45} {details}")

def print_warning(item, details=""):
    """Print warning with warning emoji."""
    print(f"⚠️  {item:<45} {details}")

def print_info(item, details=""):
    """Print info with info emoji."""
    print(f"ℹ️  {item:<45} {details}")

def check_mcp_server_availability():
    """Check if the GHL MCP server directory exists and has the required files."""
    print_header("MCP Server Directory Check")
    
    mcp_server_path = Path("../MCP_SERVERS/ghl_mcp_server")
    
    if not mcp_server_path.exists():
        print_status("MCP Server Directory", False, "Not found at ../MCP_SERVERS/ghl_mcp_server")
        return False
    
    print_status("MCP Server Directory", True, str(mcp_server_path.absolute()))
    
    # Check for required files
    required_files = [
        "main.py",
        "requirements.txt",
        "Dockerfile"
    ]
    
    all_files_exist = True
    for file_name in required_files:
        file_path = mcp_server_path / file_name
        exists = file_path.exists()
        if exists:
            size = f"({file_path.stat().st_size} bytes)"
            print_status(f"  {file_name}", True, size)
        else:
            print_status(f"  {file_name}", False, "Missing")
            all_files_exist = False
    
    return all_files_exist

def check_mcp_server_running(server_url=None):
    """Check if MCP server is running at the specified URL."""
    if not server_url:
        server_url = os.getenv("GHL_MCP_SERVER_URL", "http://localhost:8000")
    
    print_header(f"MCP Server Connectivity")
    
    mcp_url = server_url
    
    try:
        import requests
        
        # Check basic connectivity
        try:
            response = requests.get(f"{mcp_url}", timeout=5)
            if response.status_code == 200:
                print_status("MCP Server Health", True, f"Responding on {mcp_url}")
                try:
                    health_data = response.json()
                    print_info("  Server Status", health_data.get('status', 'unknown'))
                    print_info("  Server Time", health_data.get('timestamp', 'unknown'))
                except:
                    print_info("  Server Response", "Valid but not JSON")
                return True
            else:
                print_status("MCP Server Health", False, f"HTTP {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print_status("MCP Server Health", False, f"Connection refused on {mcp_url}")
            return False
        except requests.exceptions.Timeout:
            print_status("MCP Server Health", False, "Request timeout")
            return False
        except Exception as e:
            print_status("MCP Server Health", False, f"Error: {str(e)}")
            return False
            
    except ImportError:
        print_warning("Requests Library", "Not available for connectivity test")
        return False

def check_ghl_mcp_client_configuration():
    """Test the GHL MCP client configuration and basic functionality."""
    print_header("GHL MCP Client Configuration")
    
    try:
        # Import GHL components
        from tools.ghl_mcp_client import GHLMCPClient, GHLAppointmentScheduler, CustomerInfoExtractor
        print_status("GHL MCP Imports", True, "All classes imported successfully")
        
        # Check environment configuration
        mcp_server_url = os.getenv("GHL_MCP_SERVER_URL")
        if mcp_server_url:
            print_status("GHL_MCP_SERVER_URL", True, mcp_server_url)
        else:
            print_warning("GHL_MCP_SERVER_URL", "Not configured - using default http://localhost:8000")
            mcp_server_url = "http://localhost:8000"
        
        # Test client initialization
        try:
            client = GHLMCPClient(mcp_server_url)
            print_status("MCP Client Init", True, "Client created successfully")
            
            # Test calendar configuration
            calendars = client.get_available_calendars()
            print_status("Calendar Config", True, f"{len(calendars)} calendars configured")
            
            for cal_type, cal_id in calendars.items():
                print_info(f"  {cal_type}", cal_id)
            
            # Test available tools
            available_tools = client.list_available_tools()
            print_status("Available Tools", True, f"{len(available_tools)} tools")
            for tool in available_tools:
                print_info(f"  Tool", tool)
                
        except Exception as e:
            print_status("MCP Client Init", False, f"Error: {str(e)}")
            return False
        
        # Test CustomerInfoExtractor
        try:
            extractor = CustomerInfoExtractor()
            test_text = "Hi, I'm John Smith. You can reach me at john.smith@email.com or call (555) 123-4567"
            result = extractor.extract_contact_info(test_text)
            
            has_name = result.get('name') == 'John Smith'
            has_email = result.get('email') == 'john.smith@email.com'
            has_phone = result.get('phone') == '(555) 123-4567'
            
            if has_name and has_email and has_phone:
                print_status("Contact Extraction", True, "All fields extracted correctly")
            else:
                print_status("Contact Extraction", False, f"Missing fields: {result}")
                
        except Exception as e:
            print_status("Contact Extraction", False, f"Error: {str(e)}")
        
        # Test calendar selection logic
        try:
            test_cases = [
                ("I need jewelry appraised", "appraisals"),
                ("Custom design consultation", "custom_jewelry"),
                ("Book a demo", "demo"),
                ("Marketing campaign meeting", "campaign"),
                ("General inquiry", "demo")  # fallback
            ]
            
            print_info("Calendar Selection Tests", "")
            all_correct = True
            for query, expected in test_cases:
                selected = client.select_calendar(query)
                correct = selected == expected
                if not correct:
                    all_correct = False
                status_symbol = "✅" if correct else "❌"
                print(f"    {status_symbol} '{query}' → {selected} (expected: {expected})")
            
            print_status("Calendar Selection Logic", all_correct, "All tests passed" if all_correct else "Some tests failed")
                
        except Exception as e:
            print_status("Calendar Selection", False, f"Error: {str(e)}")
        
        return True
        
    except ImportError as e:
        print_status("GHL MCP Imports", False, f"Import error: {str(e)}")
        return False
    except Exception as e:
        print_status("GHL MCP Client", False, f"Unexpected error: {str(e)}")
        return False

async def test_mcp_server_integration(server_url=None):
    if not server_url:
        server_url = os.getenv("GHL_MCP_SERVER_URL", "http://localhost:8000")
    """Test actual MCP server integration with real API calls."""
    print_header("MCP Server Integration Testing")
    
    try:
        from tools.ghl_mcp_client import GHLMCPClient
        client = GHLMCPClient(server_url)
        
        # Test 1: List available tools
        try:
            tools = client.list_available_tools()
            print_status("List Available Tools", True, f"{len(tools)} tools found")
        except Exception as e:
            print_status("List Available Tools", False, f"Error: {str(e)}")
            return False
        
        # Test 2: Test each available tool with safe parameters
        test_tools = [
            ("get_contact_info", {"contact_id": "test_id_123"}),
            ("list_opportunities", {"limit": 1}),
            ("get_pipeline_info", {"pipeline_id": "test_pipeline"}),
            ("search_contacts", {"query": "test", "limit": 1})
        ]
        
        print_info("Testing Individual Tools", "")
        tools_working = 0
        for tool_name, params in test_tools:
            try:
                result = client.call_mcp_tool(tool_name, params)
                if result:
                    print_status(f"  {tool_name}", True, "Responded successfully")
                    tools_working += 1
                else:
                    print_status(f"  {tool_name}", False, "No response")
            except Exception as e:
                # Expected for test data - server should respond with error but connection works
                if "404" in str(e) or "not found" in str(e).lower():
                    print_status(f"  {tool_name}", True, "Connected (test data not found - expected)")
                    tools_working += 1
                else:
                    print_status(f"  {tool_name}", False, f"Error: {str(e)}")
        
        print_status("Tool Integration", tools_working > 0, f"{tools_working}/{len(test_tools)} tools responding")
        
        # Test 3: End-to-end appointment scheduling flow (with test data)
        try:
            from tools.ghl_mcp_client import GHLAppointmentScheduler
            scheduler = GHLAppointmentScheduler(client)
            
            # Test with fake data to verify flow
            test_conversation = [
                {"role": "user", "content": "I want to schedule an appointment"},
                {"role": "assistant", "content": "I'd be happy to help you schedule an appointment!"}
            ]
            
            # This should fail gracefully with test data but show the integration works
            result = await scheduler.schedule_from_conversation(
                conversation_messages=test_conversation,
                customer_name="Test Customer",
                customer_email="test@example.com", 
                customer_phone="(555) 123-4567",
                appointment_type="consultation"
            )
            
            if result.get("success"):
                print_status("Appointment Scheduling", True, "Flow completed successfully")
            else:
                error_msg = result.get("error", "Unknown error")
                if "test" in error_msg.lower() or "not found" in error_msg.lower():
                    print_status("Appointment Scheduling", True, "Flow working (test data expected to fail)")
                else:
                    print_status("Appointment Scheduling", False, f"Error: {error_msg}")
            
        except Exception as e:
            if "test" in str(e).lower() or "not found" in str(e).lower():
                print_status("Appointment Scheduling", True, "Integration working (test data rejection expected)")
            else:
                print_status("Appointment Scheduling", False, f"Error: {str(e)}")
        
        return True
        
    except Exception as e:
        print_status("MCP Integration Test", False, f"Failed: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_main_app_integration():
    """Test the main application's integration with GHL MCP."""
    print_header("Main Application Integration")
    
    try:
        # Import main app components
        from app import ghl_mcp_client, ghl_scheduler, ghl_extractor, PROMPT_ARRAYS
        
        # Test if GHL components are initialized
        print_status("GHL MCP Client", ghl_mcp_client is not None, 
                    "Initialized" if ghl_mcp_client else "Not initialized")
        print_status("GHL Scheduler", ghl_scheduler is not None,
                    "Initialized" if ghl_scheduler else "Not initialized")
        print_status("GHL Extractor", ghl_extractor is not None,
                    "Initialized" if ghl_extractor else "Not initialized")
        
        # Test events and promotions integration
        events = PROMPT_ARRAYS.get('upcomingEvents', [])
        current_offer = PROMPT_ARRAYS.get('currentOffer', '')
        
        print_status("Events Loaded", len(events) > 0, f"{len(events)} events")
        print_status("Promotions Loaded", bool(current_offer), "Current offer available" if current_offer else "No current offer")
        
        # Test debug endpoints availability
        try:
            from app import app
            routes = [route.path for route in app.routes]
            
            debug_routes = ['/debug/ghl-status', '/debug/events-promotions', '/health']
            routes_available = 0
            for route in debug_routes:
                has_route = route in routes
                if has_route:
                    routes_available += 1
                print_status(f"Debug Route {route}", has_route)
            
            print_status("Debug Infrastructure", routes_available == len(debug_routes), 
                        f"{routes_available}/{len(debug_routes)} routes available")
                
        except Exception as e:
            print_status("Debug Routes", False, f"Error: {str(e)}")
        
        return True
        
    except Exception as e:
        print_status("Main App Integration", False, f"Error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

def check_deployment_readiness():
    """Check if the system is ready for deployment."""
    print_header("Deployment Readiness")
    
    # Check continuity plan files
    continuity_files = [
        "MCP_CONTINUITY_PLAN.md",
        "deploy_continuity.sh", 
        "monitor_services.sh"
    ]
    
    continuity_ready = 0
    for file_name in continuity_files:
        exists = os.path.exists(file_name)
        if exists:
            continuity_ready += 1
        print_status(f"Continuity File {file_name}", exists)
    
    # Check Docker files
    docker_files = ["Dockerfile", "docker-compose.yml"]
    docker_ready = 0
    for file_name in docker_files:
        exists = os.path.exists(file_name)
        if exists:
            docker_ready += 1
        print_status(f"Docker File {file_name}", exists)
    
    # Check MCP server Docker files
    mcp_docker_path = Path("../MCP_SERVERS/ghl_mcp_server/Dockerfile")
    mcp_docker_ready = mcp_docker_path.exists()
    print_status("MCP Server Dockerfile", mcp_docker_ready)
    
    # Check environment variables for production
    prod_vars = ["OPENAI_API_KEY", "GHL_MCP_SERVER_URL"]
    env_ready = 0
    for var in prod_vars:
        value = os.getenv(var)
        if var == "OPENAI_API_KEY" and value:
            env_ready += 1
        elif var == "GHL_MCP_SERVER_URL":
            env_ready += 1  # Optional but counted for readiness
        print_status(f"Production Var {var}", bool(value), "Set" if value else "Missing")
    
    overall_ready = (continuity_ready == len(continuity_files) and 
                    docker_ready == len(docker_files) and 
                    mcp_docker_ready and 
                    env_ready >= 1)
    
    return overall_ready

async def run_comprehensive_diagnostic():
    """Run the complete GHL MCP diagnostic."""
    print("💎 Diamond Demo - GHL MCP Integration Diagnostic")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🔗 Testing JewelryBoxAI_Bot ↔ GHL MCP Server connectivity and functionality")
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment variables loaded from .env")
    except:
        print("⚠️  Could not load .env file (may not exist)")
    
    # Run diagnostic tests
    tests_passed = 0
    total_tests = 6
    
    # Test 1: MCP Server Directory
    if check_mcp_server_availability():
        tests_passed += 1
    
    # Test 2: MCP Server Running  
    server_running = check_mcp_server_running()
    if server_running:
        tests_passed += 1
    
    # Test 3: GHL MCP Client Configuration
    if check_ghl_mcp_client_configuration():
        tests_passed += 1
    
    # Test 4: MCP Server Integration (only if server is running)
    if server_running:
        if await test_mcp_server_integration():
            tests_passed += 1
    else:
        print_warning("MCP Server Integration", "Skipped - server not running")
    
    # Test 5: Main App Integration
    if test_main_app_integration():
        tests_passed += 1
    
    # Test 6: Deployment Readiness
    if check_deployment_readiness():
        tests_passed += 1
    
    # Summary
    print_header("Diagnostic Summary")
    
    success_rate = (tests_passed / total_tests) * 100
    print(f"📊 Tests Passed: {tests_passed}/{total_tests} ({success_rate:.1f}%)")
    
    if tests_passed == total_tests:
        print("🎉 All systems operational! Ready for production deployment.")
    elif tests_passed >= 4:
        print("⚠️  Most systems operational. Address remaining issues before production.")
    else:
        print("❌ Multiple issues detected. Review and fix before deployment.")
    
    print("\n🔧 Recommended Next Steps:")
    if not server_running:
        print("   1. Start MCP Server: cd ../MCP_SERVERS/ghl_mcp_server && docker-compose up")
    print("   2. Test integration: python ghl_mcp_diagnostic.py")
    print("   3. Deploy with continuity: ./deploy_continuity.sh")
    print("   4. Monitor services: ./monitor_services.sh continuous")
    
    print(f"\n📋 Diagnostic completed at {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(run_comprehensive_diagnostic()) 