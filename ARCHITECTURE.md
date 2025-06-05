# Diamond Family Assistant Architecture

**Diamond Family Assistant** transforms jewelry retail through intelligent AI conversation, family business warmth, and cutting-edge technology. At JCK Las Vegas 2025, it serves as Anthony Haddad's digital wingman—The AI Marketing Genius's secret weapon for industry networking and innovation demonstration.

## Technology Stack

### Core Framework
- **FastAPI** 0.104.1+ - Web framework with automatic API documentation
- **Python** 3.8+ - Runtime environment
- **Uvicorn** 0.24.0+ - ASGI server for production

### AI & Language Processing
- **LangChain** 0.0.350+ - LLM orchestration and prompt management
- **OpenAI API** (GPT-4o-mini) - Core language model for responses
- **OpenAI Embeddings** - Semantic search capabilities (optional)

### Vector Search (Optional)
- **FAISS** 1.7.0+ - Semantic similarity search
- **NumPy** 1.24.0+ - Numerical operations for embeddings
- **LangChain Community** - FAISS integration

### Frontend & Templates
- **Jinja2** 3.1.2+ - HTML templating engine
- **Custom HTML/CSS/JS** - Chat widget interface

### Configuration & Environment
- **python-dotenv** 1.0.0+ - Environment variable management
- **Base64 encoding** - Avatar image embedding

### GoHighLevel Integration
- **aiohttp** 3.9.0+ - HTTP client for MCP server communication
- **GHL MCP Server** - External appointment scheduling service
- **Async scheduling** - Non-blocking appointment creation

## Architectural Decisions

### 1. Dual-Layer Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Web Layer                        │
├─────────────────────────────────────────────────────────────┤
│  Widget  │  Chat API  │  Scheduling  │  Static  │  Health  │
├─────────────────────────────────────────────────────────────┤
│                   AI Processing Layer                       │
├─────────────────────────────────────────────────────────────┤
│  LangChain Chain  │  Memory Manager  │  Intent Matching    │
├─────────────────────────────────────────────────────────────┤
│                 Integration Layer                           │
├─────────────────────────────────────────────────────────────┤
│  FAISS Search  │  Web Search  │  GHL MCP Client  │  URLs   │
└─────────────────────────────────────────────────────────────┘
```

### 2. Memory Management Strategy
- **InMemoryChatMessageHistory**: Server-side conversation storage
- **LocalStorage**: Client-side persistence for user experience
- **Global Memory**: Single conversation thread (suitable for single-user demo)

### 3. Intent Recognition System
- **Primary**: FAISS semantic search with confidence thresholds
- **Fallback**: Pattern-based intent matching using `intents.json`
- **URL Injection**: Automatic relevant link insertion based on user queries

### 4. Graceful Degradation Pattern
- FAISS semantic search is optional - app works without it
- Environment validation prevents runtime crashes
- Error boundaries with user-friendly messages
- Fallback images and default configurations

### 5. Expo Wingman Intelligence
- **Contextual Awareness**: Real-time understanding of JCK Las Vegas 2025 environment
- **Industry Networking**: Strategic conversation facilitation and relationship building
- **Error Transformation**: Converts technical issues into demonstration opportunities
- **Humor Integration**: Perfectly-timed industry jokes and networking conversation starters

## File Structure

```
src/
├── app.py                 # Main FastAPI application
├── memory_manager.py      # Semantic search and URL injection
├── __init__.py           # Package initialization
├── tools/
│   ├── ghl_mcp_client.py     # GoHighLevel MCP integration
│   ├── web_search_tool.py    # Web search functionality
│   └── test_ghl_integration.py # GHL integration tests
├── templates/
│   └── widget.html       # Chat interface with appointment scheduling
├── images/
│   ├── diamond.ico       # Favicon
│   ├── male_avatar.png   # Bot avatar (base64 encoded)
│   └── README.md         # Image documentation
└── prompts/
    ├── prompt.json       # LLM system prompts and personality
    ├── diamond_family_kb.json  # Business knowledge base
    └── intents.json      # URL mapping for intent recognition

indexes/                  # Optional FAISS semantic search
├── default/             # General query index
├── faqs/               # FAQ-specific index
├── products/           # Product-related index
├── services/           # Service-specific index
├── design/             # Design consultation index
└── README.md           # Index documentation

