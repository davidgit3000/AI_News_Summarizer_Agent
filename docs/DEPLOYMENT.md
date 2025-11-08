# 🚀 Deployment Guide

## Overview
This guide covers deploying the AI News Summarizer to various platforms and handling data persistence.

---

## 📊 Data Storage Architecture

### Current Local Setup
```
./data/news_cache.db    # SQLite database (articles, embeddings)
./chroma_db/            # ChromaDB vector store (semantic search)
```

### ⚠️ Important: Ephemeral vs Persistent Storage
- **Ephemeral**: Data is lost when the app restarts (Streamlit Cloud default)
- **Persistent**: Data survives restarts (requires configuration)

---

## 🎯 Deployment Options

### Option 1: Streamlit Community Cloud (Easiest - Free)

**Best for:** Demos, testing, small projects

**Limitations:**
- ⚠️ Ephemeral storage (data resets on restart)
- Limited resources
- Public by default

**Steps:**
1. Push code to GitHub:
   ```bash
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. Deploy:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Select your GitHub repo
   - Set main file: `app.py`

3. Add secrets (in Streamlit dashboard):
   ```toml
   OPENAI_API_KEY = "your_key"
   NEWSAPI_KEY = "your_key"
   GEMINI_API_KEY = "your_key"
   ```

**Data Persistence Solution:**
- Use external database (Supabase, Neon)
- Use managed vector DB (Pinecone, Weaviate)

---

### Option 2: Railway (Recommended for Production)

**Best for:** Production apps with persistent storage

**Features:**
- ✅ Persistent volumes
- ✅ PostgreSQL database included
- ✅ Automatic HTTPS
- **Cost:** ~$5-10/month

**Steps:**

1. Create `railway.json`:
   ```json
   {
     "$schema": "https://railway.app/railway.schema.json",
     "build": {
       "builder": "NIXPACKS"
     },
     "deploy": {
       "startCommand": "streamlit run app.py --server.port $PORT --server.address 0.0.0.0",
       "restartPolicyType": "ON_FAILURE",
       "restartPolicyMaxRetries": 10
     }
   }
   ```

2. Create `Procfile`:
   ```
   web: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
   ```

3. Deploy:
   - Go to [railway.app](https://railway.app)
   - Create new project from GitHub repo
   - Add PostgreSQL database (optional)
   - Add environment variables
   - Deploy!

4. Add persistent volume for ChromaDB:
   - In Railway dashboard: Settings → Volumes
   - Mount path: `/app/chroma_db`

---

### Option 3: Render

**Similar to Railway, good alternative**

**Steps:**
1. Create `render.yaml`:
   ```yaml
   services:
     - type: web
       name: ai-news-summarizer
       env: python
       buildCommand: pip install -r requirements.txt
       startCommand: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
       envVars:
         - key: OPENAI_API_KEY
           sync: false
         - key: NEWSAPI_KEY
           sync: false
         - key: GEMINI_API_KEY
           sync: false
   ```

2. Connect GitHub repo at [render.com](https://render.com)

---

## 💾 Database Migration Options

### Option A: Keep SQLite + Add Persistent Volume
**Pros:** No code changes needed
**Cons:** Limited scalability

**Railway/Render:**
- Mount volume to `/app/data`
- SQLite will persist across restarts

---

### Option B: Migrate to PostgreSQL (Recommended)
**Pros:** Better for production, scalable
**Cons:** Requires code changes

**Steps:**

1. Install PostgreSQL adapter:
   ```bash
   pip install psycopg2-binary
   ```

2. Update `requirements.txt`:
   ```
   psycopg2-binary==2.9.9
   ```

3. Modify `src/database/db_manager.py`:
   ```python
   import os
   from sqlalchemy import create_engine
   
   # Use PostgreSQL if DATABASE_URL is set, otherwise SQLite
   database_url = os.getenv('DATABASE_URL', 'sqlite:///./data/news_cache.db')
   
   # Railway/Render provide DATABASE_URL automatically
   ```

4. Use Supabase (Free tier):
   - Create project at [supabase.com](https://supabase.com)
   - Get connection string
   - Add as `DATABASE_URL` environment variable

---

## 🔍 Vector Database Options

### Option A: Keep ChromaDB with Persistent Volume
**Setup:**
- Mount volume to `/app/chroma_db` on Railway/Render
- No code changes needed

**Limitations:**
- Single instance only
- Manual backups needed

---

### Option B: Pinecone (Recommended for Production)
**Pros:** Managed, scalable, free tier
**Cons:** Requires code changes

**Steps:**

1. Sign up at [pinecone.io](https://pinecone.io)

2. Install Pinecone:
   ```bash
   pip install pinecone-client
   ```

3. Update `config.py`:
   ```python
   vector_store_type: str = "pinecone"  # or "chromadb"
   pinecone_api_key: str = ""
   pinecone_environment: str = "gcp-starter"
   pinecone_index_name: str = "news-articles"
   ```

4. Modify `src/retrieval/vector_store.py` to support Pinecone

---

### Option C: Weaviate Cloud
**Similar to Pinecone, good alternative**

---

## 🔐 Environment Variables for Production

Create these in your deployment platform:

```bash
# Required
OPENAI_API_KEY=sk-...
NEWSAPI_KEY=...
GEMINI_API_KEY=...

