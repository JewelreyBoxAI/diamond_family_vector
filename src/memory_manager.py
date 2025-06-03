import os
import json
import numpy as np
from typing import List, Tuple, Optional
import logging

# Optional FAISS imports with fallback handling
try:
    import faiss
    from langchain_community.vectorstores import FAISS
    from langchain.schema import Document
    from langchain.retrievers.document_compressors import EmbeddingsFilter
    FAISS_AVAILABLE = True
    logger = logging.getLogger("memory_manager")
    logger.info("🔍 FAISS libraries available - semantic search enabled")
except ImportError as e:
    FAISS_AVAILABLE = False
    logger = logging.getLogger("memory_manager")
    logger.warning(f"🔍 FAISS libraries not available - using basic intent matching only: {e}")
    # Create dummy classes to prevent import errors
    class FAISS: pass
    class Document: pass
    class EmbeddingsFilter: pass

from langchain_openai import OpenAIEmbeddings

# ENV setup (✅ Lazy loading - check only when needed)
def get_embeddings():
    """Get OpenAI embeddings with lazy API key validation"""
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        raise ValueError("☠️ OPENAI_API_KEY not found in environment variables")
    
    if not OPENAI_API_KEY.startswith("sk-"):
        raise ValueError("☠️ OPENAI_API_KEY appears to be invalid (should start with 'sk-')")
    
    try:
        return OpenAIEmbeddings()
    except Exception as e:
        raise ValueError(f"☠️ Failed to initialize OpenAI embeddings: {e}")

# Init Embeddings lazily
embedding_model = None

# Load intents configuration for fallback URL injection
ROOT = os.path.dirname(os.path.abspath(__file__))
intents_file = os.path.join(ROOT, "prompts", "intents.json")
try:
    with open(intents_file, "r", encoding="utf-8") as f:
        INTENTS = json.load(f)
except FileNotFoundError:
    logger.warning(f"Intents file not found at {intents_file}")
    INTENTS = {}

# ----------------------------------------------------------------------------
# LOADERS (merged logic from loaders.py)
# ----------------------------------------------------------------------------
def load_documents_from_jsonl(path: str) -> List[Document]:
    """
    Load documents from a .jsonl file. Each line should be a JSON object
    with at least 'content' and optionally 'metadata'.
    """
    docs = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            content = data.get('content')
            metadata = data.get('metadata', {})
            if content:
                docs.append(Document(page_content=content, metadata=metadata))
    return docs

# ----------------------------------------------------------------------------
# INDEX BUILDER (merged logic from index_builder.py)
# ----------------------------------------------------------------------------
def build_faiss_index(docs: List[Document], index_path: str) -> Optional[FAISS]:
    """
    Create or overwrite a FAISS index from the given documents.
    Saves index to disk at index_path.
    Returns None if FAISS is not available.
    """
    if not FAISS_AVAILABLE:
        logger.warning("Cannot build FAISS index - FAISS libraries not available")
        return None
    
    try:
        embeddings = get_embeddings()
        vectorstore = FAISS.from_documents(docs, embeddings)
        vectorstore.save_local(index_path)
        return vectorstore
    except Exception as e:
        logger.error(f"Failed to build FAISS index: {e}")
        return None

# ----------------------------------------------------------------------------
# SEMANTIC RETRIEVER WITH FALLBACKS
# ----------------------------------------------------------------------------
def load_faiss_index(index_path: str) -> Optional[FAISS]:
    """Load FAISS index with availability check."""
    if not FAISS_AVAILABLE:
        logger.debug("FAISS not available - skipping index load")
        return None
        
    try:
        embeddings = get_embeddings()
        return FAISS.load_local(index_path, embeddings)
    except Exception as e:
        logger.debug(f"Could not load FAISS index from {index_path}: {e}")
        return None

