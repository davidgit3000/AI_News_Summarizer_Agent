"""
Ingestion tab component for fetching and storing news articles.
"""

import streamlit as st
from datetime import datetime, timedelta
from src.ingestion.pipeline import IngestionPipeline
from src.vectorization.pipeline import VectorizationPipeline
from src.retrieval.pipeline import RetrievalPipeline


def render_ingestion_tab():
    """Render the news ingestion tab."""
    st.header("📥 News Ingestion")
    st.write("Fetch and store news articles from NewsAPI")
    
    # Query tips expander
    with st.expander("💡 Query Tips - How to Search Effectively"):
        st.markdown("""
        **Basic Search:**
        - Simple words: `artificial intelligence` (finds articles with any of these words)
        - Single topic: `machine learning`
        
        **Advanced Search Operators:**
        - **Exact phrase**: Use quotes → `"large language models"`
        - **All words must appear**: Use AND → `AI AND healthcare`
        - **Any word can appear**: Use OR → `GPT OR ChatGPT OR OpenAI`
        - **Exclude words**: Use NOT or - → `AI NOT cryptocurrency`
        - **Required word**: Use + → `+ChatGPT applications`
        - **Complex queries**: Combine operators → `(AI OR "artificial intelligence") AND ethics NOT hype`
        
        **Tips for Better Results:**
        - 📅 **Date range matters**: Rare topics may need longer timeframes (7-30 days)
        - 🔄 **Try variations**: "AI models", "artificial intelligence models", "ML models"
        - 🎯 **Be specific**: Use exact phrases for specific topics
        - 🌐 **Sources**: Leave blank to search ALL sources (80,000+ available)
        
        **Examples:**
        - `"artificial intelligence" AND healthcare` - AI in healthcare
        - `(GPT-4 OR ChatGPT) AND research` - GPT research news
        - `+machine learning computer vision` - ML with computer vision
        """)
    
    # Fetch mode selector
    fetch_mode = st.selectbox(
        "📋 Fetch Mode",
        ["Top Headlines", "By Topic", "Everything (Advanced Search)"],
        help="Choose how to fetch articles: Top Headlines (breaking news), By Topic (specific subject), or Everything (custom search)"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if fetch_mode == "Top Headlines":
            query = st.text_input(
                "Search Query (optional)", 
                placeholder='e.g., "artificial intelligence" OR bitcoin',
                help="Use quotes for exact phrases, AND/OR/NOT for boolean search"
            )
            sources = st.text_input(
                "Sources (optional)", 
                placeholder="e.g., bbc-news,cnn,reuters",
                help="Leave blank to search ALL sources"
            )
        elif fetch_mode == "By Topic":
            query = st.text_input(
                "Topic (required)", 
                placeholder='e.g., "climate change" AND renewable',
                help="Use quotes for exact phrases, AND/OR for boolean search"
            )
        else:  # Everything
            query = st.text_input(
                "Search Query (required)", 
                placeholder='e.g., "artificial intelligence" OR bitcoin',
                help="Use advanced operators: quotes, AND, OR, NOT, +, -"
            )
            sources = st.text_input(
                "Sources (optional)", 
                placeholder="e.g., bbc-news,cnn,reuters",
                help="Leave blank to search ALL sources"
            )
    
    with col2:
        if fetch_mode == "Top Headlines":
            category = st.selectbox(
                "Category (optional)",
                ["", "business", "entertainment", "general", "health", "science", "sports", "technology"]
            )
            page_size = st.slider("Number of Articles", 5, 50, 20)
        elif fetch_mode == "By Topic":
            days_back = st.slider("Days Back", 1, 30, 7, help="How many days back to search")
            page_size = st.slider("Number of Articles", 5, 50, 20)
        else:  # Everything
            sort_by = st.selectbox(
                "Sort By",
                ["publishedAt", "relevancy", "popularity"],
                help="How to sort the results"
            )
            page_size = st.slider("Number of Articles", 5, 100, 50)
    
    # Date range for Everything mode
    if fetch_mode == "Everything (Advanced Search)":
        st.subheader("📅 Date Range")
        col_date1, col_date2 = st.columns(2)
        
        with col_date1:
            from_date = st.date_input(
                "From Date",
                value=datetime.now() - timedelta(days=7),
                max_value=datetime.now(),
                help="Oldest article date to search from"
            )
        
        with col_date2:
            to_date = st.date_input(
                "To Date",
                value=datetime.now(),
                max_value=datetime.now(),
                help="Newest article date to search to"
            )
        
        # Validate date range
        if from_date > to_date:
            st.error("⚠️ 'From Date' must be before 'To Date'")
    
    if st.button("🚀 Fetch Articles", type="primary"):
        # Validate required fields
        if fetch_mode == "By Topic" and not query:
            st.warning("⚠️ Please enter a topic")
        elif fetch_mode == "Everything (Advanced Search)" and not query:
            st.warning("⚠️ Please enter a search query")
        else:
            try:
                # Create progress container
                progress_container = st.container()
                
                with progress_container:
                    # Step 1: Fetch articles
                    with st.spinner("📰 Step 1/3: Fetching articles from NewsAPI..."):
                        if st.session_state.ingestion_pipeline is None:
                            st.session_state.ingestion_pipeline = IngestionPipeline()
                        
                        # Call appropriate method based on fetch mode
                        if fetch_mode == "Top Headlines":
                            stats = st.session_state.ingestion_pipeline.ingest_top_headlines(
                                query=query if query else None,
                                sources=sources if sources else None,
                                category=category if category else None,
                                page_size=page_size
                            )
                        elif fetch_mode == "By Topic":
                            stats = st.session_state.ingestion_pipeline.ingest_by_topic(
                                topic=query,
                                days_back=days_back,
                                max_results=page_size
                            )
                        else:  # Everything
                            # Convert date objects to datetime objects
                            from_datetime = datetime.combine(from_date, datetime.min.time())
                            to_datetime = datetime.combine(to_date, datetime.max.time())
                            
                            stats = st.session_state.ingestion_pipeline.ingest_everything(
                                query=query,
                                from_date=from_datetime,
                                to_date=to_datetime,
                                sources=sources if sources else None,
                                sort_by=sort_by,
                                page_size=page_size
                            )
                        
                        st.session_state.last_ingestion_stats = stats
                
                st.success(f"✅ Step 1/3: Fetched {stats['fetched']} articles ({stats['inserted']} new)")
                
                # Only continue if new articles were inserted
                if stats['inserted'] > 0:
                    # Step 2: Vectorize articles
                    with st.spinner("🔍 Step 2/3: Generating embeddings..."):
                        if st.session_state.vectorization_pipeline is None:
                            st.session_state.vectorization_pipeline = VectorizationPipeline()
                        
                        vectorize_result = st.session_state.vectorization_pipeline.vectorize_all_articles()
                        st.session_state.last_vectorize_stats = vectorize_result
                    
                    st.success(f"✅ Step 2/3: Vectorized {vectorize_result['successful']} articles")
                    
                    # Step 3: Sync to Pinecone
                    with st.spinner("🔄 Step 3/3: Syncing to Pinecone..."):
                        if st.session_state.retrieval_pipeline is None:
                            st.session_state.retrieval_pipeline = RetrievalPipeline()
                        
                        sync_result = st.session_state.retrieval_pipeline.sync_database_to_vector_store()
                        st.session_state.last_sync_stats = sync_result
                    
                    st.success(f"✅ Step 3/3: Synced {sync_result['synced']} articles to Pinecone")
                    
                    # Final success message
                    st.balloons()
                    st.success("🎉 All done! Articles are ready for summarization.")
                    
                    # Clear cache to update sidebar count on next page interaction
                    # (avoids immediate rerun which causes UI flicker)
                    st.cache_data.clear()
                else:
                    st.info("ℹ️ No new articles to process (all were duplicates)")
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # Display last ingestion stats (shown after rerun or if no new inserts)
    if st.session_state.last_ingestion_stats:
        stats = st.session_state.last_ingestion_stats
        st.success(f"✅ Successfully fetched {stats['fetched']} articles!")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Fetched", stats['fetched'])
        col2.metric("Inserted", stats['inserted'])
        col3.metric("Duplicates", stats['duplicates'])
        
        # Display auto-vectorization and sync stats if available
        if 'last_vectorize_stats' in st.session_state and st.session_state.last_vectorize_stats:
            st.info("✅ Auto-vectorization completed!")
            vec_stats = st.session_state.last_vectorize_stats
            col1, col2, col3 = st.columns(3)
            col1.metric("Vectorized", vec_stats['successful'])
            col2.metric("Processed", vec_stats['processed'])
            col3.metric("Failed", vec_stats['failed'])
        
        if 'last_sync_stats' in st.session_state and st.session_state.last_sync_stats:
            st.info("✅ Pinecone sync completed!")
            sync_stats = st.session_state.last_sync_stats
            col1, col2, col3 = st.columns(3)
            col1.metric("Synced", sync_stats['synced'])
            col2.metric("Skipped", sync_stats['skipped'])
            col3.metric("Failed", sync_stats['failed'])
