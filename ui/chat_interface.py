"""
Chat Interface - ChatGPT-style UI for the News Summarizer Agent.

This provides a conversational interface where users can ask questions
and the agent automatically handles fetching, searching, and summarizing.
"""

import streamlit as st
from datetime import datetime
import re
from src.agent.orchestrator import NewsAgentOrchestrator
from src.validation.pipeline import ValidationPipeline
from ui.components.validation_display import render_validation_results


# def sanitize_text(text: str) -> str:
#     """
#     Sanitize text to prevent unwanted markdown formatting.
    
#     Removes or escapes characters that cause rendering issues:
#     - Stray underscores that create italics
#     - Multiple asterisks that create bold/italic
#     - Other markdown artifacts
    
#     Args:
#         text: Raw text that may contain markdown artifacts
    
#     Returns:
#         Cleaned text safe for display
#     """
#     if not text:
#         return text
    
#     # Replace problematic patterns that create unintended formatting
#     # Pattern 1: Single underscores in the middle of words (creates italics)
#     text = re.sub(r'(\w)_(\w)', r'\1\\_\2', text)
    
#     # Pattern 2: Multiple underscores or asterisks (creates bold/italic)
#     text = re.sub(r'_{2,}', lambda m: '\\' + m.group(0), text)
#     text = re.sub(r'\*{2,}', lambda m: '\\' + m.group(0), text)
    
#     # Pattern 3: Stray single underscores at word boundaries
#     text = re.sub(r'(?<!\w)_(?=\w)|(?<=\w)_(?!\w)', '\\_', text)
    
#     return text


