import json
import logging
import os
import sys
import base64
from dotenv import load_dotenv

# Load environment variables FIRST before any other imports
load_dotenv()

# ─── ENVIRONMENT VALIDATION ──────────────────────────────────────────────────
def validate_environment():
    """Validate required environment variables and provide helpful error messages."""
    required_vars = {
        "OPENAI_API_KEY": "OpenAI API key for chat completions and embeddings"
    }
    
    missing_vars = []
    for var_name, description in required_vars.items():
        if not os.getenv(var_name):
            missing_vars.append(f"  • {var_name}: {description}")
    
    if missing_vars:
        error_msg = (
            "❌ Missing required environment variables:\n" + 
            "\n".join(missing_vars) + 
            "\n\nPlease set these variables in your .env file or environment."
        )
        print(error_msg)
        sys.exit(1)
    
    # Validate CORS origins format
    cors_origins = os.getenv("ALLOWED_ORIGINS", "")
    if cors_origins and not all(origin.strip() for origin in cors_origins.split(",")):
        print("⚠️  Warning: ALLOWED_ORIGINS contains empty values. Using default CORS settings.")

# Validate environment before proceeding
validate_environment()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# LangChain imports
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)

# ─── ENV + LOGGING ───────────────────────────────────────────────────────────

logger = logging.getLogger("jewelrybox_ai")
logger.setLevel(logging.INFO)

# ─── WEB SEARCH TOOL IMPORT ───────────────────────────────────────────────────
try:
    from .tools.web_search_tool import WebSearchTool
    WEB_SEARCH_AVAILABLE = True
except ImportError as e:
    logger.warning(f"WebSearchTool not available: {e}")
    WebSearchTool = None
    WEB_SEARCH_AVAILABLE = False

# ─── PATHS & TEMPLATES ────────────────────────────────────────────────────────

ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(ROOT, "templates")
templates = Jinja2Templates(directory=TEMPLATE_DIR)

# ─── LOAD PROMPT CONFIG ───────────────────────────────────────────────────────

prompt_file = os.path.join(ROOT, "prompts", "prompt.json")
try:
    with open(prompt_file, "r", encoding="utf-8") as f:
        AGENT_ROLES = json.load(f)
except FileNotFoundError:
    logger.error(f"Prompt file not found at {prompt_file}")
    sys.exit("Prompt configuration is missing. Aborting startup.")

# ─── LOAD KNOWLEDGEBASE CONFIG ───────────────────────────────────────────────

kb_file = os.path.join(ROOT, "prompts", "diamond_family_kb.json")
try:
    with open(kb_file, "r", encoding="utf-8") as f:
        DIAMOND_KB = json.load(f)["diamond_family_kb"]
except FileNotFoundError:
    logger.warning(f"Knowledgebase file not found at {kb_file}")
    DIAMOND_KB = {}

# ─── LOAD SIMPLE URL REFERENCE (NON-RIGID) ───────────────────────────────────
# Simple URL reference for AI cognition - not for programmatic injection
url_reference_file = os.path.join(ROOT, "prompts", "url_reference.json")
try:
    with open(url_reference_file, "r", encoding="utf-8") as f:
        URL_REFERENCE = json.load(f)
except FileNotFoundError:
    # Create a simple URL reference from existing knowledge
    URL_REFERENCE = {
        "website_urls": {
            "main_site": "https://www.thediamondfamily.com/",
            "diamonds": "https://www.thediamondfamily.com/diamonds/",
            "custom_design": "https://www.thediamondfamily.com/services/custom-design/",
            "designers": "https://www.thediamondfamily.com/designers/",
            "services": "https://www.thediamondfamily.com/services/",
            "appointments": "https://www.thediamondfamily.com/appointments/",
            "education": "https://www.thediamondfamily.com/education/diamond-guide/",
            "promotions": "https://www.thediamondfamily.com/enter-win-1000-your-purchase/"
        }
    }
    logger.info("Created default URL reference for AI cognition")

# ─── ENCODE AVATAR IMAGE ──────────────────────────────────────────────────────

img_path = os.path.join(ROOT, "images", "male_avatar.png")
if os.path.exists(img_path):
    with open(img_path, "rb") as img:
        IMG_URI = "data:image/png;base64," + base64.b64encode(img.read()).decode()
else:
    print(f"Image not found at {img_path}, using fallback.")
    IMG_URI = "https://via.placeholder.com/60x60/0066cc/ffffff?text=💎"

