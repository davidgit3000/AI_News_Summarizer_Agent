# UI Components

This folder contains modularized Streamlit UI components for the AI News Summarizer application.

## Structure

```
ui/
├── __init__.py                    # Package initialization and exports
├── sidebar.py                     # Sidebar with stats and settings
├── ingestion_tab.py               # News ingestion tab
├── search_tab.py                  # Article search and single-article summarization
├── summarization_tab.py           # Main summarization coordinator (25 lines)
├── analytics_tab.py               # Analytics and statistics
├── components/                    # Reusable UI components
│   ├── __init__.py
│   └── validation_display.py     # Reusable validation results display
└── summarization/                 # Summarization sub-components
    ├── __init__.py
    ├── standard_summary.py        # Standard topic summarization with validation
    └── qa_summary.py              # Q&A-based summarization
```

## Components

### `sidebar.py`
Renders the sidebar with:
- **Statistics**: Article count from database
- **API Keys Status**: Visual indicators for OpenAI, NewsAPI, and Gemini
- **Settings**: LLM and retrieval configuration (read from `.env`)

### `ingestion_tab.py`
Handles news article fetching with three modes:
- **Top Headlines**: Breaking news with optional filters
- **By Topic**: Search for specific topics with date range
- **Everything**: Advanced search with sorting options

Features automatic vectorization and Pinecone sync after fetching.

### `search_tab.py`
Article search and single-article summarization:
- **Search Articles**: Query articles by topic with similarity search
- **View Article Details**: Read full article content
- **Summarize Individual Articles**: Generate summaries with style options
- **Validate Summaries**: Quality metrics and optional fidelity checking

### `summarization_tab.py` (Refactored)
Main coordinator for summarization features (25 lines):
- Delegates to `summarization/standard_summary.py` for topic summarization
- Delegates to `summarization/qa_summary.py` for Q&A mode
- Clean separation of concerns

### `summarization/standard_summary.py`
Standard topic-based summarization with validation (200 lines):
- Topic-based RAG search
- Configurable article count and summary length
- Multiple styles: concise, comprehensive, bullet_points, executive, technical, eli5
- Integrated validation with quality metrics
- Optional fidelity checking (Gemini)
- Uses `components/validation_display.py` for results

### `summarization/qa_summary.py`
Q&A-based summarization interface (160 lines):
- Multi-question input support
- Generates targeted answers from retrieved articles
- Displays overview and Q&A pairs
- Shows source articles with metadata
- Clears validation state to prevent background checks

### `components/validation_display.py`
Reusable validation results component (106 lines):
- **Quality Metrics**: Overall score, compression, readability, lexical diversity, information density, coherence
- **Fidelity Analysis**: Overall fidelity, factual consistency, hallucination detection
- **Recommendations**: Actionable suggestions for improvement
- **Reusable**: Used in both `search_tab.py` and `summarization/standard_summary.py`

### `analytics_tab.py`
Database statistics and analytics:
- Article count and distribution
- Source breakdown
- Ingestion timeline
- Database health metrics

## Usage

Run the application:
```bash
streamlit run app.py
``` 

## Adding New Components

### Adding a New Tab
1. Create a new file in `ui/` (e.g., `ui/new_tab.py`)
2. Define a render function:
   ```python
   import streamlit as st
   
   def render_new_tab():
       st.header("New Feature")
       # Your UI code here
   ```
3. Export it in `ui/__init__.py`:
   ```python
   from .new_tab import render_new_tab
   __all__ = [..., 'render_new_tab']
   ```
4. Use it in `app.py`:
   ```python
   from ui import render_new_tab
   
   tab1, tab2, ..., tabN = st.tabs([..., "🆕 New Feature"])
   with tabN:
       render_new_tab()
   ```

### Adding a Reusable Component
1. Create file in `ui/components/` (e.g., `ui/components/chart_display.py`)
2. Define reusable function:
   ```python
   import streamlit as st
   
   def render_chart(data: dict):
       """Reusable chart display component."""
       # Chart rendering logic
   ```
3. Export in `ui/components/__init__.py`:
   ```python
   from .chart_display import render_chart
   __all__ = [..., 'render_chart']
   ```
4. Import and use anywhere:
   ```python
   from ui.components import render_chart
   
   render_chart(my_data)
   ```

## File Organization Best Practices

- **Main tabs** → `ui/[tab_name]_tab.py`
- **Reusable components** → `ui/components/[component_name].py`
- **Tab sub-components** → `ui/[tab_name]/[feature].py`
- **Keep main files small** → Delegate to sub-components
- **Single responsibility** → Each file should do one thing well