def render_chat_interface():
    """Render the main chat interface."""
    
    # Header
    st.title("🤖 Let's chat with Nunu AI!")
    st.caption("Ask me anything about recent news - I'll find, analyze, and summarize for you!")
    
    # Settings in sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        max_articles = st.slider(
            "Max Articles",
            min_value=3,
            max_value=15,
            value=8,
            help="Maximum number of articles to use for summary"
        )
        
        summary_length = st.slider(
            "Summary Length (words)",
            min_value=100,
            max_value=500,
            value=250,
            help="Target length for the summary"
        )
        
        style = st.selectbox(
            "Summary Style",
            [
                "concise",
                "comprehensive",
                "bullet_points",
                "executive",
                "technical",
                "eli5"
            ],
            help="Choose the style of summary"
        )
        
        st.divider()
        
        # Validation settings
        st.subheader("📊 Validation")
        run_fidelity = st.checkbox(
            "🔍 Run Fidelity Check (Gemini)",
            value=False,
            help="Enable LLM-based fidelity checking (uses Gemini API)"
        )
        
        st.divider()
        
        # Clear chat button
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        st.divider()
        
        # Example queries
        with st.expander("💡 Example Queries"):
            st.markdown("""
            **Technology:**
            - "What's new with AI and machine learning?"
            - "Tell me about recent developments in quantum computing"
            
            **Business:**
            - "Latest news on cryptocurrency markets"
            - "What's happening with electric vehicles?"
            
            **Science:**
            - "Recent breakthroughs in climate science"
            - "News about space exploration"
            
            **General:**
            - "What are the top tech stories today?"
            - "Summarize recent AI ethics discussions"
            """)
    
    # Initialize chat history (should already be done in app.py)
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Orchestrator should already be initialized in app.py
    # Just verify it exists
    if 'orchestrator' not in st.session_state or st.session_state.orchestrator is None:
        st.error("⚠️ Orchestrator not initialized. Please refresh the page.")
        return
    
    # Display chat history
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message['role']):
            # Display message content with proper formatting
            st.write(message['content'])
            
            # Display sources if available
            if message.get('sources'):
                with st.expander(f"📚 Sources ({len(message['sources'])} articles)"):
                    for i, source in enumerate(message['sources'], 1):
                        # Get relevance score if available
                        relevance = source.get('similarity', 0)
                        relevance_pct = f"{relevance * 100:.1f}%" if relevance > 0 else "N/A"
                        
                        st.markdown(f"""
                        **{i}. {source.get('title', 'Untitled')}**
                        - 📰 Source: {source.get('source', 'Unknown')}
                        - 📅 Published: {source.get('published_at', 'Unknown')}
                        - 🎯 Relevance: {relevance_pct}
                        - 🔗 [Read more]({source.get('url', '#')})
                        """)
            
            # Display metadata if available
            if message.get('metadata'):
                meta = message['metadata']
                cols = st.columns(3)
                with cols[0]:
                    st.metric("Articles Used", meta.get('articles_used', 0))
                with cols[1]:
                    st.metric("Newly Fetched", meta.get('newly_fetched', 0))
                with cols[2]:
                    status = "💾 Cached" if meta.get('cached') else "✨ Fresh"
                    st.metric("Status", status)
                
                # Display validation results if available (stored in message)
                if message['role'] == 'assistant' and message.get('validation'):
                    st.divider()
                    render_validation_results(
                        message['validation']['result'], 
                        message['validation']['run_fidelity']
                    )
    
    # Chat input
    if prompt := st.chat_input("Ask about any news topic..."):
        # Add user message to chat
        st.session_state.messages.append({
            'role': 'user',
            'content': prompt,
            'timestamp': datetime.now().isoformat()
        })
        
        # Display user message
        with st.chat_message('user'):
            st.markdown(prompt)
        
        # Generate assistant response
        with st.chat_message('assistant'):
            with st.spinner('🔍 Searching and analyzing news...'):
                try:
                    # Process query through orchestrator
                    result = st.session_state.orchestrator.process_query(
                        user_query=prompt,
                        max_articles=max_articles,
                        summary_length=summary_length,
                        style=style
                    )
                    
                    # Check for errors
                    if result.get('error'):
                        st.error(f"⚠️ {result['error']}")
                        
                        # Show debug info
                        with st.expander("🔍 Debug Info"):
                            st.json({
                                'extracted_topic': result.get('topic'),
                                'articles_used': result.get('articles_used', 0),
                                'newly_fetched': result.get('newly_fetched', 0),
                                'error': result.get('error')
                            })
                        
                        response_content = f"I encountered an issue: {result['error']}"
                        sources = []
                        metadata = None
                    elif not result.get('summary'):
                        st.warning("⚠️ No articles found for this topic. Try a different query or check back later.")
                        response_content = "I couldn't find any articles on this topic. Try:\n- Using different keywords\n- Broadening your search\n- Checking back later for new articles"
                        sources = []
                        metadata = None
                    else:
                        # Display summary with proper formatting
                        st.write(result['summary'])
                        response_content = result['summary']  # Store original for history
                        sources = result.get('sources', [])
                        articles = result.get('articles', [])  # Get full articles for validation
                        
                        # Display metadata
                        metadata = {
                            'articles_used': result.get('articles_used', 0),
                            'newly_fetched': result.get('newly_fetched', 0),
                            'cached': result.get('cached', False),
                            'topic': result.get('topic', '')
                        }
                        
                        # Show status
                        status_msg = f"📊 Used {metadata['articles_used']} articles"
                        if metadata['newly_fetched'] > 0:
                            status_msg += f" | ✨ Fetched {metadata['newly_fetched']} new"
                        else:
                            status_msg += " | 💾 From cache"
                        st.caption(status_msg)
                        
                        # Display sources
                        if sources:
                            with st.expander(f"📚 Sources ({len(sources)} articles)"):
                                for i, source in enumerate(sources, 1):
                                    # Get relevance score if available
                                    relevance = source.get('similarity', 0)
                                    relevance_pct = f"{relevance * 100:.1f}%" if relevance > 0 else "N/A"
                                    
                                    st.markdown(f"""
                                    **{i}. {source.get('title', 'Untitled')}**
                                    - 📰 Source: {source.get('source', 'Unknown')}
                                    - 📅 Published: {source.get('published_at', 'Unknown')}
                                    - 🎯 Relevance: {relevance_pct}
                                    - 🔗 [Read more]({source.get('url', '#')})
                                    """)
                        
                        # Display metadata metrics
                        cols = st.columns(3)
                        with cols[0]:
                            st.metric("Articles Used", metadata['articles_used'])
                        with cols[1]:
                            st.metric("Newly Fetched", metadata['newly_fetched'])
                        with cols[2]:
                            status = "💾 Cached" if metadata['cached'] else "✨ Fresh"
                            st.metric("Status", status)
                        
                        # Automatically run validation
                        st.divider()
                        validation_data = None
                        try:
                            # Initialize validation pipeline
                            validation_pipeline = ValidationPipeline(
                                summarization_pipeline=st.session_state.get('orchestrator').summarization,
                                enable_fidelity_check=run_fidelity
                            )
                            
                            # Combine source texts - use articles which have full document content
                            source_texts = []
                            combined_sources = ""
                            for article in articles:
                                # Get document field which has full scraped content
                                content = article.get('document', article.get('content', ''))
                                if content:
                                    source_texts.append(content)
                                    combined_sources += f"\n\n{content}"
                            
                            # Debug: Check if we have content
                            if not combined_sources.strip():
                                st.warning("⚠️ No source content available for validation metrics")
                                # Log for debugging
                                st.info(f"Debug: Found {len(articles)} articles, {len(sources)} sources")
                            
                            # Validate the summary
                            validation_result = validation_pipeline.evaluate_summary(
                                summary=response_content,
                                original_text=combined_sources.strip(),
                                check_fidelity=run_fidelity,
                                source_articles=source_texts if run_fidelity else None
                            )
                            
                            validation_data = {
                                'result': validation_result,
                                'run_fidelity': run_fidelity
                            }
                            
                            # Display validation results immediately
                            render_validation_results(validation_result, run_fidelity)
                        
                        except Exception as e:
                            st.error(f"❌ Validation error: {str(e)}")
                            import traceback
                            st.code(traceback.format_exc())
                    
                    # Add assistant message to chat history with validation
                    st.session_state.messages.append({
                        'role': 'assistant',
                        'content': response_content,
                        'sources': sources,
                        'metadata': metadata,
                        'validation': validation_data,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    st.error(f"❌ An error occurred: {str(e)}")
                    error_msg = f"I encountered an error while processing your request: {str(e)}"
                    st.session_state.messages.append({
                        'role': 'assistant',
                        'content': error_msg,
                        'timestamp': datetime.now().isoformat()
                    })


def render_welcome_message():
    """Display a welcome message when chat is empty."""
    if not st.session_state.get('messages'):
        st.markdown("""
        ### 👋 Welcome to Nunu AI - AI News Assistant!
        
        I can help you:
        - 📰 Find and summarize recent news on any topic
        - 🔍 Search through thousands of news sources
        - 📊 Provide citations and sources for all information
        - 💾 Cache results for faster responses
        
        **Just ask me anything!** For example:
        - "What's new with artificial intelligence?"
        - "Tell me about recent climate change developments"
        - "Summarize the latest tech news"
        
        I'll automatically fetch, analyze, and summarize the most relevant articles for you.
        """)