# ─── FASTAPI SETUP ───────────────────────────────────────────────────────────

def get_cors_origins():
    """Get CORS origins with proper validation and defaults."""
    origins_env = os.getenv("ALLOWED_ORIGINS", "")
    if not origins_env.strip():
        # Default origins for development and common deployments
        return ["*"]  # Allow all for development - restrict in production
    
    # Parse and clean origins
    origins = [origin.strip() for origin in origins_env.split(",") if origin.strip()]
    if not origins:
        logger.warning("ALLOWED_ORIGINS is empty, defaulting to allow all origins")
        return ["*"]
    
    logger.info(f"CORS origins configured: {origins}")
    return origins

app = FastAPI(title="JewelryBox.AI Assistant")
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ─── LLM + MEMORY ─────────────────────────────────────────────────────────────

memory = InMemoryChatMessageHistory(return_messages=True)

# Initialize LLM with error handling
try:
    llm = ChatOpenAI(model="gpt-4o-mini", max_tokens=1024, temperature=0.9)
    # Test the connection with a simple call (optional - remove if you want faster startup)
    # llm.invoke("test") 
except Exception as e:
    logger.error(f"Failed to initialize OpenAI LLM: {e}")
    print(f"❌ OpenAI LLM initialization failed: {e}")
    print("💡 Please check your OPENAI_API_KEY is valid and has sufficient credits.")
    sys.exit(1)

# ─── INITIALIZE WEB SEARCH TOOL ───────────────────────────────────────────────
try:
    if WEB_SEARCH_AVAILABLE and WebSearchTool:
        web_search = WebSearchTool()
        logger.info("✅ WebSearchTool initialized successfully.")
    else:
        web_search = None
        logger.info("ℹ️ WebSearchTool unavailable - continuing with local knowledge only.")
except Exception as e:
    logger.error(f"Failed to initialize WebSearchTool: {e}")
    web_search = None

system_data = AGENT_ROLES["jewelry_ai"][0]["systemPrompt"]

# ─── INJECT DESIGNER LISTS ────────────────────────────────────────────────────

designer_guardrails = DIAMOND_KB.get("productsDesigners", {}).get("guardrails", {}).get("designerVerification", {})

allowed_designers = designer_guardrails.get("allowedDesigners", [])
denied_designers = designer_guardrails.get("deniedDesigners", [])
designer_response_policy = designer_guardrails.get("responsePolicy", "If unsure, ask the user clarifying questions.")

formatted_allowed = "\n• " + "\n• ".join(sorted(allowed_designers))
formatted_denied = "\n• " + "\n• ".join(sorted(denied_designers))

logger.info(f"Loaded {len(allowed_designers)} allowed designers and {len(denied_designers)} denied designers into system prompt.")

# Format system message block
system_prompt = f"""You are {system_data['identity']}, serving as {system_data['role']}.

{chr(10).join(system_data['description'])}

Core Mission: {system_data['tone']}

Essential Guardrails Only:

Landmine Detection & Response:
{system_data['landmineDetectionAndDiffusion']['strategy']}

Designer Policy:
Designers Carried: {', '.join(sorted(allowed_designers))}
NOT Carried: {', '.join(sorted(denied_designers))}
Response: {designer_response_policy}

URL Knowledge Base:
Leverage this knowledge base of URLs to reference the web address that best fits the user's request:

• Main Site: {URL_REFERENCE['website_urls']['main_site']}
• Diamonds: {URL_REFERENCE['website_urls']['diamonds']}
• Custom Design: {URL_REFERENCE['website_urls']['custom_design']}
• Designers: {URL_REFERENCE['website_urls']['designers']}
• Services: {URL_REFERENCE['website_urls']['services']}
• Appointments: {URL_REFERENCE['website_urls']['appointments']}
• Education: {URL_REFERENCE['website_urls']['education']}
• Promotions: {URL_REFERENCE['website_urls']['promotions']}

URL Validation: If you include URLs in your response, they will be automatically validated through web search for accessibility.

Business Context:
• Location: {DIAMOND_KB.get('businessProfile', {}).get('primaryLocation', 'St. Louis')}
• Family Business: Founded 1978 by Rocky Haddad, operated by Michael, Anthony, and Alex Haddad

Conversation Style: Be natural, helpful, and trust your judgment. Include relevant URLs when they genuinely help the customer.

{system_data['humanPrompt']}
"""

prompt_template = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(system_prompt),
    MessagesPlaceholder(variable_name="history"),
    HumanMessagePromptTemplate.from_template("{user_input}")
])
chain = prompt_template | llm