def semantic_retrieve(query: str, index_path: str, k: int = 3, threshold: float = 0.75) -> List[Tuple[str, float]]:
    """
    Perform semantic search with optional reranking and fallback filtering.
    Returns empty list if index doesn't exist (graceful fallback).
    """
    try:
        index = load_faiss_index(index_path)
        if not index:
            logger.info(f"🔍 FAISS index not found at {index_path}, using fallback intent matching")
            return []

        embeddings = get_embeddings()
        compressor = EmbeddingsFilter(embeddings=embeddings, similarity_threshold=threshold)
        retriever = index.as_retriever(search_type="similarity", search_kwargs={"k": k})
        retriever_with_filter = compressor | retriever

        results = retriever_with_filter.get_relevant_documents(query)
        return [(doc.page_content, doc.metadata.get("score", 0.0)) for doc in results]
    except Exception as e:
        logger.warning(f"Semantic search failed for {index_path}: {e}")
        return []

# ----------------------------------------------------------------------------
# ROUTING BY SUBINDEX (optional hierarchical retrieval)
# ----------------------------------------------------------------------------
def get_route_index_path(intent: str) -> str:
    intent_map = {
        "faq": "./indexes/faqs",
        "products": "./indexes/products",
        "services": "./indexes/services",
        "design": "./indexes/design"
    }
    return intent_map.get(intent, "./indexes/default")

def hierarchical_retrieve(query: str, intent: str) -> List[Tuple[str, float]]:
    index_path = get_route_index_path(intent)
    return semantic_retrieve(query, index_path)

# ----------------------------------------------------------------------------
# ENHANCED URL INJECTION WITH CONDITIONAL LOGIC & VECTOR SCORING
# ----------------------------------------------------------------------------
def get_relevant_url_enhanced(user_input: str, semantic_results: List[Tuple[str, float]] = None) -> Optional[str]:
    """
    Enhanced URL matching with conditional logic and semantic scoring.
    Returns the most relevant URL based on multi-layered analysis.
    """
    user_input_lower = user_input.lower()
    
    # Layer 1: High-confidence exact matches (priority scoring)
    high_confidence_matches = {
        "shop_diamonds": ["shop diamonds", "buy diamonds", "purchase diamonds"],
        "custom_ring": ["custom ring", "custom design", "make my own"],
        "appointment": ["schedule", "book appointment", "come in"]
    }
    
    for intent_key, exact_phrases in high_confidence_matches.items():
        for phrase in exact_phrases:
            if phrase in user_input_lower:
                if intent_key in INTENTS:
                    logger.info(f"🎯 High-confidence match: {intent_key} for '{phrase}'")
                    return INTENTS[intent_key]['url']
    
    # Layer 2: Semantic similarity with context scoring
    if semantic_results:
        for content, score in semantic_results:
            if score > 0.85:  # High semantic confidence
                # Extract intent from high-scoring semantic results
                content_lower = content.lower()
                for intent_key, intent_data in INTENTS.items():
                    for synonym in intent_data["synonyms"]:
                        if synonym in content_lower:
                            logger.info(f"🧠 Semantic match: {intent_key} (score: {score:.2f})")
                            return intent_data['url']
    
    # Layer 3: Fallback to original intent matching
    for intent_key, intent_data in INTENTS.items():
        for synonym in intent_data["synonyms"]:
            if synonym in user_input_lower:
                logger.info(f"📋 Standard match: {intent_key} for '{synonym}'")
                return intent_data['url']
    
    return None

def get_contextual_intent(user_input: str, conversation_history: List = None) -> str:
    """
    Determine user intent with conversation context analysis.
    Returns intent classification for routing to specific vector indexes.
    """
    user_input_lower = user_input.lower()
    
    # Intent classification with weighted keywords
    intent_keywords = {
        "products": {
            "keywords": ["diamond", "ring", "necklace", "earring", "bracelet", "watch", "jewelry"],
            "weight": 2.0
        },
        "services": {
            "keywords": ["repair", "appraisal", "custom", "restring", "battery", "fix"],
            "weight": 2.5
        },
        "education": {
            "keywords": ["learn", "guide", "4 cs", "cut", "clarity", "color", "carat"],
            "weight": 1.5
        },
        "commercial": {
            "keywords": ["buy", "shop", "purchase", "price", "cost", "budget"],
            "weight": 3.0
        }
    }
    
    intent_scores = {}
    for intent, data in intent_keywords.items():
        score = 0
        for keyword in data["keywords"]:
            if keyword in user_input_lower:
                score += data["weight"]
        intent_scores[intent] = score
    
    # Return highest scoring intent or default
    if intent_scores:
        best_intent = max(intent_scores, key=intent_scores.get)
        if intent_scores[best_intent] > 0:
            logger.info(f"🎯 Intent classified: {best_intent} (score: {intent_scores[best_intent]})")
            return best_intent
    
    return "general"

