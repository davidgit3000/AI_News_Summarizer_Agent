"""
Search tab component for finding and summarizing individual articles.
"""

import streamlit as st
from src.database.db_factory import get_database_manager
from src.retrieval.pipeline import RetrievalPipeline
from src.summarization.pipeline import SummarizationPipeline
from src.validation.pipeline import ValidationPipeline
from ui.components.validation_display import render_validation_results
from ui.sidebar import get_selected_model
from dateutil import parser


def render_search_tab():
    """Render the article search and individual summarization tab."""
    st.header("🔍 Search & Summarize Articles")
    st.write("Search for articles by topic or source, then summarize individual articles")
    
    # Search section
    st.subheader("📋 Search Articles")
    
    col1, col2 = st.columns(2)
    
    with col1:
        search_mode = st.selectbox(
            "Search By",
            ["Topic/Keyword", "Source"],
            help="Search by topic/keyword or filter by news source"
        )
    
    with col2:
        if search_mode == "Topic/Keyword":
            search_query = st.text_input("Enter topic or keyword", placeholder="e.g., artificial intelligence")
        else:
            # Get available sources from database
            db = get_database_manager()
            stats = db.get_stats()
            sources = list(stats.get('articles_by_source', {}).keys())
            search_query = st.selectbox("Select Source", [""] + sorted(sources))
    
    max_results = st.slider("Maximum Results", 5, 50, 20)
    
    if st.button("🔍 Search Articles", type="primary"):
        if not search_query:
            st.warning("⚠️ Please enter a search query or select a source")
        else:
            with st.spinner("Searching articles..."):
                try:
                    db = get_database_manager()
                    
                    if search_mode == "Topic/Keyword":
                        # Use semantic search via retrieval pipeline
                        # from src.retrieval.pipeline import RetrievalPipeline
                        
                        if 'retrieval_pipeline' not in st.session_state or st.session_state.retrieval_pipeline is None:
                            st.session_state.retrieval_pipeline = RetrievalPipeline()
                        
                        # Semantic search with Pinecone/ChromaDB
                        # Use sidebar settings if available, otherwise use config defaults
                        from config import get_settings
                        settings = get_settings()
                        top_k = st.session_state.get('top_k_results', settings.top_k_results)
                        min_sim = st.session_state.get('similarity_threshold', settings.similarity_threshold)
                        
                        results = st.session_state.retrieval_pipeline.retrieve_for_query(
                            query=search_query,
                            top_k=top_k,
                            min_similarity=min_sim
                        )
                        
                        # Convert to article format
                        articles = []
                        for result in results:
                            article_id = int(result['id'])
                            # Get full article from database
                            full_article = db.get_article_by_id(article_id)
                            if full_article:
                                full_article['similarity'] = result['similarity']
                                articles.append(full_article)
                    else:
                        # Get articles by source
                        articles = db.get_articles_by_source(search_query, limit=max_results)
                    
                    if articles:
                        st.session_state.search_results = articles
                        st.session_state.search_query = search_query
                        st.success(f"✅ Found {len(articles)} articles!")
                    else:
                        st.warning("⚠️ No articles found. Try a different search term.")
                        st.session_state.search_results = None
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # Display search results
    if st.session_state.get('search_results'):
        st.markdown("---")
        st.subheader(f"📰 Search Results ({len(st.session_state.search_results)} articles)")
        
        for idx, article in enumerate(st.session_state.search_results, 1):
            # Show similarity score if available
            title_suffix = ""
            if article.get('similarity'):
                relevance_pct = article['similarity'] * 100
                title_suffix = f" (Relevance: {relevance_pct:.1f}%)"
            
            # Use HTML to display title without markdown interpretation
            title = article['title']
            
            # Create expander - use HTML entity encoding to prevent markdown
            # Replace $ with HTML entity to prevent markdown issues
            safe_title = title.replace('$', '\\$')
            
            with st.expander(f"{idx}. {safe_title}{title_suffix}", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    if article.get('description'):
                        st.write(article['description'])
                    
                    # Format published date
                    if article.get('published_at'):
                        try:
                            dt = parser.parse(article['published_at'])
                            formatted_date = dt.strftime("%B %d, %Y at %I:%M %p")
                            st.caption(f"📅 Published: {formatted_date}")
                        except:
                            st.caption(f"📅 Published: {article['published_at']}")
                
                with col2:
                    st.write(f"**Source:** {article['source']}")
                    if article.get('url'):
                        st.markdown(f"[🔗 Read Original]({article['url']})")
                
                # Summarize button for this article
                if st.button(f"✨ Summarize Article #{idx}", key=f"summarize_{article['id']}"):
                    st.session_state.selected_article = article
                    st.session_state.show_article_summary = True
                    st.rerun()
    
    # Article summarization section
    if st.session_state.get('show_article_summary') and st.session_state.get('selected_article'):
        st.markdown("---")
        render_article_summary()


def render_article_summary():
    """Render individual article summarization with Q&A."""
    article = st.session_state.selected_article
    
    st.subheader("📄 Article Summary & Q&A")
    st.markdown(f"### {article['title']}")
    st.caption(f"Source: {article['source']}")
    
    # Summary mode selector
    summary_mode = st.radio(
        "Choose Mode",
        ["📝 Generate Summary", "❓ Ask Questions"],
        horizontal=True,
        key="article_summary_mode"
    )
    
    if summary_mode == "📝 Generate Summary":
        col1, col2 = st.columns(2)
        with col1:
            summary_length = st.slider("Summary Length (words)", 50, 300, 150, key="article_summary_length")
        with col2:
            style = st.selectbox(
                "Style",
                [
                    "concise",
                    "comprehensive",
                    "bullet_points",
                    "executive",
                    "technical",
                    "eli5"
                ],
                key="article_summary_style",
                help="concise (brief overview) | comprehensive (detailed analysis) | bullet_points (key points list) | executive (business-focused) | technical (technical details) | eli5 (Explain Like I'm 5: simple language, short sentences, no jargon - perfect for beginners)"
            )
        
        if st.button("✨ Generate Summary", type="primary", key="generate_article_summary"):
            with st.spinner("Generating summary..."):
                try:
                    if st.session_state.summarization_pipeline is None:
                        st.session_state.summarization_pipeline = SummarizationPipeline(llm_model=get_selected_model())
                    
                    # Use the article content directly
                    content = article.get('content') or article.get('description', '')
                    
                    if not content:
                        st.warning("⚠️ Article content not available")
                    else:
                        # Generate summary using the proper summarize method with style-specific prompts
                        summary = st.session_state.summarization_pipeline.llm_client.summarize(
                            text=content,
                            max_length=summary_length,
                            style=style
                        )
                        
                        # Store summary in session state
                        st.session_state.current_summary = summary
                        st.session_state.current_article_for_validation = article
                        st.session_state.summary_generated = True
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        # Display summary if it exists (outside the button block so it persists after rerun)
        if st.session_state.get('summary_generated') and st.session_state.get('current_summary'):
            st.success("✅ Summary generated!")
            st.markdown("---")
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
                {st.session_state.current_summary.strip()}
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Add validation button
            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("📊 Validate Summary", key="validate_from_search"):
                    st.session_state.show_validation = True
                    st.rerun()
        
        # Show validation results if requested (outside the try block)
        if st.session_state.get('show_validation', False) and st.session_state.get('current_summary'):
            st.markdown("---")
            st.subheader("📊 Summary Validation")
            
            # Check if summary indicates unavailable content
            summary = st.session_state.current_summary
            unavailable_indicators = [
                'article content unavailable',
                'content unavailable',
                'subscription required',
                'cannot be accessed',
                'cannot access',
                'article cannot be read',
                'insufficient information',
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
                st.warning("⚠️ Cannot validate summary - article content is unavailable or inaccessible.")
                st.info("💡 The model indicated that the article content could not be accessed. This may be due to subscription requirements, access restrictions, or content unavailability.")
                
                # Reset validation flag
                if st.button("✅ Done", key="close_validation_unavailable"):
                    st.session_state.show_validation = False
                    st.rerun()
            else:
                with st.spinner("Running validation..."):
                    try:
                        # Get stored summary and article
                        article = st.session_state.current_article_for_validation
                        
                        # Get article content
                        article_content = article.get('content') or article.get('description', '')
                        
                        # Initialize validation pipeline with existing summarization pipeline
                        if 'validation_pipeline' not in st.session_state or st.session_state.validation_pipeline is None:
                            st.session_state.validation_pipeline = ValidationPipeline(
                                summarization_pipeline=st.session_state.get('summarization_pipeline'),
                                enable_fidelity_check=False
                            )
                        
                        # Validate the summary
                        validation_result = st.session_state.validation_pipeline.evaluate_summary(
                            summary=summary,
                            original_text=article_content,
                            check_fidelity=False,
                            source_articles=None
                        )
                        
                        # Display validation results using reusable component
                        render_validation_results(validation_result, run_fidelity=False)
                        
                        # Reset validation flag
                        if st.button("✅ Done", key="close_validation"):
                            st.session_state.show_validation = False
                            st.rerun()
                    
                    except Exception as e:
                        st.error(f"❌ Validation error: {str(e)}")
    
    else:  # Ask Questions mode
        st.write("**Ask questions about this article:**")
        questions_text = st.text_area(
            "Questions (one per line)",
            placeholder="What is the main point?\nWhat are the key findings?\nWhat are the implications?",
            height=120,
            key="article_questions"
        )
        
        if st.button("❓ Get Answers", type="primary", key="get_article_answers"):
            if not questions_text.strip():
                st.warning("⚠️ Please enter at least one question")
            else:
                questions = [q.strip() for q in questions_text.split('\n') if q.strip()]
                
                with st.spinner(f"Answering {len(questions)} questions..."):
                    try:
                        if st.session_state.summarization_pipeline is None:
                            st.session_state.summarization_pipeline = SummarizationPipeline(llm_model=get_selected_model())
                        
                        content = article.get('content') or article.get('description', '')
                        
                        if not content:
                            st.warning("⚠️ Article content not available")
                        else:
                            st.success(f"✅ Generated {len(questions)} answers!")
                            st.markdown("---")
                            
                            # Answer each question
                            for i, question in enumerate(questions, 1):
                                answer = st.session_state.summarization_pipeline.llm_client.answer_question(
                                    context=content,
                                    question=question,
                                    use_web_search= True if st.session_state.llm_model == 'gpt-4.1' else False
                                )
                                
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
                    
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    
    # Back button with spacing
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⬅️ Back to Search Results"):
        st.session_state.show_article_summary = False
        st.session_state.selected_article = None
        # Clear summary and validation states
        st.session_state.summary_generated = False
        st.session_state.show_validation = False
        st.session_state.current_summary = None
        st.session_state.current_article_for_validation = None
        st.rerun()
