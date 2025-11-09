"""
Summarization tab component for generating news summaries.
Refactored to use modular components for better maintainability.
"""

import streamlit as st
from ui.summarization import render_standard_summary, render_qa_summary


def render_summarization_tab():
    """Render the news summarization tab."""
    st.header("📝 News Summarization")
    st.write("Generate intelligent summaries using RAG and LLMs")
    
    # Create sub-tabs for different summarization modes
    subtab1, subtab2 = st.tabs(["📄 Standard Summary", "❓ Q&A Summary"])
    
    # Standard Summary Tab
    with subtab1:
        render_standard_summary()
    
    # Q&A Summary Tab
    with subtab2:
        render_qa_summary()
