"""
Standard summarization interface with validation.
"""

import streamlit as st
from contextlib import nullcontext
from src.summarization.pipeline import SummarizationPipeline
from src.validation.pipeline import ValidationPipeline
from ui.components.validation_display import render_validation_results


def render_standard_summary():
    """Render the standard summarization interface with validation."""
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
            help="concise (brief overview) | comprehensive (detailed analysis) | bullet_points (key points list) | executive (business-focused) | technical (technical details) | eli5 (Explain Like I'm 5: simple language, short sentences, no jargon - perfect for beginners)"
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
        
        _display_summary(result)
        _display_validation_section(result)


def _display_summary(result: dict):
    """Display the generated summary and sources."""
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


def _display_validation_section(result: dict):
    """Display validation controls and results."""
    # Add validation options and button
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Checkbox for fidelity check (must be before button)
    run_fidelity = st.checkbox("Run Fidelity Check (Gemini)", value=False, key="run_fidelity_topic")
    
    # Validation button
    if st.button("📊 Validate Summary", key="validate_topic_summary"):
        st.session_state.show_summary_validation = True
        st.session_state.validation_needs_run = True
    
    # Show validation results if requested
    if st.session_state.get('show_summary_validation', False):
        st.markdown("---")
        st.subheader("📊 Summary Validation")
        
        # Check if summary indicates unavailable content
        summary = result.get('summary', '')
        unavailable_indicators = [
            'article content unavailable',
            'content unavailable',
            'subscription required',
            'cannot be accessed',
            'cannot access',
            'article cannot be read',
            'insufficient information',
            'some article content unavailable',
            'some articles cannot be read',
            'summary is unavailable',
            'summary cannot be provided',
            'cannot provide a',
            'not accessible in its entirety',
            'provided text appears to be',
            'limited information provided',
            'i cannot provide',
            "i'm sorry, but",
            'content is not accessible',
            'content provided is not relevant',
            'is unavailable',
            'is not available',
            'summary of the article is unavailable',
            'summary is not available',
            "i'm unable to access",
            'unable to access the content',
            'may require a subscription',
            'are not fully available',
            'sorry, the articles about',
            "sorry, i couldn't find",
            'articles you provided are not available',
            'articles provided are not available',
            "i'm sorry, but the articles",
            'sorry, but the articles',
            'the content of the provided articles is not accessible.',
        ]
        
        is_unavailable = any(indicator in summary.lower() for indicator in unavailable_indicators)
        
        if is_unavailable:
            st.warning("⚠️ Cannot validate summary - some or all article content is unavailable or inaccessible.")
            st.info("💡 The model indicated that article content could not be accessed. This may be due to subscription requirements, access restrictions, or content unavailability.")
        else:
            # Only show spinner if validation needs to run
            if st.session_state.get('validation_needs_run', False):
                spinner_context = st.spinner("Running validation...")
            else:
                spinner_context = nullcontext()
            
            with spinner_context:
                try:
                    # Get fidelity check setting
                    run_fidelity = st.session_state.get('run_fidelity_topic', False)
                    
                    # Re-initialize validation pipeline if fidelity setting changed or if it doesn't exist
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
                    
                    # Display validation results using reusable component
                    render_validation_results(validation_result, run_fidelity)
                
                except Exception as e:
                    st.error(f"❌ Validation error: {str(e)}")
