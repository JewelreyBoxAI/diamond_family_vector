# JewelryBoxAI Architecture

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

## Architectural Decisions

### 1. Dual-Layer Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Web Layer                        │
├─────────────────────────────────────────────────────────────┤
│  Widget Endpoint  │  Chat API  │  Static Assets  │  Health │
├─────────────────────────────────────────────────────────────┤
│                   AI Processing Layer                       │
├─────────────────────────────────────────────────────────────┤
│  LangChain Chain  │  Memory Manager  │  Intent Matching    │
├─────────────────────────────────────────────────────────────┤
│                   Optional Search Layer                     │
├─────────────────────────────────────────────────────────────┤
│  FAISS Indexes   │  Semantic Search  │  Fallback Routing  │
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

## File Structure

```
src/
├── app.py                 # Main FastAPI application
├── memory_manager.py      # Semantic search and URL injection
├── __init__.py           # Package initialization
├── templates/
│   └── widget.html       # Chat interface template
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
OPENAI_API_KEY=required    # Primary LLM access
ALLOWED_ORIGINS=optional   # CORS configuration (default: *)
PORT=optional             # Server port (default: 8000)
HOST=optional             # Server host (default: 0.0.0.0)
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
docker build -t jewelrybox-ai .
docker run -p 8000:8000 --env-file .env jewelrybox-ai
```

### Cloud Deployment
- **Render.com**: Automatic Docker deployment
- **Environment**: Variables configured in platform
- **Health Check**: Built-in FastAPI health endpoint
- **HTTPS**: Automatic SSL termination

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