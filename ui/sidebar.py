"""
Sidebar component for the AI News Summarizer application.
"""

import streamlit as st
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


# @st.cache_data(ttl=2000, show_spinner=False)  # Cache for 60 seconds, hide default spinner
# def get_article_count():
#     """Get article count from database with caching."""
#     try:
#         db = get_database_manager()
#         stats = db.get_stats()
#         return stats['total_articles'], None
#     except Exception as e:
#         return 0, str(e)


def get_selected_model():
    """Get the currently selected LLM model from session state."""
    return st.session_state.get('llm_model', 'gpt-3.5-turbo')


def render_sidebar():
    st.sidebar.title("⚙️ Configuration")
    
    # Statistics - Get actual count from database
    # st.sidebar.subheader("📊 Statistics")
    
    # # Show loading message
    # with st.sidebar:
    #     with st.spinner("🔄 Connecting to database..."):
    #         article_count, error = get_article_count()
    
    # if error:
    #     st.sidebar.error(f"Database error: {error}")
    #     st.sidebar.metric("Articles Ingested", 0)
    # else:
    #     st.sidebar.metric("Articles Ingested", article_count)
    
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
        # Model selection
        model_options = ["gpt-3.5-turbo", "gpt-4.1", "gpt-4.1-mini"]
        current_model = settings.llm_model if settings.llm_model in model_options else "gpt-3.5-turbo"
        
        selected_model = st.selectbox(
            "Model",
            options=model_options,
            index=model_options.index(current_model),
            help="Select the OpenAI model to use. GPT-4.1 models are newer and more capable but more expensive."
        )
        
        # Store in session state for use across the app
        st.session_state.llm_model = selected_model
        
        st.write(f"**Temperature:** {settings.llm_temperature}")
        st.write(f"**Max Tokens:** {settings.llm_max_tokens}")
    
    # Retrieval Settings
    with st.sidebar.expander("🔍 Retrieval Settings", expanded=True):
        top_k = st.slider(
            "Top K Results",
            min_value=1,
            max_value=20,
            value=settings.top_k_results,
            help="Maximum number of articles to retrieve"
        )
        
        similarity = st.slider(
            "Similarity Threshold",
            min_value=0.0,
            max_value=1.0,
            value=settings.similarity_threshold,
            step=0.05,
            help="Minimum similarity score (0-1) for relevance"
        )
        
        # Store in session state for use across tabs
        st.session_state.top_k_results = top_k
        st.session_state.similarity_threshold = similarity
    
    # Vector Store Settings
    with st.sidebar.expander("💾 Vector Store"):
        st.write(f"**Type:** {settings.vector_store_type}")
        # st.write(f"**Path:** {settings.vector_store_path}")
    
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
        - Python
        - Streamlit
        - Sentence Transformers
        - OpenAI
        - Google Gemini
        - Pinecone
        - NeonDB
        """)
