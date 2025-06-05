#!/usr/bin/env python3
"""
Diamond Family Assistant - Comprehensive System Diagnostic
Checks all components, integrations, and configurations.
"""

import os
import sys
import json
import importlib
import subprocess
import traceback
from datetime import datetime
from pathlib import Path

def print_header(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print('='*60)

def print_status(item, status, details=""):
    """Print status with emoji indicators."""
    emoji = "✅" if status else "❌"
    print(f"{emoji} {item:<40} {details}")

def print_warning(item, details=""):
    """Print warning with warning emoji."""
    print(f"⚠️  {item:<40} {details}")

def check_python_environment():
    """Check Python version and basic environment."""
    print_header("Python Environment")
    
    print(f"🐍 Python Version: {sys.version}")
    print(f"📁 Working Directory: {os.getcwd()}")
    print(f"📂 Python Path: {sys.executable}")
    
    # Check if we're in the right directory
    is_correct_dir = os.path.exists('src/app.py')
    print_status("Correct Project Directory", is_correct_dir)
    
    # Check Python version
    version_ok = sys.version_info >= (3, 8)
    print_status("Python Version >= 3.8", version_ok, f"({sys.version_info.major}.{sys.version_info.minor})")

def check_dependencies():
    """Check if required packages are installed."""
    print_header("Dependencies Check")
    
    required_packages = [
        'fastapi',
        'uvicorn', 
        'openai',
        'langchain',
        'langchain_openai',
        'langchain_core',
        'python_dotenv',
        'jinja2',
        'aiohttp',  # GHL MCP
        'requests'
    ]
    
    optional_packages = [
        'faiss-cpu',
        'numpy'
    ]
    
    print("Required Dependencies:")
    for package in required_packages:
        try:
            module = importlib.import_module(package.replace('-', '_'))
            version = getattr(module, '__version__', 'unknown')
            print_status(package, True, f"v{version}")
        except ImportError:
            print_status(package, False, "NOT INSTALLED")
    
    print("\nOptional Dependencies:")
    for package in optional_packages:
        try:
            module = importlib.import_module(package.replace('-', '_'))
            version = getattr(module, '__version__', 'unknown')
            print_status(package, True, f"v{version}")
        except ImportError:
            print_warning(package, "Not installed (optional)")

def check_environment_variables():
    """Check environment variables configuration."""
    print_header("Environment Variables")
    
    # Required variables
    required_vars = {
        'OPENAI_API_KEY': 'OpenAI API key for LLM access'
    }
    
    # Optional variables
    optional_vars = {
        'GHL_MCP_SERVER_URL': 'GoHighLevel MCP server URL',
        'GHL_DEFAULT_CALENDAR_ID': 'Default GHL calendar ID',
        'GHL_CALENDAR_JEWELLER_ID': 'GHL jewelry calendar ID',
        'GHL_CALENDAR_AUDIT_ID': 'GHL audit calendar ID',
        'GHL_CALENDAR_BOOKCALL_ID': 'GHL consultation calendar ID',
        'TAVILY_API_KEY': 'Tavily web search API key',
        'ALLOWED_ORIGINS': 'CORS allowed origins',
        'PORT': 'Server port',
        'HOST': 'Server host'
    }
    
    print("Required Environment Variables:")
    for var, desc in required_vars.items():
        value = os.getenv(var)
        if value:
            masked = value[:8] + "..." if len(value) > 8 else value
            print_status(var, True, f"Set ({masked})")
        else:
            print_status(var, False, "MISSING")
    
    print("\nOptional Environment Variables:")
    for var, desc in optional_vars.items():
        value = os.getenv(var)
        if value:
            masked = value[:12] + "..." if len(value) > 12 else value
            print_status(var, True, f"Set ({masked})")
        else:
            print_warning(var, "Not set")

def check_file_structure():
    """Check if all required files and directories exist."""
    print_header("File Structure")
    
    required_files = [
        'src/app.py',
        'src/__init__.py',
        'src/templates/widget.html',
        'src/prompts/prompt.json',
        'src/prompts/diamond_family_kb.json',
        'requirements.txt',
        'Dockerfile',
        'docker-compose.yml'
    ]
    
    ghl_files = [
        'src/tools/__init__.py',
        'src/tools/ghl_mcp_client.py',
        'src/tools/test_ghl_integration.py'
    ]
    
    optional_files = [
        'src/tools/web_search_tool.py',
        'src/memory_manager.py',
        '.env',
        '.env.example'
    ]
    
    print("Required Files:")
    for file_path in required_files:
        exists = os.path.exists(file_path)
        size = ""
        if exists:
            size = f"({os.path.getsize(file_path)} bytes)"
        print_status(file_path, exists, size)
    
    print("\nGHL MCP Integration Files:")
    for file_path in ghl_files:
        exists = os.path.exists(file_path)
        size = ""
        if exists:
            size = f"({os.path.getsize(file_path)} bytes)"
        print_status(file_path, exists, size)
    
    print("\nOptional Files:")
    for file_path in optional_files:
        exists = os.path.exists(file_path)
        if exists:
            size = f"({os.path.getsize(file_path)} bytes)"
            print_status(file_path, True, size)
        else:
            print_warning(file_path, "Not present")

def check_imports():
    """Check if imports work correctly."""
    print_header("Import Tests")
    
    imports_to_test = [
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'uvicorn'),
        ('openai', 'OpenAI client'),
        ('langchain_openai', 'LangChain OpenAI'),
        ('langchain_core.chat_history', 'LangChain Chat History'),
        ('python_dotenv', 'python-dotenv'),
        ('jinja2', 'Jinja2 Templates'),
        ('aiohttp', 'Async HTTP Client')
    ]
    
    for module_name, description in imports_to_test:
        try:
            importlib.import_module(module_name)
            print_status(description, True, f"'{module_name}' imported successfully")
        except ImportError as e:
            print_status(description, False, f"Import error: {str(e)}")

