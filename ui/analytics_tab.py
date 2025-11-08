"""
Analytics tab component for displaying insights and trends.
"""

import streamlit as st
from datetime import datetime, timedelta
from collections import Counter
from src.database.db_factory import get_database_manager


@st.cache_data(ttl=60, show_spinner=False)
def get_analytics_stats():
    """Get analytics stats with caching (60 second TTL)."""
    db = get_database_manager()
    return db.get_stats()


@st.cache_data(ttl=60, show_spinner=False)
def get_recent_activity_counts():
    """Get recent activity counts with caching (60 second TTL)."""
    from src.database.postgres_manager import Article
    db = get_database_manager()
    session = db.get_session()
    
    try:
        now = datetime.now()
        periods = {
            "Last 24 Hours": now - timedelta(days=1),
            "Last 7 Days": now - timedelta(days=7),
            "Last 30 Days": now - timedelta(days=30)
        }
        
        counts = {}
        for period_name, start_date in periods.items():
            count = session.query(Article).filter(
                Article.published_at >= start_date
            ).count()
            counts[period_name] = count
        
        return counts
    finally:
        session.close()


@st.cache_data(ttl=60, show_spinner=False)
def get_trending_articles():
    """Get trending articles with caching (60 second TTL)."""
    from src.database.postgres_manager import Article
    db = get_database_manager()
    session = db.get_session()
    
    try:
        articles = session.query(Article).order_by(
            Article.published_at.desc()
        ).limit(5).all()
        
        return [
            (a.title, a.source, a.published_at.isoformat() if a.published_at else None, a.url, a.description)
            for a in articles
        ]
    finally:
        session.close()


def render_analytics_tab():
    """Render the analytics tab with database insights."""
    st.header("📊 Analytics & Insights")
    st.write("Real-time analytics from your news database")
    
    try:
        with st.spinner("📊 Loading analytics data..."):
            stats = get_analytics_stats()
        
        # Overview metrics
        st.subheader("📈 Overview")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Articles", 
                stats['total_articles'],
                help="Total number of articles stored in your database"
            )
        with col2:
            st.metric(
                "Vectorized", 
                stats['articles_with_embeddings'],
                help="Number of articles that have been converted to embeddings for semantic search"
            )
        with col3:
            vectorization_rate = (stats['articles_with_embeddings'] / stats['total_articles'] * 100) if stats['total_articles'] > 0 else 0
            st.metric(
                "Vectorization Rate", 
                f"{vectorization_rate:.1f}%",
                help="Percentage of articles that have been vectorized and are ready for summarization"
            )
        with col4:
            pending = stats['total_articles'] - stats['articles_with_embeddings']
            st.metric(
                "Pending", 
                pending,
                help="Number of articles waiting to be vectorized"
            )
        
        st.markdown("---")
        
        # Source distribution
        st.subheader("📰 Source Distribution")
        if stats.get('articles_by_source'):
            # Sort sources by count
            sorted_sources = sorted(stats['articles_by_source'].items(), key=lambda x: x[1], reverse=True)
            
            # Show top 10 sources
            top_sources = sorted_sources[:10]
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Create a simple bar chart using metrics
                st.write("**Top 10 News Sources:**")
                for source, count in top_sources:
                    percentage = (count / stats['total_articles'] * 100) if stats['total_articles'] > 0 else 0
                    st.write(f"**{source}**: {count} articles ({percentage:.1f}%)")
                    st.progress(percentage / 100)
            
            with col2:
                st.write("**Summary:**")
                st.metric(
                    "Unique Sources", 
                    len(stats['articles_by_source']),
                    help="Total number of different news sources in your database"
                )
                avg_per_source = stats['total_articles'] / len(stats['articles_by_source']) if stats['articles_by_source'] else 0
                st.metric(
                    "Avg per Source", 
                    f"{avg_per_source:.1f}",
                    help="Average number of articles per news source"
                )
                
                if top_sources:
                    top_source_name, top_count = top_sources[0]
                    st.metric(
                        "Top Source", 
                        top_source_name,
                        help="News source with the most articles in your database"
                    )
                    st.caption(f"{top_count} articles")
        else:
            st.info("No articles ingested yet. Start by fetching some articles!")
        
        st.markdown("---")
        
        # Recent activity
        st.subheader("🕒 Recent Activity")
        
        with st.spinner("📅 Analyzing recent activity..."):
            counts = get_recent_activity_counts()
            
            col1, col2, col3 = st.columns(3)
            
            tooltips = {
                "Last 24 Hours": "Number of articles published in the last 24 hours",
                "Last 7 Days": "Number of articles published in the last 7 days",
                "Last 30 Days": "Number of articles published in the last 30 days"
            }
            
            for idx, (period_name, count) in enumerate(counts.items()):
                if idx == 0:
                    col1.metric(period_name, count, help=tooltips[period_name])
                elif idx == 1:
                    col2.metric(period_name, count, help=tooltips[period_name])
                else:
                    col3.metric(period_name, count, help=tooltips[period_name])
        
        st.markdown("---")
        
        # Database health
        st.subheader("💾 Database Health")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Storage Status:**")
            if stats['total_articles'] > 0:
                st.success(f"✅ {stats['total_articles']} articles stored")
            else:
                st.warning("⚠️ Database is empty")
            
            if stats['articles_with_embeddings'] > 0:
                st.success(f"✅ {stats['articles_with_embeddings']} articles vectorized")
            else:
                st.warning("⚠️ No articles vectorized yet")
            
            # Show vectorization completion status
            if pending == 0 and stats['total_articles'] > 0:
                st.success("✅ All articles are vectorized!")
        
        with col2:
            st.write("**Recommendations:**")
            has_recommendations = False
            
            if pending > 0:
                st.info(f"💡 Vectorize {pending} pending articles for better search")
                has_recommendations = True
            if stats['total_articles'] < 50:
                st.info("💡 Ingest more articles for better summaries")
                has_recommendations = True
            if stats.get('articles_by_source') and len(stats['articles_by_source']) < 5:
                st.info("💡 Add more diverse sources for balanced coverage")
                has_recommendations = True
            
            # Show positive message only if no recommendations were shown
            if not has_recommendations and stats['total_articles'] > 0:
                st.info("Database is in great shape!")
        
        st.markdown("---")
        
        # Top 5 Trending Articles (most recent)
        st.subheader("🔥 Top 5 Trending Articles")
        
        with st.spinner("🔥 Loading trending articles..."):
            trending_articles = get_trending_articles()
        
        if trending_articles:
            for idx, (title, source, published_at, url, description) in enumerate(trending_articles, 1):
                with st.expander(f"**{idx}. {title}**", expanded=(idx == 1)):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        if description:
                            st.write(description[:200] + "..." if len(description) > 200 else description)
                        # Format date for better readability
                        try:
                            from dateutil import parser
                            dt = parser.parse(published_at)
                            formatted_date = dt.strftime("%B %d, %Y at %I:%M %p")
                        except:
                            formatted_date = published_at
                        st.caption(f"📅 Published: {formatted_date}")
                    
                    with col2:
                        st.write(f"**Source:** {source}")
                        if url:
                            st.markdown(f"[🔗 Read More]({url})")
        else:
            st.info("No articles available yet. Start by ingesting some articles!")
        
    except Exception as e:
        st.error(f"❌ Error loading analytics: {str(e)}")
        st.info("💡 Make sure you have ingested some articles first!")
