# 📰 AI News Summarizer Agent

An intelligent news aggregation and summarization system powered by **RAG (Retrieval-Augmented Generation)** and **LLMs**. Built with production-grade cloud infrastructure using **Neon PostgreSQL** and **Pinecone** vector database.

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.29-FF4B4B.svg)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Project Overview

An end-to-end AI system that:

- ✅ **Fetches** latest news from NewsAPI
- ✅ **Stores** articles in **Neon PostgreSQL** (cloud database)
- ✅ **Vectorizes** content using Sentence Transformers
- ✅ **Indexes** embeddings in **Pinecone** for semantic search
- ✅ **Retrieves** relevant articles using RAG
- ✅ **Summarizes** with GPT-3.5/GPT-4 (OpenAI)
- ✅ **Validates** quality with Gemini fidelity checking
- ✅ **Presents** insights via beautiful Streamlit UI

## 🏗️ Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   NewsAPI   │───▶│  Ingestion   │───▶│    Neon     │
│             │    │   Pipeline   │    │ PostgreSQL  │
└─────────────┘    └──────────────┘    └─────────────┘
                           │                    │
                           ▼                    ▼
                   ┌──────────────┐    ┌─────────────┐
                   │Vectorization │───▶│  Pinecone   │
                   │   Pipeline   │    │ Vector DB   │
                   └──────────────┘    └─────────────┘
                                              │
                                              ▼
                   ┌──────────────┐    ┌─────────────┐
                   │     RAG      │◀───│  Retrieval  │
                   │ Summarizer   │    │   Pipeline  │
                   └──────────────┘    └─────────────┘
                           │
                           ▼
                   ┌──────────────┐    ┌─────────────┐
                   │   OpenAI     │───▶│   Gemini    │
                   │   GPT-3.5    │    │  Fidelity   │
                   └──────────────┘    └─────────────┘
                           │
                           ▼
                   ┌──────────────┐
                   │  Streamlit   │
                   │      UI      │
                   └──────────────┘
```

**Pipeline Stages:**

1. **Ingestion**: Fetch news from NewsAPI → Store in Neon PostgreSQL
2. **Vectorization**: Generate embeddings (384-dim) → Index in Pinecone
3. **Retrieval**: Semantic search using cosine similarity
4. **Summarization**: RAG-enhanced LLM summaries with source attribution
5. **Validation**: Gemini-powered fidelity checking + ROUGE metrics

## 🛠️ Tech Stack

### **Core Technologies**

- **Python 3.13** - Modern Python with latest features
- **Streamlit** - Interactive web UI with real-time updates

### **AI & ML**

- **OpenAI GPT-3.5/GPT-4** - Advanced text summarization
- **Google Gemini 2.5 Flash** - Fidelity checking and validation
- **Sentence Transformers** - Text embeddings (`all-MiniLM-L6-v2`)
- **ROUGE & NLTK** - Quality metrics

### **Databases**

- **Neon PostgreSQL** - Serverless Postgres (cloud-hosted)
- **Pinecone** - Managed vector database for semantic search
- **SQLAlchemy** - ORM for database operations

### **APIs & Services**

- **NewsAPI** - Real-time news data
- **Pinecone API** - Vector similarity search
- **OpenAI API** - LLM inference
- **Google AI API** - Gemini models

## 📋 Prerequisites

### **Required**

- Python 3.9+ (3.13 recommended)
- [OpenAI API Key](https://platform.openai.com/api-keys)
- [NewsAPI Key](https://newsapi.org/register)
- [Neon PostgreSQL Database](https://neon.tech) (Free tier available)
- [Pinecone Account](https://www.pinecone.io) (Free tier available)

### **Optional**

- [Google Gemini API Key](https://ai.google.dev) (for fidelity checking)

## 🚀 Quick Start

### **1. Clone and Setup**

```bash
git clone <repository-url>
cd AI_News_Summarizer_Agent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### **2. Setup Cloud Services**

#### **Neon PostgreSQL**