Root Files:
├── requirements.txt     # Python dependencies
├── Dockerfile          # Production container
├── docker-compose.yml  # Development orchestration
├── .env               # Environment configuration (local)
└── .gitignore         # Repository cleanliness rules
```

## Integration Points

### 1. OpenAI API
- **Models Used**: gpt-4o-mini (cost-optimized)
- **Max Tokens**: 1024 (balanced response length)
- **Temperature**: 0.9 (creative but controlled)
- **API Key Validation**: Startup validation with helpful error messages

### 2. External URLs (intents.json)
- **Diamond Shopping**: https://www.thediamondfamily.com/diamonds/
- **Custom Design**: https://www.thediamondfamily.com/services/custom-design/
- **Appointments**: https://www.thediamondfamily.com/appointments/
- **Reviews**: Google Business Profile link

### 3. Environment Variables
```bash
# Required
OPENAI_API_KEY=required    # Primary LLM access

# Optional Web Configuration  
ALLOWED_ORIGINS=optional   # CORS configuration (default: *)
PORT=optional             # Server port (default: 8000)
HOST=optional             # Server host (default: 0.0.0.0)

# Optional GoHighLevel Integration
GHL_MCP_SERVER_URL=optional        # GHL MCP server endpoint
GHL_DEFAULT_CALENDAR_ID=optional   # Default appointment calendar
GHL_CALENDAR_JEWELLER_ID=optional  # Jewelry appointments
GHL_CALENDAR_AUDIT_ID=optional     # Appraisal appointments
GHL_CALENDAR_BOOKCALL_ID=optional  # Consultation appointments
```

## Design Patterns

### 1. Chain of Responsibility
LangChain implements prompt → LLM → memory → URL injection pipeline

### 2. Strategy Pattern  
Memory manager uses semantic search OR intent matching based on availability

### 3. Template Method
Widget rendering uses consistent template pattern with dynamic URL generation

### 4. Singleton Pattern
Global memory and LLM instances for demo simplicity

## Security Considerations

### 1. Input Validation
- FastAPI Pydantic models validate all API inputs
- XSS prevention through template escaping
- CORS configuration for cross-origin requests

### 2. API Key Management
- Environment variable storage only
- Startup validation prevents runtime exposure
- No API keys in logs or error messages

### 3. Content Security
- Base64 image embedding prevents external requests
- Hardcoded business URLs prevent injection attacks
- Rate limiting handled by OpenAI API

## Expo Wingman Features

### 1. JCK Las Vegas 2025 Intelligence
- **Event Context**: June 6-9, 2025 at The Venetian Expo
- **Anthony's Role**: CEO of JewelryBox AI & The AI Marketing Genius
- **Mission**: Demonstrate AI innovation while building industry relationships

### 2. Contextual Networking
- **Exhibitor Recognition**: Identifies mentions of Grown Diamond Corporation, MID House of Diamonds
- **Conversation Bridging**: Connects expo discussions to Diamond Family services
- **Follow-up Coordination**: Schedules meetings around expo activities
- **Relationship Mapping**: Maintains context from expo conversations

### 3. Error Handling as Demo Strategy
```python
# Technical errors become networking opportunities
"Perfect timing! This is exactly why we're pioneering AI in jewelry—
imagine when this connection is live, I could create your contact record, 
add our conversation notes, and schedule your follow-up visit to St. Louis 
all while we're talking. That's the future Diamond Family is building."
```

### 4. Industry Humor Integration
- **Diamond Clarity Jokes**: Context-appropriate grading humor
- **Carat Weight References**: Networking conversation enhancers  
- **Setting Puns**: "Setting" appointments and relationships
- **Booth Traffic Observations**: Expo environment awareness

### 5. Strategic AI Demonstration
- **Live Innovation Showcase**: Real-time AI capabilities during conversations
- **Future Vision Communication**: Explains seamless AI-powered customer experiences
- **Technology Leadership**: Positions Diamond Family as industry innovators
- **Competitive Differentiation**: Highlights unique AI integration approach

## Performance Characteristics

### 1. Response Times
- **Cold Start**: ~2-3 seconds (LLM + prompt processing)
- **Warm Requests**: ~1-2 seconds (cached model)
- **Semantic Search**: +200-500ms (if FAISS enabled)

### 2. Memory Usage
- **Base Application**: ~50-100MB
- **With FAISS**: +100-200MB (depending on index size)
- **Per Conversation**: ~1-5KB (message history)

### 3. Scalability Notes
- Single-user memory design (global state)
- Stateless API endpoints (horizontally scalable)
- FAISS indexes loaded once at startup

## Deployment Architecture

### Development
```bash
docker-compose up -d  # Local development with hot reload
```

### Production
```bash
docker build -t diamond-family-assistant .
docker run -p 8000:8000 --env-file .env diamond-family-assistant
```

### Cloud Deployment
- **Render.com**: Automatic Docker deployment
- **Environment**: Variables configured in platform
- **Health Check**: Built-in FastAPI health endpoint
- **HTTPS**: Automatic SSL termination

## GoHighLevel MCP Integration

### Appointment Scheduling Architecture
The system integrates with a GoHighLevel MCP (Model Context Protocol) server to automatically create contacts and schedule appointments.

```
┌─────────────────────────────────────────────────────────────┐
│                 Diamond Family Assistant                    │
├─────────────────────────────────────────────────────────────┤
│  1. Customer expresses appointment interest                 │
│  2. AI detects appointment intent + extracts contact info  │
│  3. Frontend shows appointment form (auto-filled)          │
│  4. Customer confirms/completes missing details            │
├─────────────────────────────────────────────────────────────┤
│                    GHL MCP Client                          │
├─────────────────────────────────────────────────────────────┤
│  • HTTP client to GHL MCP server                          │
│  • Calendar selection logic (jewelry/audit/consultation)   │
│  • Contact info extraction & validation                    │
│  • Conversation summary generation                         │
├─────────────────────────────────────────────────────────────┤
│                  GHL MCP Server                            │
├─────────────────────────────────────────────────────────────┤
│  • Creates contact in GoHighLevel                         │
│  • Adds conversation notes to contact                      │
│  • Schedules appointment on appropriate calendar           │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. GHLMCPClient (`src/tools/ghl_mcp_client.py`)
- **Purpose**: HTTP client for communicating with GHL MCP server
- **Features**: 
  - Async HTTP requests with timeout handling
  - Calendar selection based on conversation context
  - Appointment time suggestion logic
  - Error handling and retry logic

