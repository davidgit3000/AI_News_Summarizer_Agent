"""
Sidebar component for the AI News Summarizer application.
"""

import streamlit as st
from src.database.db_manager import DatabaseManager
from config import get_settings


def check_api_keys():
    """Check if required API keys are configured."""
    settings = get_settings()
    
    keys_status = {
        'OpenAI': bool(settings.openai_api_key),
        'NewsAPI': bool(settings.newsapi_key),
        'Gemini': bool(settings.gemini_api_key)
    }
    
    return keys_status


def render_sidebar():
    st.sidebar.title("⚙️ Configuration")
    
    # Statistics - Get actual count from database
    st.sidebar.subheader("📊 Statistics")
    try:
        from src.database.db_manager import DatabaseManager
        db = DatabaseManager()
        stats = db.get_stats()
        article_count = stats['total_articles']
    except:
        article_count = 0
    st.sidebar.metric("Articles Ingested", article_count)

    st.sidebar.markdown("---")
    
    # API Keys Status
    st.sidebar.subheader("API Keys Status")
    keys_status = check_api_keys()
    
    for key_name, is_configured in keys_status.items():
        if is_configured:
            st.sidebar.success(f"✅ {key_name}")
        else:
            st.sidebar.error(f"❌ {key_name}")
    
    if not all(keys_status.values()):
        st.sidebar.warning("⚠️ Some API keys are missing. Check your .env file.")
    
    st.sidebar.markdown("---")
    
    # Settings
    st.sidebar.subheader("Settings")
    
    settings = get_settings()
    
    # LLM Settings
    with st.sidebar.expander("🤖 LLM Settings"):
        st.write(f"**Model:** {settings.llm_model}")
        st.write(f"**Temperature:** {settings.llm_temperature}")
        st.write(f"**Max Tokens:** {settings.llm_max_tokens}")
    
    # Retrieval Settings
    with st.sidebar.expander("🔍 Retrieval Settings"):
        st.write(f"**Top K Results:** {settings.top_k_results}")
        st.write(f"**Similarity Threshold:** {settings.similarity_threshold}")
    
    # Vector Store Settings
    with st.sidebar.expander("💾 Vector Store"):
        st.write(f"**Type:** {settings.vector_store_type}")
        st.write(f"**Path:** {settings.vector_store_path}")
    
    st.sidebar.markdown("---")
    
    # About
    with st.sidebar.expander("ℹ️ About"):
        st.write("""
        **AI News Summarizer Agent**
        
        A RAG-based system for intelligent news summarization.
        
        **Features:**
        - News ingestion from NewsAPI
        - Vector-based retrieval
        - LLM-powered summarization
        - Quality validation
        - Fidelity checking
        
        **Tech Stack:**
        - OpenAI GPT
        - Google Gemini
        - ChromaDB
        - Sentence Transformers
        """)
