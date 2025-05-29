# 🧠 JewelryBox AI: SaaS-Capable Smart Concierge for Jewelry Retailers

## 🚀 What It Is

JewelryBox AI is a **modular AI chatbot assistant** engineered specifically for high-end jewelry retailers. Built on a scalable, multi-layer architecture using **FAISS vector search**, **semantic retrieval**, and **contextual prompt injection**, it delivers precise, URL-linked responses to real customer queries—across product discovery, education, services, and promotions.

This isn’t just a chatbot—it's an **AI concierge that mimics real staff behavior**, understands intent, and responds with tailored, resource-linked answers using natural language processing.

---

## ⚙️ How It Works (Under the Hood)

### 1. Memory & Query Handling

* Uses a **custom `memory_manager.py` module** to centralize all vector-based semantic search.
* Incoming user input is parsed and embedded via OpenAI or a compatible model.
* Matched against **FAISS** indexes categorized by:

  * `products` (diamond types, rings, designers)
  * `services` (repairs, custom work, appraisals)
  * `intents` (scheduling, promos, support)

### 2. Smart Retrieval & Response Generation

* Retrieves the **most semantically relevant** knowledge base entry.
* Injects the **matching URL directly**, using fallback logic if the query is vague or ambiguous.
* Always limits to **one authoritative URL per response**, cutting hallucinations by design.

### 3. Extensible Intent Mapping

* Trigger words and synonyms are **mapped to intents** like `shopping_for_diamonds`, `book_appointment`, or `custom_design`.
* Hierarchical intent recognition routes queries to the right FAISS sub-index and returns **contextually relevant, business-linked answers**.

---

## 🧱 Why It Was Built This Way

* **Retail Staff Are Overloaded:** This AI handles 70%+ of incoming website and mobile inquiries (based on pilot data).
* **Reduces Bounce Rate:** Direct answers = less confusion = lower bounce rates.
* **Saves Sales Time:** Filters high-intent leads (custom ring requests, service booking) from low-intent browsers.
* **White-Label Ready:** Fully repurposeable for **other verticals**—medical spas, automotive sales, real estate, or luxury watches.

---

## 🔁 How It Can Be Repurposed / Sold as SaaS

### 1. Vertical Adaptability

* Swap in a new knowledge base and vector index (e.g., `real_estate_docs`, `cosmetic_services`, etc.)
* Update system prompt and tone (e.g., from "concierge" to "advisor" or "receptionist")

### 2. Plug-and-Play Deployment

* Installable on any site via `<script>` widget
* Hosted backend (e.g., FastAPI, LangServe) with cloud-deployed memory index

### 3. Multi-Tenant Design

* FAISS + retriever logic can be **isolated per client**
* Supports RAG pipelines, API rate limiting, and optional logging hooks for analytics

### 4. Licensing Models

* White-label it to agencies
* Charge monthly per client usage
* Upsell long-term memory, custom prompt tuning, or domain-trained embedding

---

## 🧰 What It’s Capable Of

* ✅ Product discovery with direct linking (Diamonds, Designers, Rings)
* ✅ Services FAQ and routing (Watch Repair, Appraisals, Resizing)
* ✅ Lead capture and appointment setting
* ✅ Promotions & contest handling (Instagram giveaways, seasonal discounts)
* ✅ Smart fallback handling when queries are vague
* ✅ Upgrade-ready to include image-gen or voice agents (LiveKit, VAPI, etc.)

---

## 📈 Why It Wins in the Market

* **Precision, not bloat:** One URL per query, no guesswork
* **Zero hallucination design:** Built from the ground up to return what exists—not what sounds plausible
* **Cross-domain reskinning:** Swap vector DB + prompts = New vertical, no rebuild
* **Memory centralization:** Every call routes through `memory_manager.py`—clean, trackable, and scalable
* **Built by engineers for engineers:** No dependency hell, modular by design, compliant with Rick's Law (If it’s not bulletproof, it doesn’t ship.)

---

## 💼 Use Cases

| Industry     | AI Role               | Example Outcome                     |
| ------------ | --------------------- | ----------------------------------- |
| Jewelry      | Concierge             | Links to ring collections, booking  |
| Med Spa      | AI Receptionist       | Routes botox vs. filler questions   |
| Real Estate  | Lead Qualifier        | Matches listings and books tours    |
| Automotive   | Sales Funnel Agent    | Explains trims, books test drives   |
| Fine Watches | Product Specialist    | Filters by brand/style, sends links |
| E-Commerce   | FAQ / Returns Handler | Pulls exact policy links            |

---

> Want to clone this stack for your industry? Swap out the vector index, rewrite the prompt, and deploy. Done.




## Quick Start (Docker - Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd JewelryBoxAI_Bot
   ```

2. **Create environment file**
   ```bash
   # Create .env file with your OpenAI API key
   echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
   echo "ALLOWED_ORIGINS=*" >> .env
   ```

3. **Deploy with Docker**
   
   **For Windows (PowerShell):**
   ```powershell
   .\deploy.ps1
   ```
   
   **For Linux/Mac:**
   ```bash
   ./deploy.sh
   ```
   
   **Or manually:**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Main app: http://localhost:8000
   - Chat widget: http://localhost:8000/widget

## Alternative: Local Development Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Set up your OpenAI API key in environment variables
3. Run the application: `uvicorn src.app:app --reload`
4. Visit `/widget` to interact with the chatbot

## Configuration

Create a `.env` file with your API keys:
```
OPENAI_API_KEY=your_openai_api_key_here
ALLOWED_ORIGINS=*
```

## Docker Commands

- **Start**: `docker-compose up -d`
- **Stop**: `docker-compose down`
- **View logs**: `docker-compose logs -f`
- **Rebuild**: `docker-compose up -d --build`

## Deployment

This application is containerized and ready for deployment on any Docker-compatible platform including:
- Local Docker
- AWS ECS/Fargate
- Google Cloud Run
- Azure Container Instances
- DigitalOcean App Platform

---

*Built for luxury jewelry retailers who want to provide exceptional customer service through AI technology.*