def check_ghl_integration():
    """Check GHL MCP integration components."""
    print_header("GHL MCP Integration")
    
    try:
        # Test importing GHL components
        sys.path.append('src')
        from tools.ghl_mcp_client import GHLMCPClient, GHLAppointmentScheduler, CustomerInfoExtractor
        print_status("GHL MCP Client Import", True, "All classes imported")
        
        # Test basic functionality
        extractor = CustomerInfoExtractor()
        test_text = "Call me at john@test.com or (555) 123-4567"
        result = extractor.extract_contact_info(test_text)
        
        has_email = result.get('email') == 'john@test.com'
        has_phone = result.get('phone') == '(555) 123-4567'
        
        print_status("Contact Info Extraction", has_email and has_phone, f"Email: {has_email}, Phone: {has_phone}")
        
        # Test calendar selection
        mock_client = GHLMCPClient("https://mock-server.com")
        calendar = mock_client.select_calendar("I need my jewelry appraised")
        print_status("Calendar Selection", True, f"Selected appropriate calendar")
        
    except Exception as e:
        print_status("GHL MCP Integration", False, f"Error: {str(e)}")
        print(f"   Traceback: {traceback.format_exc()}")

def check_openai_connection():
    """Test OpenAI API connection."""
    print_header("OpenAI API Connection")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print_status("OpenAI API Key", False, "Not configured")
        return
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        # Simple test call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'API test successful'"}],
            max_tokens=10
        )
        
        if response.choices[0].message.content:
            print_status("OpenAI API Connection", True, "Connection successful")
            print_status("GPT-4o-mini Model", True, "Model accessible")
        else:
            print_status("OpenAI API Connection", False, "No response received")
            
    except Exception as e:
        print_status("OpenAI API Connection", False, f"Error: {str(e)}")

def check_server_startup():
    """Check if the server can start properly."""
    print_header("Server Startup Test")
    
    try:
        # Import the app
        sys.path.append('src')
        from app import app, validate_environment
        
        print_status("App Import", True, "FastAPI app imported successfully")
        
        # Test environment validation
        try:
            validate_environment()
            print_status("Environment Validation", True, "All required variables present")
        except SystemExit:
            print_status("Environment Validation", False, "Missing required environment variables")
        
        # Check if app has expected routes
        routes = [route.path for route in app.routes]
        expected_routes = ['/chat', '/widget', '/schedule_appointment', '/clear_chat']
        
        for route in expected_routes:
            has_route = route in routes
            print_status(f"Route {route}", has_route)
            
    except Exception as e:
        print_status("Server Startup", False, f"Error: {str(e)}")

def run_diagnostic():
    """Run complete diagnostic."""
    print("🏥 Diamond Family Assistant - System Diagnostic")
    print(f"⏰ Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment variables loaded from .env")
    except:
        print("⚠️  Could not load .env file (may not exist)")
    
    # Run all checks
    check_python_environment()
    check_dependencies() 
    check_environment_variables()
    check_file_structure()
    check_imports()
    check_ghl_integration()
    check_openai_connection()
    check_server_startup()
    
    # Summary
    print_header("Diagnostic Summary")
    print("🔧 Fix Priority:")
    print("   1. Install missing required dependencies")
    print("   2. Set OPENAI_API_KEY environment variable")
    print("   3. Configure GHL MCP variables for appointment scheduling")
    print("   4. Test server startup: python src/app.py")
    
    print(f"\n📋 Diagnostic completed at {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    run_diagnostic() 