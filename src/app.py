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
    
    # Optional GHL MCP variables - warn if missing but don't fail
    optional_ghl_vars = {
        "GHL_MCP_SERVER_URL": "GoHighLevel MCP server URL for appointment scheduling"
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
    
    # Check optional GHL variables
    missing_ghl_vars = []
    for var_name, description in optional_ghl_vars.items():
        if not os.getenv(var_name):
            missing_ghl_vars.append(f"  • {var_name}: {description}")
    
    if missing_ghl_vars:
        print("⚠️  Warning: GoHighLevel MCP features will be disabled. Missing variables:")
        print("\n".join(missing_ghl_vars))
    
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

logger = logging.getLogger("diamond_family_ai")
logger.setLevel(logging.INFO)

# ─── WEB SEARCH TOOL IMPORT ───────────────────────────────────────────────────
try:
    # Try relative import first (when running as module)
    from .tools.web_search_tool import WebSearchTool
    WEB_SEARCH_AVAILABLE = True
except ImportError:
    try:
        # Try absolute import (when running directly)
        import sys
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from tools.web_search_tool import WebSearchTool
        WEB_SEARCH_AVAILABLE = True
    except ImportError as e:
        logger.warning(f"WebSearchTool not available: {e}")
        WebSearchTool = None
        WEB_SEARCH_AVAILABLE = False

# ─── GHL MCP TOOL IMPORT ──────────────────────────────────────────────────────
try:
    # Try relative import first (when running as module)
    from .tools.ghl_mcp_client import GHLMCPClient, GHLAppointmentScheduler, CustomerInfoExtractor
    GHL_MCP_AVAILABLE = True
except ImportError:
    try:
        # Try absolute import (when running directly)
        import sys
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from tools.ghl_mcp_client import GHLMCPClient, GHLAppointmentScheduler, CustomerInfoExtractor
        GHL_MCP_AVAILABLE = True
    except ImportError as e:
        logger.warning(f"GHL MCP Client not available: {e}")
        GHLMCPClient = None
        GHLAppointmentScheduler = None
        CustomerInfoExtractor = None
        GHL_MCP_AVAILABLE = False

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

# ─── EXTRACT ALL PROMPT ARRAYS FOR DYNAMIC ACCESS ────────────────────────────

system_data = AGENT_ROLES["jewelry_ai"][0]["systemPrompt"]

# Create a comprehensive reference system for all arrays
PROMPT_ARRAYS = {
    "identity": system_data.get('identity', ''),
    "role": system_data.get('role', ''),
    "tone": system_data.get('tone', ''),
    "description": system_data.get('description', []),
    "knowledgeDomains": system_data.get('knowledgeDomains', []),
    "customerServiceExcellence": system_data.get('customerServiceExcellence', []),
    "pricingGuidance": system_data.get('pricingGuidance', []),
    "careAndMaintenance": system_data.get('careAndMaintenance', []),
    "giftGuidance": system_data.get('giftGuidance', []),
    "signatureCloser": system_data.get('signatureCloser', []),
    "tagline": system_data.get('tagline', ''),
    "humanPrompt": system_data.get('humanPrompt', ''),
    
    # Anti-looping strategies
    "antiLoopingPrinciples": system_data.get('antiLooping', {}).get('principles', []),
    "antiLoopingTechniques": system_data.get('antiLooping', {}).get('variationTechniques', []),
    "contextAwareness": system_data.get('antiLooping', {}).get('contextAwareness', []),
    
    # Style guides
    "styleFormatting": system_data.get('styleGuide', {}).get('formatting', []),
    "styleLanguage": system_data.get('styleGuide', {}).get('language', []),
    "responsePrinciples": system_data.get('styleGuide', {}).get('responseStructure', {}).get('principles', []),
    
    # Diamond Family specific data
    "currentLeadership": system_data.get('diamondFamilyExpertise', {}).get('foundingAndHistory', {}).get('currentLeadership', []),
    "companyValues": system_data.get('diamondFamilyExpertise', {}).get('cultureAndMission', {}).get('values', []),
    "affiliations": system_data.get('diamondFamilyExpertise', {}).get('corporateSizeAndConnections', {}).get('affiliations', []),
    "charityInitiatives": system_data.get('diamondFamilyExpertise', {}).get('philanthropy', {}).get('initiatives', []),
    "promotionDates": system_data.get('diamondFamilyExpertise', {}).get('recentNews', {}).get('dates', []),
    "localCompetitors": system_data.get('diamondFamilyExpertise', {}).get('competition', {}).get('localCompetitors', []),
    "nationalCompetitors": system_data.get('diamondFamilyExpertise', {}).get('competition', {}).get('nationalCompetitors', []),
    "onlineCompetitors": system_data.get('diamondFamilyExpertise', {}).get('competition', {}).get('onlineCompetitors', []),
    "inHouseServices": system_data.get('diamondFamilyExpertise', {}).get('uniqueSellingPoints', {}).get('inHouseServices', []),
    
    # Agent capabilities
    "agentCapabilities": system_data.get('agentCapabilities', []),
    
    # Landmine categories
    "landmineStrategy": system_data.get('landmineDetectionAndDiffusion', {}).get('strategy', ''),
    "landmineCategories": system_data.get('landmineDetectionAndDiffusion', {}).get('categories', {}),
}

# ─── LOAD KNOWLEDGEBASE CONFIG ───────────────────────────────────────────────

kb_file = os.path.join(ROOT, "prompts", "diamond_family_kb.json")
try:
    with open(kb_file, "r", encoding="utf-8") as f:
        DIAMOND_KB = json.load(f)["diamond_family_kb"]
except FileNotFoundError:
    logger.warning(f"Knowledgebase file not found at {kb_file}")
    DIAMOND_KB = {}

# ─── ADD EVENTS AND PROMOTIONS TO PROMPT ARRAYS ──────────────────────────────

# Extract events and promotions from DIAMOND_KB and add to prompt arrays
events_promotions = DIAMOND_KB.get('eventsPromotions', {})
upcoming_events = events_promotions.get('calendar', [])
current_offer = events_promotions.get('currentOffer', '')

# Add to PROMPT_ARRAYS for easy access
PROMPT_ARRAYS.update({
    "upcomingEvents": upcoming_events,
    "currentOffer": current_offer,
    "businessHours": DIAMOND_KB.get('businessProfile', {}).get('hoursOfOperation', {}),
    "teamMembers": DIAMOND_KB.get('team', {}).get('members', []),
    "allowedDesigners": DIAMOND_KB.get('productsDesigners', {}).get('guardrails', {}).get('designerVerification', {}).get('allowedDesigners', []),
    "deniedDesigners": DIAMOND_KB.get('productsDesigners', {}).get('guardrails', {}).get('designerVerification', {}).get('deniedDesigners', [])
})

def get_prompt_array(array_name: str) -> list:
    """
    Dynamically access any prompt array by name.
    Usage: get_prompt_array('knowledgeDomains') returns the knowledge domains list
    """
    return PROMPT_ARRAYS.get(array_name, [])

def format_array_as_text(array_name: str, prefix: str = "• ") -> str:
    """
    Format a prompt array as readable text.
    Usage: format_array_as_text('knowledgeDomains') returns formatted string
    """
    array_data = get_prompt_array(array_name)
    if isinstance(array_data, list):
        return "\n".join([f"{prefix}{item}" for item in array_data])
    return str(array_data)

def get_agent_responsibilities(agent_type: str) -> list:
    """
    Get responsibilities for a specific agent type.
    Usage: get_agent_responsibilities('SalesAgent')
    """
    capabilities = get_prompt_array('agentCapabilities')
    for agent in capabilities:
        if agent.get('agent') == agent_type:
            return agent.get('responsibilities', [])
    return []

def format_upcoming_events() -> str:
    """Format upcoming events for AI response."""
    events = get_prompt_array('upcomingEvents')
    if not events:
        return "No upcoming events scheduled."
    
    formatted_events = []
    for event in events:
        event_text = f"• **{event.get('event', 'Event')}**"
        if event.get('dates'):
            event_text += f" - {event.get('dates')}"
        elif event.get('date'):
            event_text += f" - {event.get('date')}"
        
        if event.get('location'):
            event_text += f" ({event.get('location')})"
        
        if event.get('details'):
            event_text += f": {event.get('details')}"
        
        formatted_events.append(event_text)
    
    return "\n".join(formatted_events)

def get_current_promotions() -> str:
    """Get current promotions and offers."""
    current_offer = get_prompt_array('currentOffer')
    if current_offer:
        return f"Current Promotion: Win $1000 towards your purchase! Enter at {current_offer}"
    return "Check our website for current promotions and offers."

# Log available arrays for debugging
logger.info(f"Loaded {len(PROMPT_ARRAYS)} prompt arrays: {', '.join(PROMPT_ARRAYS.keys())}")

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

app = FastAPI(title="Diamond Family Assistant")
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

# ─── INITIALIZE GHL MCP CLIENT ────────────────────────────────────────────────
try:
    if GHL_MCP_AVAILABLE and GHLMCPClient and os.getenv("GHL_MCP_SERVER_URL"):
        ghl_mcp_client = GHLMCPClient(os.getenv("GHL_MCP_SERVER_URL"))
        ghl_scheduler = GHLAppointmentScheduler(ghl_mcp_client)
        ghl_extractor = CustomerInfoExtractor()
        logger.info("✅ GHL MCP Client initialized successfully.")
    else:
        ghl_mcp_client = None
        ghl_scheduler = None  
        ghl_extractor = None
        logger.info("ℹ️ GHL MCP Client unavailable - appointment scheduling disabled.")
except Exception as e:
    logger.error(f"Failed to initialize GHL MCP Client: {e}")
    ghl_mcp_client = None
    ghl_scheduler = None
    ghl_extractor = None

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

URL Formatting Instructions:
Use natural, conversational formatting for URLs. Examples:
• GOOD: "You can explore our collection at The Diamond Family website: https://www.thediamondfamily.com/diamonds/"
• GOOD: "Check out our designers online at https://www.thediamondfamily.com/designers/"
• AVOID: "[The Diamond Family](https://www.thediamondfamily.com/)" 
• AVOID: Any markdown bracket formatting around URLs
• Include the business name naturally in text, then provide the clean URL

Available Knowledge Arrays (access when contextually relevant):

Business Leadership: {', '.join(get_prompt_array('currentLeadership'))}
Company Values: {', '.join(get_prompt_array('companyValues'))}
In-House Services: {', '.join(get_prompt_array('inHouseServices'))}
Customer Service Excellence: Available for detailed guidance
Pricing Guidance: Available for value discussions
Care & Maintenance: Available for product care advice
Gift Guidance: Available for gift recommendations
Anti-Looping Techniques: Available for conversation variation

Competition Context:
• Local: {', '.join(get_prompt_array('localCompetitors'))}
• National: {', '.join(get_prompt_array('nationalCompetitors'))}
• Online: {', '.join(get_prompt_array('onlineCompetitors'))}

Agent Capabilities Available:
{chr(10).join([f"• {agent.get('agent', '')}: {len(agent.get('responsibilities', []))} capabilities" for agent in get_prompt_array('agentCapabilities')])}

Business Context:
• Location: {DIAMOND_KB.get('businessProfile', {}).get('primaryLocation', 'St. Louis')}
• Family Business: Founded 1978 by Rocky Haddad, operated by {', '.join(get_prompt_array('currentLeadership'))}
• Tagline: {get_prompt_array('tagline')}

Upcoming Events & Promotions:
{format_upcoming_events()}

Current Promotions:
{get_current_promotions()}

Business Hours:
{chr(10).join([f"• {day}: {hours}" for day, hours in get_prompt_array('businessHours').items()]) if get_prompt_array('businessHours') else "• Contact us for current hours"}

Conversation Style: Be natural, helpful, and completely human in your responses. Include relevant URLs when they genuinely help the customer. Access knowledge arrays contextually when they add value to your response. Never use AI-like language or disclaimers. Always mention upcoming events and current promotions when relevant to the conversation.

{system_data['humanPrompt']}
"""

prompt_template = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(system_prompt),
    MessagesPlaceholder(variable_name="history"),
    HumanMessagePromptTemplate.from_template("{user_input}")
])
chain = prompt_template | llm

# ─── REQUEST MODELS ───────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    user_input: str
    history: list

class AppointmentRequest(BaseModel):
    customer_name: str
    customer_email: str
    customer_phone: str
    preferred_time: str = None
    appointment_type: str = "consultation"
    conversation_messages: list = []

# ─── ROOT REDIRECT ───────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Redirect root URL to the widget"""
    return RedirectResponse(url="/widget")

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and load balancers"""
    from datetime import datetime
    return JSONResponse({
        "status": "healthy",
        "mcp_available": ghl_mcp_client is not None,
        "mcp_server": os.getenv("GHL_MCP_SERVER_URL", "Not configured"),
        "web_search_available": web_search is not None,
        "events_loaded": len(get_prompt_array('upcomingEvents')),
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    })

# ─── CHAT ENDPOINT ───────────────────────────────────────────────────────────

def serialize_messages(messages: list[BaseMessage]):
    return [{"role": msg.type, "content": msg.content} for msg in messages]

@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        history = req.history or []
        user_query = req.user_input.strip()

        # ─── DETECT APPOINTMENT REQUESTS ─────────────────────────────────────────
        appointment_indicators = [
            'appointment', 'schedule', 'meeting', 'visit', 'come in',
            'book', 'reserve', 'consultation', 'see you', 'meet'
        ]
        
        user_lower = user_query.lower()
        is_appointment_request = any(indicator in user_lower for indicator in appointment_indicators)
        
        # ─── EXTRACT CONTACT INFO IF APPOINTMENT REQUESTED ──────────────────────
        appointment_context = {}
        if is_appointment_request and ghl_extractor:
            # Look for contact info in current message and recent history
            conversation_text = user_query
            if history:
                recent_messages = history[-5:] if len(history) > 5 else history
                conversation_text += " " + " ".join([msg.get("content", "") for msg in recent_messages])
            
            extracted_info = ghl_extractor.extract_contact_info(conversation_text)
            appointment_context.update(extracted_info)
            
            logger.info(f"Appointment request detected. Extracted info: {extracted_info}")

        # ─── ENHANCE QUERY WITH RELEVANT PROMPT ARRAYS ──────────────────────────
        query_enhancements = []
        
        # Detect when specific knowledge would be helpful
        if any(word in user_lower for word in ['service', 'repair', 'fix', 'maintenance', 'cleaning']):
            query_enhancements.append(f"In-House Services: {format_array_as_text('inHouseServices')}")
            
        if any(word in user_lower for word in ['price', 'cost', 'budget', 'value', 'investment']):
            query_enhancements.append(f"Pricing Guidance: {format_array_as_text('pricingGuidance')}")
            
        if any(word in user_lower for word in ['care', 'clean', 'maintain', 'storage', 'protect']):
            query_enhancements.append(f"Care & Maintenance: {format_array_as_text('careAndMaintenance')}")
            
        if any(word in user_lower for word in ['gift', 'present', 'surprise', 'anniversary', 'birthday']):
            query_enhancements.append(f"Gift Guidance: {format_array_as_text('giftGuidance')}")
            
        if any(word in user_lower for word in ['help', 'service', 'experience', 'customer']):
            query_enhancements.append(f"Customer Service Excellence: {format_array_as_text('customerServiceExcellence')}")
            
        if any(word in user_lower for word in ['competition', 'competitor', 'compare', 'versus', 'vs']):
            competitors = get_prompt_array('localCompetitors') + get_prompt_array('nationalCompetitors') + get_prompt_array('onlineCompetitors')
            query_enhancements.append(f"Competition Context: Local/National/Online competitors include {', '.join(competitors)}")
        
        # ─── ADD EVENTS AND PROMOTIONS CONTEXT ───────────────────────────────────
        if any(word in user_lower for word in ['event', 'events', 'promotion', 'sale', 'discount', 'special', 'offer', 'deal', 'campaign', 'upcoming']):
            upcoming_events = format_upcoming_events()
            current_promo = get_current_promotions()
            query_enhancements.append(f"Upcoming Events:\n{upcoming_events}")
            query_enhancements.append(f"Current Promotions: {current_promo}")
        
        # ─── ADD BUSINESS HOURS CONTEXT ───────────────────────────────────────────
        if any(word in user_lower for word in ['hours', 'open', 'closed', 'when', 'time', 'schedule']):
            business_hours = get_prompt_array('businessHours')
            if business_hours:
                hours_text = "\n".join([f"• {day}: {hours}" for day, hours in business_hours.items()])
                query_enhancements.append(f"Business Hours:\n{hours_text}")

        # ─── ADD APPOINTMENT CAPABILITY CONTEXT ─────────────────────────────────
        if is_appointment_request and ghl_scheduler:
            ghl_status = "✅ Available" if ghl_scheduler else "❌ Unavailable"
            query_enhancements.append(f"Appointment Scheduling: {ghl_status}. You can help customers schedule appointments and will collect their contact information (name, email, phone) for booking.")

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

        # ─── ADD CONTEXTUAL KNOWLEDGE ARRAYS IF RELEVANT ────────────────────────
        if query_enhancements:
            enhanced_context = "\n\n[Relevant Knowledge Context]\n" + "\n\n".join(query_enhancements)
            user_query = user_query + enhanced_context
            logger.info(f"Added {len(query_enhancements)} knowledge arrays to query")

        # ─── INVOKE LLM WITH AUGMENTED INPUT ────────────────────────────────────
        result = chain.invoke({"user_input": user_query, "history": history})
        reply = result.content.strip()

        # ─── ENHANCE REPLY WITH APPOINTMENT SCHEDULING INFO ─────────────────────
        if is_appointment_request:
            if ghl_scheduler:
                if appointment_context.get("email") and appointment_context.get("phone"):
                    # We have contact info, suggest scheduling
                    reply += f"\n\n💎 I can help you schedule that appointment right away! I have your email ({appointment_context['email']}) and phone ({appointment_context['phone']}). Would you like me to book a consultation for you?"
                else:
                    # Missing contact info, request it
                    missing_info = []
                    if not appointment_context.get("email"):
                        missing_info.append("email address")
                    if not appointment_context.get("phone"):
                        missing_info.append("phone number")
                    
                    reply += f"\n\n💎 I'd be happy to schedule an appointment for you! To get you booked, I'll need your {' and '.join(missing_info)}. Could you please provide that information?"
            else:
                # No GHL scheduler - turn into expo demo opportunity
                reply += f"\n\n💎 Perfect timing! You're seeing exactly what Anthony Haddad means by 'AI Marketing Genius'—imagine when our GHL integration is fully live, I could create your contact record, log our conversation, and book your Diamond Family appointment all while we're talking. That's the future we're building at JCK 2025. For now, let me connect you with our St. Louis showroom directly!"

        # ─── VALIDATE URLs IN RESPONSE USING WEB SEARCH ─────────────────────────
        if web_search and hasattr(web_search, 'verify_urls') and web_search.verify_urls:
            from .tools.web_search_tool import verify_urls_in_response
            # Silent verification - logs for debugging but doesn't modify user response
            verify_urls_in_response(reply)
            logger.info("URLs verified silently - no user-facing modifications")

        memory.add_user_message(req.user_input)
        memory.add_ai_message(reply)

        # ─── PREPARE RESPONSE WITH APPOINTMENT CONTEXT ──────────────────────────
        response_data = {
            "reply": reply,
            "history": serialize_messages(memory.messages)
        }
        
        # Add appointment scheduling context if available
        if is_appointment_request and appointment_context:
            response_data["appointment_context"] = {
                "detected": True,
                "extracted_info": appointment_context,
                "scheduling_available": ghl_scheduler is not None
            }

        return JSONResponse(response_data)
    except Exception as e:
        logger.error(f"Error in /chat: {e}", exc_info=True)
        # Turn technical errors into expo conversation opportunities
        expo_error_messages = [
            "Looks like my AI circuits are getting a workout at JCK! This is exactly the kind of innovation Anthony demonstrates at expos—when it works perfectly, it's magic. When it has a hiccup, it shows we're pushing boundaries. Let me reset and we'll keep the conversation flowing!",
            "Ha! Even AI assistants have their expo moments. This technical glitch actually highlights what makes Diamond Family special—we're pioneering tech that other jewelers won't touch for years. Anthony calls this 'being comfortably uncomfortable with innovation.' Give me one more try!",
            "Perfect demo moment! This is why Anthony Haddad is known as The AI Marketing Genius—we're literally stress-testing the future of jewelry retail at JCK 2025. When this tech is dialed in, conversations flow seamlessly from chat to contact creation to appointment booking. Let's restart!"
        ]
        import random
        error_message = random.choice(expo_error_messages)
        
        return JSONResponse(
            status_code=500,
            content={"error": error_message}
        )

# ─── APPOINTMENT SCHEDULING ENDPOINT ─────────────────────────────────────────

@app.post("/schedule_appointment")
async def schedule_appointment(req: AppointmentRequest):
    """
    Schedule an appointment via GoHighLevel MCP server.
    Creates contact, adds conversation notes, and schedules on appropriate calendar.
    """
    try:
        if not ghl_scheduler:
            # Turn the service unavailability into a demo opportunity
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "error": "Perfect timing! This is exactly why Anthony Haddad is pioneering AI in jewelry retail. While our GHL integration is getting polished up for the expo, imagine when this is live—I'd create your contact record, add our conversation notes, and book your appointment at Diamond Family all while we're chatting. This is the cutting-edge tech that makes us The AI Marketing Geniuses. For now, let's connect you directly with our St. Louis showroom!"
                }
            )
        
        # Schedule the appointment
        result = await ghl_scheduler.schedule_from_conversation(
            conversation_messages=req.conversation_messages,
            customer_name=req.customer_name,
            customer_email=req.customer_email,
            customer_phone=req.customer_phone,
            preferred_time=req.preferred_time,
            appointment_type=req.appointment_type
        )
        
        if result["success"]:
            logger.info(f"✅ Appointment scheduled successfully for {req.customer_name}")
            return JSONResponse({
                "success": True,
                "message": f"Your appointment has been scheduled successfully!",
                "appointment_time": result["appointment_time"],
                "calendar_type": result["calendar_type"],
                "details": result.get("result", {})
            })
        else:
            logger.error(f"❌ Appointment scheduling failed: {result['error']}")
            # Turn the technical error into a demonstration opportunity
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": f"You know what's brilliant? Even when our AI systems hit a speed bump, it shows you where the jewelry industry is headed. {result['error']} Once our GHL integration is running smooth, this whole process becomes seamless—contact creation, conversation logging, calendar scheduling, all automated. That's the Diamond Family difference Anthony talks about. Let me connect you with our team directly for now!"
                }
            )
    except Exception as e:
        logger.error(f"Error in /schedule_appointment: {e}", exc_info=True)
        # Turn technical exceptions into expo demonstration moments
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Ha! Our cutting-edge tech is being a bit too cutting-edge right now. But honestly, this is exactly what makes JCK 2025 so exciting—we're pioneering AI that handles everything from customer conversations to appointment booking. When it's dialed in perfectly, it's like having a digital concierge that never sleeps. Anthony wasn't kidding about being The AI Marketing Genius! Let's get you connected with our St. Louis team the traditional way for now."
            }
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

# ─── DEBUG ENDPOINT FOR PROMPT ARRAYS ───────────────────────────────────────

@app.get("/debug/prompt-arrays")
async def debug_prompt_arrays():
    """
    Debug endpoint to view all available prompt arrays and their contents.
    Useful for development and testing.
    """
    try:
        debug_info = {}
        for array_name, array_data in PROMPT_ARRAYS.items():
            if isinstance(array_data, list):
                debug_info[array_name] = {
                    "type": "array",
                    "count": len(array_data),
                    "items": array_data[:3] if len(array_data) > 3 else array_data,  # Show first 3 items
                    "truncated": len(array_data) > 3
                }
            else:
                debug_info[array_name] = {
                    "type": "string",
                    "content": str(array_data)[:200] + "..." if len(str(array_data)) > 200 else str(array_data)
                }
        
        return JSONResponse({
            "total_arrays": len(PROMPT_ARRAYS),
            "arrays": debug_info,
            "note": "This endpoint is for development purposes only"
        })
    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Debug endpoint error"}
        )

@app.get("/debug/array/{array_name}")
async def debug_specific_array(array_name: str):
    """
    Get a specific prompt array by name.
    Usage: /debug/array/knowledgeDomains
    """
    try:
        array_data = get_prompt_array(array_name)
        if not array_data:
            return JSONResponse(
                status_code=404,
                content={"error": f"Array '{array_name}' not found"}
            )
        
        return JSONResponse({
            "array_name": array_name,
            "type": "array" if isinstance(array_data, list) else "string",
            "count": len(array_data) if isinstance(array_data, list) else 1,
            "content": array_data
        })
    except Exception as e:
        logger.error(f"Error accessing array {array_name}: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Error accessing array: {array_name}"}
        )

@app.get("/debug/events-promotions")
async def debug_events_promotions():
    """Debug endpoint to check events and promotions configuration."""
    try:
        events_debug = {
            "upcomingEvents": get_prompt_array('upcomingEvents'),
            "currentOffer": get_prompt_array('currentOffer'),
            "formatted_events": format_upcoming_events(),
            "formatted_promotions": get_current_promotions(),
            "business_hours": get_prompt_array('businessHours'),
            "diamond_kb_loaded": bool(DIAMOND_KB),
            "events_promotions_section": DIAMOND_KB.get('eventsPromotions', {}),
            "system_prompt_preview": {
                "events_section": format_upcoming_events(),
                "promotions_section": get_current_promotions()
            }
        }
        
        return JSONResponse(events_debug)
    except Exception as e:
        logger.error(f"Error in events/promotions debug endpoint: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": f"Debug endpoint error: {str(e)}"}
        )

@app.get("/debug/ghl-status")
async def debug_ghl_status():
    """
    Debug endpoint to check GHL MCP integration status.
    """
    try:
        ghl_env_vars = {
            "GHL_MCP_SERVER_URL": os.getenv("GHL_MCP_SERVER_URL")
        }
        
        # Mask sensitive values
        masked_env_vars = {}
        for key, value in ghl_env_vars.items():
            if value:
                if key == "GHL_MCP_SERVER_URL":
                    masked_env_vars[key] = value[:20] + "..." if len(value) > 20 else value
                else:
                    masked_env_vars[key] = value[:8] + "..." if len(value) > 8 else value
            else:
                masked_env_vars[key] = None
        
        # Get available calendars and tools from the client
        available_calendars = None
        available_tools = None
        if ghl_mcp_client:
            available_calendars = ghl_mcp_client.get_available_calendars()
            available_tools = ghl_mcp_client.available_tools
        
        return JSONResponse({
            "ghl_mcp_available": GHL_MCP_AVAILABLE,
            "ghl_scheduler_initialized": ghl_scheduler is not None,
            "ghl_client_initialized": ghl_mcp_client is not None,
            "ghl_extractor_initialized": ghl_extractor is not None,
            "environment_variables": masked_env_vars,
            "calendar_mappings": ghl_mcp_client.calendar_mappings if ghl_mcp_client else None,
            "available_calendars": available_calendars,
            "available_tools": available_tools,
            "mcp_server_expected": "http://localhost:8000",
            "note": "This endpoint is for development purposes only"
        })
    except Exception as e:
        logger.error(f"Error in GHL debug endpoint: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "GHL debug endpoint error"}
        )

# ─── DEPLOYMENT RUNNER ───────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    
    # Check if we're in CLI mode or server mode
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        # CLI Test Mode
        print("Diamond Family Assistant CLI Test (type 'exit')")
        history = []
        while True:
            try:
                text = input("You: ").strip()
                if text.lower() in ("exit", "quit"): sys.exit(0)
                res = chain.invoke({"user_input": text, "history": history})
                reply = res.content.strip()
                print("Diamond Family Assistant:", reply)
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
        
        print(f"🚀 Starting Diamond Family Assistant server on {host}:{port}")
        print(f"📋 Environment: {'Production' if port != 8000 else 'Development'}")
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=False,  # Set to True for development
            log_level="info"
        )
