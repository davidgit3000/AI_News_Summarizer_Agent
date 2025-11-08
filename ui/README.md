# UI Components

This folder contains modularized Streamlit UI components for the AI News Summarizer application.

## Structure

```
ui/
├── __init__.py           # Package initialization and exports
├── sidebar.py            # Sidebar with stats and settings
├── ingestion_tab.py      # News ingestion tab
├── summarization_tab.py  # Summarization tab
├── validation_tab.py     # Validation tab
└── analytics_tab.py      # Analytics tab
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

Features automatic vectorization and ChromaDB sync after fetching.

### `summarization_tab.py`
Generates summaries using RAG:
- Topic-based search
- Configurable article count and summary length
- Multiple styles: concise, comprehensive, bullet points
- Displays sources with similarity scores

### `validation_tab.py`
Evaluates summary quality:
- **Quality Metrics**: Readability, lexical diversity, compression ratio
- **Fidelity Check**: Gemini-powered hallucination detection
- **Source References**: Links to original articles

### `analytics_tab.py`
Placeholder for future analytics features:
- Summary quality trends
- Topic analysis
- Source distribution
- Performance metrics

## Usage

### Option 1: Use Modular Version
Run the modular version that uses these components:
```bash
streamlit run app_modular.py
```

### Option 2: Keep Original
Keep using the original `app.py` (all code in one file):
```bash
streamlit run app.py
```

## Benefits of Modularization

✅ **Easy Maintenance**: Each tab is in its own file  
✅ **Better Organization**: Clear separation of concerns  
✅ **Reusability**: Components can be reused or tested independently  
✅ **Collaboration**: Multiple developers can work on different tabs  
✅ **Scalability**: Easy to add new tabs or features  

## Adding New Components

1. Create a new file in `ui/` (e.g., `ui/new_tab.py`)
2. Define a render function:
   ```python
   def render_new_tab():
       st.header("New Feature")
       # Your UI code here
   ```
3. Export it in `ui/__init__.py`:
   ```python
   from .new_tab import render_new_tab
   __all__ = [..., 'render_new_tab']
   ```
4. Use it in `app_modular.py`:
   ```python
   with tab5:
       render_new_tab()
   ```
