"""
Validation tab component for evaluating summary quality.
"""

import streamlit as st
from src.validation.pipeline import ValidationPipeline


def render_validation_tab():
    """Render the summary validation tab."""
    st.header("✅ Summary Validation")
    st.write("Evaluate summary quality with comprehensive metrics")
    
    if st.session_state.last_summary is None:
        st.info("ℹ️ Generate a summary first to validate it")
    else:
        result = st.session_state.last_summary
        
        st.subheader("Summary to Validate")
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
        
        col1, col2 = st.columns(2)
        
        with col1:
            run_validation = st.checkbox("Run Quality Metrics", value=True)
        with col2:
            run_fidelity = st.checkbox("Run Fidelity Check (Gemini)", value=False)
        
        if st.button("🔍 Validate Summary", type="primary"):
            with st.spinner("Validating..."):
                try:
                    # Initialize validation pipeline
                    if st.session_state.validation_pipeline is None:
                        st.session_state.validation_pipeline = ValidationPipeline(
                            enable_fidelity_check=run_fidelity
                        )
                    
                    # Get source articles for validation
                    if 'articles' in result and result['articles']:
                        source_texts = [a.get('document', a.get('content', '')) for a in result['articles']]
                    else:
                        # Fallback to using titles if full articles not available
                        source_texts = [s.get('title', '') for s in result.get('sources', [])]
                    combined_sources = "\n\n".join(source_texts)
                    
                    # Run validation
                    validation_result = st.session_state.validation_pipeline.evaluate_summary(
                        summary=result['summary'],
                        original_text=combined_sources,
                        check_fidelity=run_fidelity,
                        source_articles=source_texts if run_fidelity else None
                    )
                    
                    # Display quality metrics
                    if run_validation:
                        st.subheader("📊 Quality Metrics")
                        
                        quality = validation_result['quality_assessment']
                        
                        # Overall score
                        col1, col2, col3 = st.columns(3)
                        col1.metric(
                            "Overall Quality", 
                            quality['overall'].upper(),
                            help="Overall assessment of summary quality based on all metrics"
                        )
                        col2.metric(
                            "Score", 
                            f"{quality['score']:.0f}/100",
                            help="Composite quality score (0-100) based on readability, diversity, and density"
                        )
                        col3.metric(
                            "Compression", 
                            f"{validation_result['metrics']['compression_ratio']:.1%}",
                            help="Ratio of summary to original length. Ideal: 20-40% (concise but complete)"
                        )
                        
                        # Detailed metrics
                        st.markdown("---")
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric(
                                "Readability", 
                                f"{validation_result['metrics']['readability']['flesch_reading_ease']:.1f}",
                                help="Flesch Reading Ease score (0-100). Ideal: 60-80 (plain English)"
                            )
                        with col2:
                            st.metric(
                                "Lexical Diversity", 
                                f"{validation_result['metrics']['lexical_diversity']:.1%}",
                                help="Ratio of unique words to total words. Ideal: 60-80% (varied vocabulary without repetition)"
                            )
                        with col3:
                            st.metric(
                                "Information Density", 
                                f"{validation_result['metrics']['information_density']:.1%}",
                                help="Ratio of important words (nouns, verbs, adjectives) to total words. Ideal: 30-60% (informative without filler)"
                            )
                        with col4:
                            st.metric(
                                "Coherence", 
                                f"{validation_result['metrics']['coherence']:.1%}",
                                help="Semantic similarity between consecutive sentences. Ideal: >30% (good logical flow)"
                            )
                        
                        # Recommendations
                        if quality['recommendations']:
                            st.markdown("---")
                            st.subheader("💡 Recommendations")
                            for rec in quality['recommendations']:
                                st.write(f"• {rec}")
                    
                    # Display fidelity results
                    if run_fidelity and 'fidelity' in validation_result:
                        st.markdown("---")
                        st.subheader("🔍 Fidelity Analysis")
                        
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
                        
                        if fidelity.get('explanation'):
                            with st.expander("📝 Detailed Explanation"):
                                # Use write with text wrapping
                                st.write(fidelity['explanation'])
                        
                        if fidelity.get('issues_found'):
                            st.warning("⚠️ Issues Found:")
                            # Display issues as bullet points
                            for issue in fidelity['issues_found']:
                                st.write(f"• {issue}")
                    
                    # Display source articles for reference
                    if result.get('sources'):
                        st.markdown("---")
                        st.subheader("📚 Source Articles")
                        with st.expander(f"View {len(result['sources'])} Source Articles"):
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
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