# Optional - Database
DATABASE_URL=postgresql://...  # If using PostgreSQL

# Optional - Vector Store
VECTOR_STORE_TYPE=pinecone  # or chromadb
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=gcp-starter
PINECONE_INDEX_NAME=news-articles

# App Configuration
LLM_MODEL=gpt-3.5-turbo
LLM_TEMPERATURE=0.3
TOP_K_RESULTS=5
SIMILARITY_THRESHOLD=0.7
```

---

## 📋 Pre-Deployment Checklist

- [ ] All API keys added to environment variables
- [ ] `.env` file in `.gitignore` (already done)
- [ ] `requirements.txt` is up to date
- [ ] Database persistence configured
- [ ] Vector store persistence configured
- [ ] Test locally with production settings
- [ ] Set up monitoring/logging (optional)

---

## 🔄 Recommended Production Setup

**For a robust production deployment:**

1. **App Hosting:** Railway or Render
2. **Database:** Supabase (PostgreSQL) - Free tier
3. **Vector Store:** Pinecone - Free tier (1M vectors)
4. **Monitoring:** Railway/Render built-in logs

**Estimated Cost:** $0-5/month (free tiers) or $10-15/month (paid)

---

## 🆘 Troubleshooting

### "Database is empty after restart"
- **Cause:** Ephemeral storage
- **Solution:** Add persistent volume or use external database

### "ChromaDB collection not found"
- **Cause:** Vector store data lost
- **Solution:** Add persistent volume or migrate to Pinecone

### "Port already in use"
- **Cause:** Streamlit default port conflict
- **Solution:** Use `--server.port $PORT` in start command

### "Module not found"
- **Cause:** Missing dependencies
- **Solution:** Ensure all packages in `requirements.txt`

---

## 📚 Additional Resources

- [Streamlit Deployment Docs](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app)
- [Railway Docs](https://docs.railway.app/)
- [Render Docs](https://render.com/docs)
- [Supabase Docs](https://supabase.com/docs)
- [Pinecone Docs](https://docs.pinecone.io/)

---

## 🎉 Quick Start (Streamlit Cloud)

**Fastest way to deploy (5 minutes):**

```bash
# 1. Push to GitHub
git add .
git commit -m "Ready for deployment"
git push

# 2. Go to share.streamlit.io
# 3. Connect repo
# 4. Add secrets
# 5. Deploy!
```

**Note:** Data will be ephemeral. For persistence, follow Option 2 (Railway) or Option B (PostgreSQL + Pinecone).
