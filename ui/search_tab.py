"""
Search tab component for finding and summarizing individual articles.
"""

import streamlit as st
from src.database.db_manager import DatabaseManager
from src.summarization.pipeline import SummarizationPipeline
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
            db = DatabaseManager()
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
                    db = DatabaseManager()
                    
                    if search_mode == "Topic/Keyword":
                        # Search by keyword in title or content
                        articles = db.search_articles(search_query, limit=max_results)
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
            with st.expander(f"**{idx}. {article['title']}**", expanded=False):
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
                ["concise", "comprehensive", "bullet_points"],
                key="article_summary_style"
            )
        
        if st.button("✨ Generate Summary", type="primary", key="generate_article_summary"):
            with st.spinner("Generating summary..."):
                try:
                    if st.session_state.summarization_pipeline is None:
                        st.session_state.summarization_pipeline = SummarizationPipeline()
                    
                    # Use the article content directly
                    content = article.get('content') or article.get('description', '')
                    
                    if not content:
                        st.warning("⚠️ Article content not available")
                    else:
                        # Generate summary using LLM directly
                        prompt = f"""Summarize the following article in approximately {summary_length} words.
                                        Style: {style}

                                        Article:
                                        {content}

                                        Summary:"""
                        
                        summary = st.session_state.summarization_pipeline.llm_client.generate(
                            prompt=prompt,
                            system_message="You are a professional news analyst.",
                            max_tokens=summary_length * 2
                        )
                        
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
                            {summary.strip()}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
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
                            st.session_state.summarization_pipeline = SummarizationPipeline()
                        
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
                                    question=question
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
        st.rerun()
