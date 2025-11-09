"""
Summarization tab component for generating news summaries.
"""

import streamlit as st
from src.summarization.pipeline import SummarizationPipeline


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


def render_standard_summary():
    """Render the standard summarization interface."""
    col1, col2 = st.columns(2)
    
    with col1:
        topic = st.text_input("Topic", placeholder="e.g., climate change")
        max_articles = st.slider("Max Articles to Use", 1, 10, 5)
    
    with col2:
        summary_length = st.slider("Summary Length (words)", 50, 500, 200)
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
            help="Choose summary style: concise (brief), comprehensive (detailed), bullet_points (key points), executive (business focus), technical (detailed analysis), eli5 (simple explanation)"
        )
    
    if st.button("✨ Generate Summary", type="primary"):
        if not topic:
            st.warning("⚠️ Please enter a topic")
        else:
            with st.spinner("Generating summary..."):
                try:
                    # Initialize pipeline if needed
                    if st.session_state.summarization_pipeline is None:
                        st.session_state.summarization_pipeline = SummarizationPipeline()
                    
                    # Generate summary
                    result = st.session_state.summarization_pipeline.summarize_topic(
                        topic=topic,
                        max_articles=max_articles,
                        summary_length=summary_length,
                        style=style
                    )
                    
                    # Store in session
                    st.session_state.last_summary = result
                    st.session_state.show_summary_validation = False  # Reset validation flag
                    
                    if result['summary']:
                        st.success("✅ Summary generated!")
                    else:
                        st.warning("⚠️ No articles found for this topic. Try ingesting more articles first.")
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # Display summary outside button block so it persists
    if st.session_state.get('last_summary') and st.session_state.last_summary.get('summary'):
        result = st.session_state.last_summary
        
        st.subheader("📄 Summary")
        st.markdown(f"**Topic:** {result['topic']}")
        st.markdown(f"**Articles Used:** {result['article_count']}")
        st.markdown(f"**Word Count:** {len(result['summary'].split())}")
        
        st.markdown("---")
        # Display summary with better contrast
        st.markdown(
            f"""
            <div style="
                background-color: #1e1e1e;
                border: 1px solid #4a4a4a;
                border-radius: 5px;
                padding: 15px 20px;
                margin: 0;
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
        st.markdown("---")
        
        # Display sources
        if result['sources']:
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
        
        # Add validation options and button
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Checkbox for fidelity check (must be before button)
        run_fidelity = st.checkbox("Run Fidelity Check (Gemini)", value=False, key="run_fidelity_topic")
        
        # Validation button
        if st.button("📊 Validate Summary", key="validate_topic_summary"):
            st.session_state.show_summary_validation = True
            st.session_state.validation_needs_run = True
            # st.rerun()
        
        # Show validation results if requested
        if st.session_state.get('show_summary_validation', False):
            st.markdown("---")
            st.subheader("📊 Summary Validation")
            
            # Only show spinner if validation needs to run
            if st.session_state.get('validation_needs_run', False):
                spinner_context = st.spinner("Running validation...")
            else:
                from contextlib import nullcontext
                spinner_context = nullcontext()
            
            with spinner_context:
                try:
                    from src.validation.pipeline import ValidationPipeline
                    
                    # Get fidelity check setting
                    run_fidelity = st.session_state.get('run_fidelity_topic', False)
                    
                    # Re-initialize validation pipeline if fidelity setting changed
                    # or if it doesn't exist
                    need_reinit = (
                        'validation_pipeline' not in st.session_state or 
                        st.session_state.validation_pipeline is None or
                        st.session_state.get('validation_needs_run', False)
                    )
                    
                    if need_reinit:
                        st.session_state.validation_pipeline = ValidationPipeline(
                            summarization_pipeline=st.session_state.get('summarization_pipeline'),
                            enable_fidelity_check=run_fidelity
                        )
                    
                    # Get source articles
                    source_texts = [a.get('document', a.get('content', '')) for a in result.get('articles', [])]
                    if not source_texts and result.get('sources'):
                        source_texts = [s.get('title', '') for s in result['sources']]
                    combined_sources = "\n\n".join(source_texts)
                    
                    # Validate the summary
                    validation_result = st.session_state.validation_pipeline.evaluate_summary(
                        summary=result['summary'],
                        original_text=combined_sources,
                        check_fidelity=run_fidelity,
                        source_articles=source_texts if run_fidelity else None
                    )
                    
                    # Mark validation as complete
                    st.session_state.validation_needs_run = False
                    
                    # Display quality metrics
                    st.markdown("#### 📈 Quality Metrics")
                    quality = validation_result['quality_assessment']
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric(
                        "Overall Quality", 
                        quality['overall'].upper(),
                        help="Overall assessment of summary quality"
                    )
                    col2.metric(
                        "Score", 
                        f"{quality['score']:.0f}/100",
                        help="Composite quality score (0-100)"
                    )
                    col3.metric(
                        "Compression", 
                        f"{validation_result['metrics']['compression_ratio']:.1%}",
                        help="Ratio of summary to original length. Ideal: 20-40% (concise but complete)"
                    )
                    
                    # Detailed metrics
                    with st.expander("📊 Detailed Metrics"):
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric(
                            "Readability", 
                            f"{validation_result['metrics']['readability']['flesch_reading_ease']:.1f}",
                            help="Flesch Reading Ease score (0-100). Ideal: 60-80 (plain English)"
                        )
                        col2.metric(
                            "Lexical Diversity", 
                            f"{validation_result['metrics']['lexical_diversity']:.1%}",
                            help="Ratio of unique words to total words. Ideal: 60-80% (varied vocabulary without repetition)"
                        )
                        col3.metric(
                            "Information Density", 
                            f"{validation_result['metrics']['information_density']:.1%}",
                            help="Ratio of important words (nouns, verbs, adjectives) to total words. Ideal: 30-60% (informative without filler)"
                        )
                        col4.metric(
                            "Coherence", 
                            f"{validation_result['metrics']['coherence']:.1%}",
                            help="Semantic similarity between consecutive sentences. Ideal: >30% (good logical flow)"
                        )
                    
                    # Recommendations
                    if quality['recommendations']:
                        st.markdown("#### 💡 Recommendations")
                        for rec in quality['recommendations']:
                            st.write(f"• {rec}")
                    
                    # Display fidelity results
                    if run_fidelity and 'fidelity' in validation_result:
                        st.markdown("---")
                        st.markdown("#### 🔍 Fidelity Analysis")
                        
                        fidelity = validation_result['fidelity']
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric(
                            "Overall Fidelity", 
                            f"{fidelity.get('overall_fidelity', 0):.2f}",
                            help="Overall measure of how faithful the summary is to the source articles (0-1). Higher = more accurate."
                        )
                        col2.metric(
                            "Factual Consistency", 
                            f"{fidelity.get('factual_consistency', 0):.2f}",
                            help="Measures if claims in summary are supported by source articles (0-1). 1.0 = all facts verified."
                        )
                        col3.metric(
                            "Hallucination-Free", 
                            f"{fidelity.get('hallucination_free', 0):.2f}",
                            help="Measures absence of fabricated information (0-1). 1.0 = no hallucinations detected."
                        )
                        
                        # Display explanation if available
                        if fidelity.get('explanation'):
                            with st.expander("📝 Detailed Explanation"):
                                st.write(fidelity['explanation'])
                        
                        # Display detailed fidelity issues if any
                        if fidelity.get('issues'):
                            st.markdown("##### ⚠️ Detected Issues")
                            for issue in fidelity['issues']:
                                st.warning(f"• {issue}")
                    
                    # Optional: Hide validation results
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # if st.button("Hide", key="close_summary_validation"):
                    #     st.session_state.show_summary_validation = False
                    #     st.rerun()
                
                except Exception as e:
                    st.error(f"❌ Validation error: {str(e)}")


def render_qa_summary():
    """Render the Q&A summarization interface."""
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
                    else:
                        st.warning("⚠️ No articles found for this topic. Try ingesting more articles first.")
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