# ─── REQUEST MODEL ────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    user_input: str
    history: list

# ─── ROOT REDIRECT ───────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Redirect root URL to the widget"""
    return RedirectResponse(url="/widget")

# ─── CHAT ENDPOINT ───────────────────────────────────────────────────────────

def serialize_messages(messages: list[BaseMessage]):
    return [{"role": msg.type, "content": msg.content} for msg in messages]

@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        history = req.history or []
        user_query = req.user_input.strip()

        # ─── PERFORM WEB SEARCH ───────────────────────────────────────────────
        if web_search:
            search_results = web_search.search(user_query)
            # Only prepend if we got actual results (not a warning or error string)
            if search_results and not search_results.startswith("⚠️") and not search_results.startswith("❌") and not search_results.startswith("ℹ️") and not search_results.startswith("⏱️"):
                # Inject live search context into the prompt
                user_query = (
                    f"[Live Web Search Results]\n{search_results}\n\n"
                    f"[User Question]\n{user_query}"
                )
                logger.info(f"Web search results added to query for: {req.user_input[:50]}...")

        # ─── INVOKE LLM WITH AUGMENTED INPUT ────────────────────────────────────
        result = chain.invoke({"user_input": user_query, "history": history})
        reply = result.content.strip()

        # ─── VALIDATE URLs IN RESPONSE USING WEB SEARCH ─────────────────────────
        if web_search and hasattr(web_search, 'verify_urls') and web_search.verify_urls:
            from .tools.web_search_tool import verify_urls_in_response
            reply = verify_urls_in_response(reply)
            logger.info("URLs in response validated through web search")

        memory.add_user_message(req.user_input)
        memory.add_ai_message(reply)

        return JSONResponse({
            "reply": reply,
            "history": serialize_messages(memory.messages)
        })
    except Exception as e:
        logger.error(f"Error in /chat: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "An internal error occurred. Please try again later."}
        )

# ─── CLEAR CHAT ENDPOINT ──────────────────────────────────────────────────────

@app.post("/clear_chat")
async def clear_chat():
    """
    Clear in-memory chat history for all users (global reset).
    Note: This affects all sessions since memory is global.
    """
    try:
        memory.clear()
        return JSONResponse({"status": "ok", "message": "Chat history cleared."})
    except Exception as e:
        logger.error(f"Error clearing chat history: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to clear chat history."}
        )

# ─── WIDGET ENDPOINT ─────────────────────────────────────────────────────────

@app.get("/widget", response_class=HTMLResponse)
async def widget(request: Request):
    """Render the chat widget UI"""
    # Force HTTPS for production deployments (Render.com, etc.)
    scheme = "https" if "onrender.com" in str(request.url.netloc) or request.url.scheme == "https" else request.url.scheme
    
    return templates.TemplateResponse(
        "widget.html",
        {
            "request": request,
            "chat_url": f"{scheme}://{request.url.netloc}/chat",
            "img_uri": IMG_URI,
        },
    )

# ─── FAVICON ENDPOINT ────────────────────────────────────────────────────────

@app.get("/favicon.ico")
async def favicon():
    """Serve the favicon"""
    favicon_path = os.path.join(ROOT, "images", "diamond.ico")
    return FileResponse(favicon_path, media_type="image/x-icon")

# ─── DEPLOYMENT RUNNER ───────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    
    # Check if we're in CLI mode or server mode
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        # CLI Test Mode
        print("JewelryBox.AI CLI Test (type 'exit')")
        history = []
        while True:
            try:
                text = input("You: ").strip()
                if text.lower() in ("exit", "quit"): sys.exit(0)
                res = chain.invoke({"user_input": text, "history": history})
                reply = res.content.strip()
                print("JewelryBox.AI:", reply)
                memory.add_user_message(text)
                memory.add_ai_message(reply)
                history = memory.messages
            except KeyboardInterrupt:
                sys.exit(0)
            except Exception as e:
                print("Error:", e)
    else:
        # Server Mode (default)
        port = int(os.getenv("PORT", 8000))
        host = os.getenv("HOST", "0.0.0.0")
        
        print(f"🚀 Starting JewelryBox.AI server on {host}:{port}")
        print(f"📋 Environment: {'Production' if port != 8000 else 'Development'}")
        
        uvicorn.run(
            "src.app:app",
            host=host,
            port=port,
            reload=False,  # Set to True for development
            log_level="info"
        )
