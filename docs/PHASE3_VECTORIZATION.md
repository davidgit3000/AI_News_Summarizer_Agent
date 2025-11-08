# Phase 3: Vectorization Module - Complete ✅

## Overview
The Vectorization Module generates high-quality embeddings for news articles using Sentence Transformers, enabling semantic search and similarity-based retrieval for the RAG pipeline.

## Components Created

### 1. **TextEmbedder** (`src/vectorization/embedder.py`)
Generates embeddings using Sentence Transformers.

**Features:**
- Pre-trained model loading (`all-MiniLM-L6-v2` by default)
- Single text and batch embedding generation
- Article-specific embedding (combines title, description, content)
- Cosine similarity computation
- Efficient batch processing

**Model Information:**
- **Model:** `all-MiniLM-L6-v2`
- **Embedding Dimension:** 384
- **Max Sequence Length:** 256 tokens
- **Performance:** Fast, lightweight, high-quality embeddings

**Key Methods:**
```python
embedder = TextEmbedder()

# Single text
embedding = embedder.embed_text("AI is transforming technology")

# Batch processing
texts = ["text1", "text2", "text3"]
embeddings = embedder.embed_texts(texts, batch_size=32)

# Article embedding
article = {'title': '...', 'description': '...', 'content': '...'}
embedding = embedder.embed_article(article)

# Similarity
similarity = embedder.compute_similarity(embedding1, embedding2)
```

### 2. **VectorizationPipeline** (`src/vectorization/pipeline.py`)
Integrated pipeline for generating and storing embeddings.

**Features:**
- Automatic embedding generation for new articles
- Batch processing with progress tracking
- Database integration for embedding storage
- Similarity search across all articles
- Re-vectorization support (when changing models)
- Pipeline status monitoring

**Key Methods:**
```python
pipeline = VectorizationPipeline()

# Vectorize all articles without embeddings
stats = pipeline.vectorize_all_articles(batch_size=32)

# Vectorize specific articles
stats = pipeline.vectorize_articles(article_ids=[1, 2, 3])

# Search similar articles
results = pipeline.search_similar_articles(
    query_text="artificial intelligence",
    top_k=5
)

# Get status
status = pipeline.get_pipeline_status()
```

## Database Integration

### Embedding Storage
Embeddings are stored as BLOB in the SQLite database:

```sql
articles (
    ...
    embedding BLOB,  -- Numpy array stored as bytes
    ...
)
```

**Storage Format:**
- Type: `numpy.float32`
- Size: 384 dimensions × 4 bytes = 1,536 bytes per article
- Conversion: `embedding.tobytes()` → database, `np.frombuffer()` → retrieval

## Testing

### Test Script: `test_vectorization.py`
Comprehensive test suite for all vectorization components.

**Run tests:**
```bash
python test_vectorization.py
```

**Test Coverage:**
- ✅ Model loading and initialization
- ✅ Single text embedding
- ✅ Batch embedding generation
- ✅ Similarity computation
- ✅ Database embedding storage
- ✅ Pipeline vectorization
- ✅ Similarity search

## Test Results

```
Text Embedder:           ✅ PASS
Database Storage:        ✅ PASS
Vectorization Pipeline:  ✅ PASS

🎉 All tests passed! Phase 3 is complete!
```

**Performance:**
- Model loading: ~5 seconds (first time, cached afterwards)
- Embedding generation: ~10 articles/second
- Batch processing: Efficient with automatic batching
- Storage: ~1.5KB per article embedding

## Usage Examples

### Example 1: Vectorize All Articles
```python
from src.vectorization.pipeline import VectorizationPipeline

pipeline = VectorizationPipeline()

# Vectorize all articles without embeddings
stats = pipeline.vectorize_all_articles(batch_size=32, show_progress=True)

print(f"Processed: {stats['processed']}")
print(f"Successful: {stats['successful']}")
```

### Example 2: Similarity Search
```python
pipeline = VectorizationPipeline()

# Search for similar articles
results = pipeline.search_similar_articles(
    query_text="machine learning and AI",
    top_k=5
)

for result in results:
    print(f"{result['title']}")
    print(f"Similarity: {result['similarity_score']:.4f}")
    print(f"Source: {result['source']}\n")
```