1. Sign up at [neon.tech](https://neon.tech)
2. Create a new project
3. Copy your connection string (starts with `postgresql://`)

#### **Pinecone**

1. Sign up at [pinecone.io](https://www.pinecone.io)
2. Create a new index:
   - **Name**: `news-summarizer`
   - **Dimensions**: `384`
   - **Metric**: `cosine`
   - **Cloud**: `AWS` (or your preference)
3. Copy your API key

📖 **Detailed setup guide**: See [`docs/NEON_PINECONE_SETUP.md`](docs/NEON_PINECONE_SETUP.md)

### **3. Configure Environment**

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your API keys
nano .env  # or use your preferred editor
```

**Required environment variables:**

```bash
# Database
DATABASE_URL=postgresql://user:pass@host.neon.tech/dbname?sslmode=require
VECTOR_STORE_TYPE=pinecone

# Vector Database
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=news-summarizer

# APIs
OPENAI_API_KEY=your_openai_api_key
NEWSAPI_KEY=your_newsapi_key

# Optional
GEMINI_API_KEY=your_gemini_api_key  # For fidelity checking
```

### **4. Initialize Database**

```bash
# Run database migrations
python -c "from src.database.postgres_manager import PostgresManager; PostgresManager()"
```

### **5. Run the Application**

```bash
# Start the Streamlit UI
streamlit run app.py
```

The app will open at `http://localhost:8501` 🎉

### **6. First Steps in the UI**

1. **Ingest Tab**:
   - Choose fetch mode (Top Headlines, By Topic, or Everything)
   - Use advanced query operators for precise searches:
     - Exact phrases: `"artificial intelligence"`
     - Boolean operators: `AI AND healthcare`, `(GPT OR ChatGPT) NOT hype`
     - Required/excluded words: `+machine learning`, `AI -cryptocurrency`
   - Set custom date ranges (Everything mode)
   - Click "Fetch Articles" to load news
2. **Summarize Tab**: Enter a topic (e.g., "AI") and generate summary
3. **Search Tab**: Search articles semantically
4. **Analytics Tab**: View insights and trends
5. **Validate Tab**: Check summary quality

## 📁 Project Structure

```
AI_News_Summarizer_Agent/
├── src/
│   ├── ingestion/              # News fetching and API integration
│   │   ├── news_fetcher.py     # NewsAPI client
│   │   └── pipeline.py         # Ingestion orchestration
│   ├── vectorization/          # Text embedding generation
│   │   ├── embedder.py         # Sentence Transformers wrapper
│   │   └── pipeline.py         # Vectorization orchestration
│   ├── retrieval/              # Vector store and semantic search
│   │   ├── vector_store.py     # ChromaDB implementation
│   │   ├── pinecone_store.py   # Pinecone implementation
│   │   └── pipeline.py         # RAG retrieval logic
│   ├── summarization/          # LLM-based summarization
│   │   ├── llm_client.py       # OpenAI API wrapper
│   │   └── pipeline.py         # RAG summarization
│   ├── validation/             # Quality metrics and evaluation
│   │   ├── evaluator.py        # ROUGE/BLEU metrics
│   │   ├── fidelity_checker.py # Gemini fidelity checking
│   │   └── pipeline.py         # Validation orchestration
│   └── database/               # Database management
│       ├── postgres_manager.py # Neon PostgreSQL ORM
│       ├── db_factory.py       # Database factory pattern
│       └── db_manager.py       # Legacy SQLite (deprecated)
├── ui/                         # Streamlit UI components
│   ├── ingestion_tab.py        # Article ingestion interface
│   ├── search_tab.py           # Semantic search interface
│   ├── summarize_tab.py        # Summarization interface
│   ├── validate_tab.py         # Validation interface
│   ├── analytics_tab.py        # Analytics dashboard
│   └── sidebar.py              # Sidebar component
├── docs/                       # Documentation
│   ├── NEON_PINECONE_SETUP.md  # Cloud setup guide
│   ├── DEPLOYMENT.md           # Deployment instructions
│   ├── GEMINI_SETUP.md         # Gemini API setup
│   └── PROJECT_SUMMARY.md      # Project overview
├── tests/                      # Unit and integration tests
├── .env                        # Environment variables (gitignored)
├── .env.example                # Example environment config
├── app.py                      # Streamlit app entry point
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🔧 Configuration Options

Edit `.env` to customize behavior:

| Variable              | Description                  | Default            | Options                  |
| --------------------- | ---------------------------- | ------------------ | ------------------------ |
| `DATABASE_URL`        | PostgreSQL connection string | Required           | Neon connection string   |
| `VECTOR_STORE_TYPE`   | Vector database to use       | `pinecone`         | `pinecone`, `chromadb`   |
| `PINECONE_API_KEY`    | Pinecone API key             | Required           | From pinecone.io         |
| `PINECONE_INDEX_NAME` | Pinecone index name          | `news-summarizer`  | Custom name              |
| `LLM_MODEL`           | OpenAI model for summaries   | `gpt-3.5-turbo`    | `gpt-4`, `gpt-3.5-turbo` |
| `LLM_TEMPERATURE`     | LLM creativity (0-1)         | `0.3`              | `0.0` - `1.0`            |
| `EMBEDDING_MODEL`     | Sentence transformer model   | `all-MiniLM-L6-v2` | Any SentenceTransformer  |
| `TOP_K_RESULTS`       | Articles to retrieve         | `5`                | `1` - `50`               |
| `GEMINI_API_KEY`      | Gemini API key (optional)    | None               | For fidelity checking    |

### **Switching Between Vector Stores**

**Use Pinecone (Recommended for production):**

```bash
VECTOR_STORE_TYPE=pinecone
PINECONE_API_KEY=your_key
```

**Use ChromaDB (Local development):**

```bash
VECTOR_STORE_TYPE=chromadb
```

## ✨ Features

### **📥 Ingestion**

- **Multi-mode fetching**: Top Headlines, By Topic, or Everything (Advanced Search)
- **Advanced query operators**: Boolean search (AND, OR, NOT), exact phrases, required/excluded words
- **Custom date ranges**: Flexible date pickers for precise time-based filtering
- **All NewsAPI sources**: Access to 80,000+ sources (not limited to predefined list)
- **Automatic deduplication**: Prevents duplicate articles in database
- **Batch processing**: Progress tracking with real-time updates
- **Cloud storage**: Neon PostgreSQL with full metadata preservation

### **🔍 Semantic Search**

- **Vector similarity search**: Powered by Pinecone for fast, scalable retrieval
- **384-dimensional embeddings**: Using Sentence Transformers (all-MiniLM-L6-v2)
- **Cosine similarity matching**: Accurate relevance scoring
- **Optimized metadata**: Smart content truncation (10KB limit) to stay within Pinecone's 40KB limit
- **Source filtering**: Search within specific news sources
- **Adjustable similarity threshold**: Fine-tune result quality

### **📝 Summarization**

- RAG-enhanced context retrieval
- GPT-3.5/GPT-4 powered summaries
- Source attribution
- Customizable length and style
- Q&A mode for specific questions

### **✅ Validation**

- ROUGE metrics (ROUGE-1, ROUGE-2, ROUGE-L)
- BLEU score calculation
- Gemini-powered fidelity checking
- Hallucination detection
- Quality scoring

### **📊 Analytics**

- Real-time database statistics
- Article trends by source
- Recent activity tracking
- Top trending articles
- Database health monitoring

## 📊 Development Status

- [x] **Phase 1**: Project Setup ✅
- [x] **Phase 2**: Data Ingestion Module ✅
- [x] **Phase 3**: Vectorization Module ✅
- [x] **Phase 4**: Retrieval Module (RAG) ✅
- [x] **Phase 5**: LLM Summary Module ✅
- [x] **Phase 6**: Validation Module ✅
- [x] **Phase 6.5**: Fidelity Checking (Gemini) ✅
- [x] **Phase 7**: UI Development (Streamlit) ✅
- [x] **Phase 8**: Cloud Migration (Neon + Pinecone) ✅
- [x] **Phase 9**: Performance Optimization ✅
- [x] **Phase 9.5**: Advanced Search Features ✅
  - Boolean query operators
  - Date range filtering
  - All NewsAPI sources enabled
  - Pinecone metadata optimization
- [x] **Phase 10**: Deployment (Completed)

## 🧪 Testing

```bash
# Run individual phase tests
python tests/test_ingestion.py
python tests/test_vectorization.py
python tests/test_retrieval.py
python tests/test_summarization.py
python tests/test_validation.py
python tests/test_fidelity.py

# Or run with pytest
pytest tests/
```

## 🔍 Advanced Search Features

### **Query Operators**

The system supports powerful NewsAPI query operators for precise article filtering:

**Basic Search:**

- Simple keywords: `artificial intelligence` (matches articles with any of these words)
- Single topic: `machine learning`

**Advanced Operators:**

- **Exact phrases**: Use quotes → `"large language models"`
- **All words required**: Use AND → `AI AND healthcare`
- **Any word matches**: Use OR → `GPT OR ChatGPT OR OpenAI`
- **Exclude words**: Use NOT or - → `AI NOT cryptocurrency`
- **Required word**: Use + → `+ChatGPT applications`
- **Complex queries**: Combine operators → `(AI OR "artificial intelligence") AND ethics NOT hype`

**Examples:**

```
"artificial intelligence" AND healthcare
(GPT-4 OR ChatGPT) AND research
+machine learning computer vision
crypto AND (ethereum OR bitcoin) NOT scam
```

### **Date Range Filtering**

When using "Everything (Advanced Search)" mode:

- **From Date**: Oldest article date to search from
- **To Date**: Newest article date to search to
- **Default range**: Last 7 days
- **Validation**: Automatically prevents invalid date ranges

### **Source Selection**

- **Leave blank**: Searches ALL 80,000+ NewsAPI sources
- **Specify sources**: Comma-separated list (e.g., `bbc-news,cnn,reuters`)
- **No limitations**: Not constrained to predefined source lists

## 📝 Usage Examples

### **Programmatic Usage**

```python
from src.summarization.pipeline import SummarizationPipeline

# Initialize pipeline
pipeline = SummarizationPipeline()

# Generate summary for a topic
result = pipeline.summarize_topic(
    topic="artificial intelligence",
    max_articles=5,
    summary_length=200,
    style="concise"
)

print(f"Summary: {result['summary']}")
print(f"Sources: {result['sources']}")
print(f"Quality Score: {result['quality_score']}")
```

### **Semantic Search**

```python
from src.retrieval.pipeline import RetrievalPipeline

# Initialize retrieval
retrieval = RetrievalPipeline()

# Search for articles
articles = retrieval.retrieve_for_query(
    query="machine learning breakthroughs",
    top_k=10,
    min_similarity=0.7
)

for article in articles:
    print(f"{article['title']} (Similarity: {article['similarity']:.2f})")
```

## 🚢 Deployment

See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for detailed deployment instructions.

**Quick Deploy Options:**

- **Streamlit Cloud**: Free hosting for Streamlit apps
- **Railway**: Easy deployment with PostgreSQL support
- **Render**: Free tier with automatic deployments
- **Docker**: Containerized deployment (Dockerfile included)

## 🤝 Contributing

This is a course project for CS 4200. Contributions and suggestions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is for educational purposes as part of CS 4200 - Fall 2025.

## 🆕 Recent Updates

### **v1.1.0 - Advanced Search & Optimization** (November 2025)

**New Features:**

- ✨ **Advanced Query Operators**: Full support for NewsAPI boolean search (AND, OR, NOT, quotes, +, -)
- 📅 **Date Range Filtering**: Custom date pickers for "Everything" search mode
- 🌐 **All Sources Enabled**: Access to 80,000+ NewsAPI sources (removed source limitations)
- 💡 **Query Tips UI**: Interactive help section with search examples and best practices

**Bug Fixes:**

- 🐛 **Pinecone Metadata Size**: Fixed 40KB metadata limit error by implementing smart content truncation (10KB limit)
- 🔧 **Source Parameter**: Fixed undefined `self.sources` attribute error in news fetcher
- ✅ **Date Validation**: Added validation to prevent invalid date ranges

**Improvements:**

- 📝 **Enhanced Documentation**: Updated README with advanced search examples
- 🎨 **Better UX**: Improved placeholder text and tooltips in search inputs
- 🔍 **Metadata Optimization**: Automatic size validation before Pinecone upsert

## 🔗 Resources

### **Documentation**

- [Neon PostgreSQL](https://neon.tech/docs)
- [Pinecone Vector Database](https://docs.pinecone.io)
- [OpenAI API](https://platform.openai.com/docs)
- [Google Gemini](https://ai.google.dev/docs)
- [Streamlit](https://docs.streamlit.io)
- [Sentence Transformers](https://www.sbert.net)

### **Tutorials**

- [RAG Implementation Guide](https://python.langchain.com/docs/use_cases/question_answering/)
- [Vector Database Comparison](https://www.pinecone.io/learn/vector-database/)
- [Prompt Engineering](https://platform.openai.com/docs/guides/prompt-engineering)

## 🙏 Acknowledgments

- **NewsAPI** for providing news data
- **OpenAI** for GPT models
- **Google** for Gemini API
- **Neon** for serverless PostgreSQL
- **Pinecone** for vector database
- **Streamlit** for the amazing UI framework

## 📧 Contact

For questions or issues, please open an issue in the repository.

---

**Built with ❤️ for CS 4200 - Fall 2025**  
_Intelligent news aggregation powered by AI_
