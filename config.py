"""
Configuration management for AI News Summarizer Agent.
Loads settings from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # Database Configuration
    database_url: str = ""  # Neon PostgreSQL URL
    use_postgres: bool = True  # Set to True to use PostgreSQL
    
    # API Keys
    openai_api_key: str = ""
    newsapi_key: str = ""
    gemini_api_key: str = ""  # For fidelity checking
    
    # LLM Configuration
    llm_model: str = "gpt-3.5-turbo"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 500
    
    # Embedding Model
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # Vector Store Configuration
    vector_store_type: str = "pinecone" # "chromadb" or "pinecone"
    vector_store_path: str = "./chroma_db"  # Only used if vector_store_type is "chromadb"
    pinecone_api_key: str = ""
    pinecone_index_name: str = "news-summarizer"

    # Database Configuration
    database_path: str = "./data/news_cache.db"
    
    # News API Configuration
    news_api_sources: str = "bbc-news,cnn,reuters,the-verge,techcrunch,wired"
    news_api_language: str = "en"
    news_api_page_size: int = 20
    
    # Retrieval Configuration
    top_k_results: int = 5
    similarity_threshold: float = 0.7
    
    # Application Settings
    debug: bool = False
    log_level: str = "INFO"
    
    def validate_api_keys(self) -> bool:
        """Check if required API keys are set."""
        missing_keys = []
        
        if not self.openai_api_key:
            missing_keys.append("OPENAI_API_KEY")
        if not self.newsapi_key:
            missing_keys.append("NEWSAPI_KEY")
        
        if missing_keys:
            print(f"⚠️  Warning: Missing API keys: {', '.join(missing_keys)}")
            print("Please set them in your .env file")
            return False
        
        return True
    
    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        directories = [
            Path(self.database_path).parent,
        ]
        
        # Only create vector store directory if using ChromaDB
        if self.vector_store_type == "chromadb":
            directories.append(Path(self.vector_store_path))
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            if self.debug:
                print(f"✓ Ensured directory exists: {directory}")


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


if __name__ == "__main__":
    # Test configuration loading
    print("=== Configuration Test ===")
    print(f"LLM Model: {settings.llm_model}")
    print(f"Embedding Model: {settings.embedding_model}")
    print(f"Vector Store Type: {settings.vector_store_type}")
    print(f"Database Path: {settings.database_path}")
    print(f"Debug Mode: {settings.debug}")
    print("\n=== API Key Validation ===")
    settings.validate_api_keys()
    print("\n=== Directory Setup ===")
    settings.ensure_directories()
