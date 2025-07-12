import os
import sys
import json
import base64
import logging
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import BaseMessage
from langchain.prompts import ChatPromptTemplate
from langchain.schema.messages import SystemMessage, HumanMessage, AIMessage

# ─── Logging ────────────────────────────────────────────────

logger = logging.getLogger("jewelrybox_ai")
logger.setLevel(logging.INFO)

# ─── Validate Environment ────────────────────────────────────

def validate_environment():
    required_vars = ["OPENAI_API_KEY"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"Missing environment vars: {missing}")
        sys.exit(1)

validate_environment()

# ─── Paths & Templates ───────────────────────────────────────

ROOT = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(ROOT, "templates"))

# ─── Load Prompt & KB Config ─────────────────────────────────

try:
    with open(os.path.join(ROOT, "prompts", "prompt.json"), "r") as f:
        AGENT_ROLES = json.load(f)
    system_data = AGENT_ROLES["jewelry_ai"][0]["systemPrompt"]
except:
    logger.error("prompt.json missing")
    sys.exit(1)

# Simplified standard prompt
system_prompt = f"You are {system_data['identity']}, serving as {system_data['role']}. Provide concise, helpful answers."

# ─── Image Setup ─────────────────────────────────────────────

img_path = os.path.join(ROOT, "images", "male_avatar.png")
if os.path.exists(img_path):
    with open(img_path, "rb") as img:
        IMG_URI = "data:image/png;base64," + base64.b64encode(img.read()).decode()
else:
    IMG_URI = "https://via.placeholder.com/60x60/0066cc/ffffff?text=💎"

# ─── FastAPI Setup ────────────────────────────────────────────

app = FastAPI(title="JewelryBox.AI Assistant")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── LLM + Memory ────────────────────────────────────────────

memory = InMemoryChatMessageHistory()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.9, max_tokens=1024)

prompt_template = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("placeholder", "{history}"),
    ("human", "{user_input}")
])

chain = prompt_template | llm

# ─── WebSearch (Optional) ────────────────────────────────────
try:
    from .tools.web_search_tool import WebSearchTool
    web_search = WebSearchTool()
    logger.info("WebSearchTool loaded.")
except:
    web_search = None
    logger.info("WebSearchTool unavailable.")

# ─── Pydantic Model ───────────────────────────────────────────

class ChatRequest(BaseModel):
    user_input: str
    history: list

# ─── Routes ──────────────────────────────────────────────────

@app.get("/")
async def root():
    return RedirectResponse("/widget")

@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        history = req.history or []
        user_query = req.user_input.strip()

        if web_search:
            search_results = web_search.search(user_query)
            if search_results and not search_results.startswith(("⚠️", "❌", "ℹ️", "⏱️")):
                user_query = f"[Web Search Results]\n{search_results}\n\n{user_query}"

        formatted_history = []
        for msg in history:
            if msg['role'] == 'human':
                formatted_history.append(HumanMessage(content=msg['content']))
            elif msg['role'] == 'ai':
                formatted_history.append(AIMessage(content=msg['content']))

        response = chain.invoke({"user_input": user_query, "history": formatted_history})
        reply = response.content.strip()

        memory.add_user_message(req.user_input)
        memory.add_ai_message(reply)

        return JSONResponse({
            "reply": reply,
            "history": [{"role": m.type, "content": m.content} for m in memory.messages]
        })
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": "Internal error occurred."})

@app.post("/clear_chat")
async def clear_chat():
    memory.clear()
    return JSONResponse({"status": "ok", "message": "Chat cleared"})

@app.get("/widget", response_class=HTMLResponse)
async def widget(request: Request):
    scheme = "https" if "onrender.com" in request.url.netloc else request.url.scheme
    return templates.TemplateResponse("widget.html", {
        "request": request,
        "chat_url": f"{scheme}://{request.url.netloc}/chat",
        "img_uri": IMG_URI,
    })

@app.get("/favicon.ico")
async def favicon():
    return FileResponse(os.path.join(ROOT, "images", "diamond.ico"), media_type="image/x-icon")

# ─── CLI Mode ────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    if "--cli" in sys.argv:
        print("JewelryBox CLI Mode (type 'exit')")
        cli_history = []
        while True:
            try:
                user_input = input("You: ")
                if user_input.lower() in ("exit", "quit"):
                    break
                res = chain.invoke({"user_input": user_input, "history": cli_history})
                reply = res.content.strip()
                print(f"AI: {reply}")
                memory.add_user_message(user_input)
                memory.add_ai_message(reply)
                cli_history = memory.messages
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
    else:
        uvicorn.run("src.app:app", host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", 8000)))
