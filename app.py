"""
AI News Summarizer - Streamlit Web Application (Chat Interface)
Main entry point for the web interface with AI agent orchestration.

This version uses a ChatGPT-style interface where users can ask questions
and the agent automatically handles fetching, searching, and summarizing.

For the legacy tab-based interface, see app_legacy.py
"""

import streamlit as st
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from ui.chat_interface import render_chat_interface, render_welcome_message
from ui import render_sidebar

# Page configuration
st.set_page_config(
    page_title="AI News Assistant",
    page_icon="🤖",
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
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'orchestrator' not in st.session_state:
        from src.agent.orchestrator import NewsAgentOrchestrator
        st.session_state.orchestrator = NewsAgentOrchestrator()


def main():
    """Main application entry point."""
    # Initialize session state
    init_session_state()
    
    # Render sidebar (for system info, etc.)
    render_sidebar()
    
    # Show welcome message if chat is empty
    render_welcome_message()
    
    # Render main chat interface
    render_chat_interface()


if __name__ == "__main__":
    main()
