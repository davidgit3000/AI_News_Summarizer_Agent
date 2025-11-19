"""
Reusable validation results display component.
"""

import streamlit as st
from typing import Dict, Any


def render_validation_results(validation_result: Dict[str, Any], run_fidelity: bool = False):
    """
    Render validation results including quality metrics and optional fidelity analysis.
    
    Args:
        validation_result: Dictionary containing validation metrics and assessment
        run_fidelity: Whether to display fidelity metrics (if available)
    """
    try:
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
            
            # Check if content was blocked by Gemini
            if fidelity.get('blocked', False):
                st.warning("⚠️ **Sensitive Content Detected**")
                st.info(
                    f"🛡️ {fidelity.get('block_message', 'This content was flagged as potentially sensitive by Gemini safety filters.')}\n\n"
                    f"**Block Reason:** {fidelity.get('block_reason', 'UNKNOWN')}\n\n"
                    "**Note:** Fidelity checking was skipped for this content. The summary quality metrics above are still valid."
                )
                st.markdown("---")
            
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
    
    except Exception as e:
        st.error(f"❌ Error displaying validation results: {str(e)}")
