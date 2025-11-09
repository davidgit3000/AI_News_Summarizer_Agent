"""
AI News Summarizer - Streamlit Web Application (Modular Version)
Main entry point for the web interface with modularized UI components.
"""

import streamlit as st
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from ui import (
    render_sidebar,
    render_ingestion_tab,
    render_summarization_tab,
    render_analytics_tab,
    render_search_tab
)

# Page configuration
st.set_page_config(
    page_title="AI News Summarizer",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if 'ingestion_pipeline' not in st.session_state:
        st.session_state.ingestion_pipeline = None
    if 'summarization_pipeline' not in st.session_state:
        st.session_state.summarization_pipeline = None
    if 'validation_pipeline' not in st.session_state:
        st.session_state.validation_pipeline = None
    if 'vectorization_pipeline' not in st.session_state:
        st.session_state.vectorization_pipeline = None
    if 'retrieval_pipeline' not in st.session_state:
        st.session_state.retrieval_pipeline = None
    if 'last_summary' not in st.session_state:
        st.session_state.last_summary = None
    if 'last_ingestion_stats' not in st.session_state:
        st.session_state.last_ingestion_stats = None


def main():
    """Main application entry point."""
    # Initialize session state
    init_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Main header
    st.markdown('<h1 class="main-header">📰 AI News Summarizer</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Intelligent news aggregation and summarization powered by RAG and LLMs</p>', unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📥 Ingest",
        "🔍 Search",
        "📝 Summarize and Validate",
        "📊 Stats"
    ])
    
    # Render each tab
    with tab1:
        render_ingestion_tab()
    
    with tab2:
        render_search_tab()
    
    with tab3:
        render_summarization_tab()
    
    with tab4:
        render_analytics_tab()


if __name__ == "__main__":
    main()