def inject_fallback_if_needed(user_input: str, response: str, semantic_results: List[Tuple[str, float]] = None) -> str:
    """
    Enhanced URL injection with conditional logic and semantic analysis.
    Ensures only ONE URL is injected per message with confidence scoring.
    """
    # Enhanced URL matching with semantic results
    url = get_relevant_url_enhanced(user_input, semantic_results)
    if url:
        return response + f"\n\n🔗 You can explore that here: {url}"
    
    # No match found
    return response

def smart_semantic_retrieve(query: str, k: int = 5, confidence_threshold: float = 0.7) -> List[Tuple[str, float]]:
    """
    Smart semantic retrieval with intent-based index routing and confidence filtering.
    Returns results only above confidence threshold with intent classification.
    Gracefully handles missing indexes.
    """
    try:
        # Classify intent to route to appropriate index
        intent = get_contextual_intent(query)
        index_path = get_route_index_path(intent)
        
        # Perform semantic search
        results = semantic_retrieve(query, index_path, k=k, threshold=confidence_threshold)
        
        # If no high-confidence results, try broader search on default index
        if not results or (results and max(score for _, score in results) < 0.8):
            logger.info(f"🔄 Fallback search on default index for: {query}")
            fallback_results = semantic_retrieve(query, "./indexes/default", k=k//2, threshold=0.6)
            results.extend(fallback_results)
        
        # Sort by confidence and return top results
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]
    except Exception as e:
        logger.warning(f"Smart semantic search failed: {e}")
        return []

# ----------------------------------------------------------------------------
# DEBUG / TEST DRIVER
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    index_path = "./indexes/products"
    query = "custom lab diamond engagement ring"
    results = semantic_retrieve(query, index_path)

    print("\n💎 Top Matches:")
    for content, score in results:
        print(f"- ({score:.2f}) {content[:100]}...")
    
    # Test URL injection
    test_query = "I want to see diamonds"
    test_response = "Here are some diamond options for you."
    final_response = inject_fallback_if_needed(test_query, test_response)
    print(f"\n🔗 URL Injection Test:\nInput: {test_query}\nOutput: {final_response}")

def inject_relevant_url(user_input: str, response: str) -> str:
    """
    Legacy compatibility function - redirects to enhanced injection.
    Maintains backward compatibility with existing app.py integration.
    """
    return inject_fallback_if_needed(user_input, response)

def inject_relevant_url_with_semantics(user_input: str, response: str, perform_semantic_search: bool = True) -> str:
    """
    Enhanced URL injection that performs semantic search for better accuracy.
    This is the recommended function for new implementations.
    Gracefully falls back to basic intent matching if semantic search fails.
    """
    semantic_results = None
    
    if perform_semantic_search:
        try:
            # Perform smart semantic retrieval
            semantic_results = smart_semantic_retrieve(user_input, k=3, confidence_threshold=0.75)
            if semantic_results:
                logger.info(f"🔍 Semantic search found {len(semantic_results)} results for: '{user_input}'")
            else:
                logger.info(f"🔍 No semantic results found, using fallback intent matching for: '{user_input}'")
        except Exception as e:
            logger.warning(f"Semantic search failed, using fallback: {e}")
            semantic_results = None
    
    return inject_fallback_if_needed(user_input, response, semantic_results)

# ----------------------------------------------------------------------------
# LEGACY SUPPORT
# ----------------------------------------------------------------------------
def get_relevant_url(user_input: str) -> Optional[str]:
    """
    Legacy function for backward compatibility.
    Redirects to enhanced URL matching without semantic results.
    """
    return get_relevant_url_enhanced(user_input) 