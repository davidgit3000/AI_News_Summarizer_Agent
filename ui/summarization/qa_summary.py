"""
Q&A summarization interface.
"""

import streamlit as st
import traceback
from src.summarization.pipeline import SummarizationPipeline


def render_qa_summary():
    """Render the Q&A summarization interface."""
    # Clear validation state from Standard Summary tab to prevent background validation
    if 'show_summary_validation' in st.session_state:
        st.session_state.show_summary_validation = False
    
    st.write("Ask specific questions about a topic and get answers based on retrieved articles")
    
    # Topic input
    topic = st.text_input("Topic", placeholder="e.g., artificial intelligence", key="qa_topic")
    
    # Questions input
    st.write("**Enter your questions (one per line):**")
    questions_text = st.text_area(
        "Questions",
        placeholder="What are the latest developments?\nWhat are the main challenges?\nWhat is the future outlook?",
        height=150,
        key="qa_questions"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        max_articles = st.slider("Max Articles to Use", 1, 10, 5, key="qa_max_articles")
    with col2:
        st.write("")  # Spacer
    
    if st.button("❓ Generate Q&A Summary", type="primary", key="qa_button"):
        if not topic:
            st.warning("⚠️ Please enter a topic")
        elif not questions_text.strip():
            st.warning("⚠️ Please enter at least one question")
        else:
            # Parse questions
            questions = [q.strip() for q in questions_text.split('\n') if q.strip()]
            
            with st.spinner(f"Generating answers for {len(questions)} questions..."):
                try:
                    # Initialize pipeline if needed
                    if st.session_state.summarization_pipeline is None:
                        st.session_state.summarization_pipeline = SummarizationPipeline()
                    
                    # Generate Q&A summary
                    result = st.session_state.summarization_pipeline.summarize_with_questions(
                        topic=topic,
                        questions=questions,
                        max_articles=max_articles
                    )
                    
                    # Store in session
                    st.session_state.last_summary = result
                    
                    if result.get('summary') or result.get('answers'):
                        st.success(f"✅ Generated answers from {result.get('article_count', 0)} articles!")
                        
                        _display_qa_results(result, questions)
                    else:
                        st.warning("⚠️ No articles found for this topic. Try ingesting more articles first.")
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.code(traceback.format_exc())


def _display_qa_results(result: dict, questions: list):
    """Display Q&A summary results."""
    st.subheader("📄 Summary & Answers")
    st.markdown(f"**Topic:** {result['topic']}")
    st.markdown(f"**Articles Used:** {result.get('article_count', 0)}")
    st.markdown(f"**Questions:** {len(questions)}")
    
    st.markdown("---")
    
    # Display summary if available
    if result.get('summary'):
        st.markdown("### 📝 Overview")
        st.markdown(
            f"""
            <div style="
                background-color: #1e1e1e;
                border: 1px solid #4a4a4a;
                border-radius: 5px;
                padding: 15px 20px;
                margin: 0 0 20px 0;
                color: #e0e0e0;
                font-size: 16px;
                line-height: 1.6;
                white-space: pre-wrap;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            ">
            {result['summary'].strip()}
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Display Q&A pairs
    if result.get('answers'):
        st.markdown("### ❓ Questions & Answers")
        # answers is a dictionary with questions as keys
        for i, question in enumerate(questions, 1):
            answer = result['answers'].get(question, "No answer generated")
            with st.expander(f"**Q{i}: {question}**", expanded=True):
                st.markdown(
                    f"""
                    <div style="
                        background-color: #1e1e1e;
                        border: 1px solid #4a4a4a;
                        border-radius: 5px;
                        padding: 15px 20px;
                        margin: 10px 0;
                        color: #e0e0e0;
                        font-size: 16px;
                        line-height: 1.6;
                        white-space: pre-wrap;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    ">
                    {answer.strip()}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    
    st.markdown("---")
    
    # Display sources
    if result.get('sources'):
        with st.expander(f"📚 Sources ({len(result['sources'])})"):
            for i, source in enumerate(result['sources'], 1):
                st.markdown(f"**{i}. {source['title']}**")
                st.write(f"**Source:** {source['source']}")
                
                # Format published date
                if source.get('published_at'):
                    try:
                        from dateutil import parser
                        dt = parser.parse(source['published_at'])
                        formatted_date = dt.strftime("%B %d, %Y at %I:%M %p")
                        st.write(f"**Published:** {formatted_date}")
                    except:
                        st.write(f"**Published:** {source['published_at']}")
                
                st.write(f"**Similarity:** {source['similarity']:.2%}")
                if source.get('url'):
                    st.write(f"🔗 [Read full article]({source['url']})")
                st.markdown("---")