### Example 3: Custom Embedding Model
```python
# Use a different model
pipeline = VectorizationPipeline(model_name="all-mpnet-base-v2")

# Re-vectorize all articles with new model
stats = pipeline.re_vectorize_all(batch_size=16)
```

### Example 4: Compute Similarity Between Articles
```python
from src.vectorization.embedder import TextEmbedder

embedder = TextEmbedder()

text1 = "Artificial intelligence is advancing rapidly"
text2 = "Machine learning models are improving"
text3 = "The weather is sunny today"

emb1 = embedder.embed_text(text1)
emb2 = embedder.embed_text(text2)
emb3 = embedder.embed_text(text3)

print(f"AI vs ML: {embedder.compute_similarity(emb1, emb2):.4f}")  # High
print(f"AI vs Weather: {embedder.compute_similarity(emb1, emb3):.4f}")  # Low
```

## Configuration

Settings in `.env`:

```bash
# Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Database (for embedding storage)
DATABASE_PATH=./data/news_cache.db
```

## Available Models

You can use any Sentence Transformers model:

| Model | Dimension | Performance | Quality |
|-------|-----------|-------------|---------|
| `all-MiniLM-L6-v2` | 384 | Fast | Good (default) |
| `all-mpnet-base-v2` | 768 | Medium | Excellent |
| `all-MiniLM-L12-v2` | 384 | Fast | Very Good |
| `paraphrase-MiniLM-L6-v2` | 384 | Fast | Good |

**To change model:**
```python
pipeline = VectorizationPipeline(model_name="all-mpnet-base-v2")
```

Or in `.env`:
```bash
EMBEDDING_MODEL=all-mpnet-base-v2
```

## How It Works

### 1. Text Preprocessing
```
Article → Combine (title + description + content) → Clean text
```

### 2. Embedding Generation
```
Text → Tokenization → BERT Model → Mean Pooling → 384-dim vector
```

### 3. Storage
```
Numpy array → tobytes() → SQLite BLOB
```

### 4. Retrieval
```
SQLite BLOB → frombuffer() → Numpy array → Similarity computation
```

## Similarity Computation

Uses **cosine similarity**:

```
similarity = (A · B) / (||A|| × ||B||)
```

**Range:** 0.0 (completely different) to 1.0 (identical)

**Typical values:**
- 0.8-1.0: Very similar (same topic, similar wording)
- 0.5-0.8: Related (same domain, different aspects)
- 0.2-0.5: Somewhat related
- 0.0-0.2: Unrelated

## Integration with RAG Pipeline

The vectorization module prepares articles for:

1. **Phase 4 (Retrieval):** ChromaDB will use these embeddings for fast semantic search
2. **Phase 5 (Summarization):** Retrieved articles will be used as context for LLM
3. **Phase 6 (Validation):** Embeddings can help verify summary relevance

## Performance Optimization

**Tips for faster processing:**

1. **Batch size:** Larger batches (32-64) are faster but use more memory
2. **GPU acceleration:** Automatically uses MPS (Apple Silicon) or CUDA if available
3. **Caching:** Model is cached after first load
4. **Incremental updates:** Only vectorize new articles

**Example:**
```python
# Fast: Process in large batches
pipeline.vectorize_all_articles(batch_size=64)

# Memory-efficient: Smaller batches
pipeline.vectorize_all_articles(batch_size=16)
```

## Error Handling

### Common Issues:

**1. Model Download**
First run downloads ~90MB model (cached afterwards)
**Solution:** Wait for download, or pre-download model

**2. Empty Text**
Articles without content get zero vectors
**Solution:** Handled automatically, returns zero vector

**3. Memory Issues**
Large batches may cause OOM
**Solution:** Reduce batch_size parameter

## Next Steps

Phase 3 is complete! Ready for:
- **Phase 4:** Retrieval Module (ChromaDB integration for fast semantic search)
- **Phase 5:** LLM Summary Module (RAG-based summarization)

## Files Created

```
src/
└── vectorization/
    ├── __init__.py
    ├── embedder.py           # Text embedding generator
    └── pipeline.py           # Vectorization pipeline

test_vectorization.py         # Test suite
docs/
└── PHASE3_VECTORIZATION.md   # This file
```

## API Reference

See inline documentation in each module for detailed API reference.

---

**Status:** ✅ Complete and Tested  
**Date:** November 7, 2025  
**Next Phase:** Retrieval Module (ChromaDB)