#### 2. CustomerInfoExtractor
- **Purpose**: Extract customer contact information from conversations
- **Features**:
  - Regex-based email/phone extraction
  - Conversation summary generation
  - Name detection (manual input required)

#### 3. GHLAppointmentScheduler
- **Purpose**: High-level scheduling interface
- **Features**:
  - Validates required customer information
  - Selects appropriate calendar based on appointment type
  - Generates conversation summaries for GHL notes
  - Handles scheduling errors gracefully

### Calendar Selection Logic
- **Jewelry Calendar**: Engagement rings, custom design, jewelry purchases
- **Audit Calendar**: Appraisals, evaluations, assessments
- **Consultation Calendar**: Design consultations, general meetings
- **Default Calendar**: Fallback for unmatched conversation types

### Frontend Integration
The chat widget automatically:
1. Detects appointment requests in conversation
2. Shows appointment scheduling form when appropriate  
3. Pre-fills extracted contact information
4. Provides real-time scheduling feedback
5. Confirms successful appointment creation

### Error Handling
- **MCP Server Unavailable**: Graceful degradation with manual contact instructions
- **Invalid Contact Data**: Clear validation messages for missing fields
- **Calendar Conflicts**: Server-side handling with alternative time suggestions
- **Network Issues**: Timeout handling with retry options

## Extension Points

### 1. Multi-Tenant Support
- Modify memory manager for user-specific conversations
- Add authentication middleware
- Separate FAISS indexes per client

### 2. Voice Integration
- Add speech-to-text endpoint
- Integrate text-to-speech response
- WebRTC for real-time voice chat

### 3. Analytics Integration
- Add conversation logging
- User interaction tracking  
- Performance monitoring

### 4. Advanced AI Features
- Image recognition for jewelry uploads
- Recommendation engine based on conversation history
- Automated appointment scheduling integration 