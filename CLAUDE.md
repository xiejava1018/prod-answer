# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Product Capability Matching System** (产品能力匹配系统) - an AI-powered semantic matching platform that compares user requirements against product feature databases using vector embeddings and similarity search.

**Core Workflow:**
1. Products are defined with hierarchical features/capabilities
2. Features are converted to vector embeddings using AI models (OpenAI/Sentence-Transformers)
3. User requirements are extracted from documents (Excel, CSV, Word) or text input
4. Requirements are matched against features using cosine similarity
5. Results are classified as: matched (≥0.85), partial (0.75-0.85), or unmatched (<0.75)

**Tech Stack:**
- **Backend:** Django 4.2 + DRF + PostgreSQL with pgvector
- **Frontend:** Vue 3 + TypeScript + Element Plus + Pinia
- **AI/ML:** OpenAI API, Sentence-Transformers, Celery for async tasks

## Development Commands

### Backend (Django)

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Environment setup
cp .env.example .env
# Edit .env with your database and API keys

# Database setup (PostgreSQL with pgvector)
createdb prod_answer
psql -d prod_answer -c "CREATE EXTENSION vector;"

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Initialize embedding configuration (creates default embedding model)
python manage.py init_embedding_config

# Run development server
python manage.py runserver

# Run with specific settings module
DJANGO_SETTINGS_MODULE=config.settings.testing python manage.py test

# Testing with SQLite (for CI/fast tests)
USE_SQLITE=True DJANGO_SETTINGS_MODULE=config.settings.testing python manage.py test
```

### Frontend (Vue 3)

```bash
cd frontend

# Install dependencies
npm install

# Development server
npm run dev

# Type check + Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

### Database Operations

```bash
# Access PostgreSQL
psql -d prod_answer

# Check pgvector extension
SELECT * FROM pg_extension WHERE extname = 'vector';

# Reset database (WARNING: deletes all data)
DROP DATABASE prod_answer;
CREATE DATABASE prod_answer;
\c prod_answer
CREATE EXTENSION vector;
```

## Architecture

### Backend Structure

```
backend/
├── config/                  # Django configuration
│   ├── settings/           # Environment-specific settings
│   │   ├── base.py         # Base settings
│   │   ├── development.py  # Dev overrides
│   │   ├── production.py   # Production overrides
│   │   └── testing.py      # Test settings
│   └── urls.py             # Root URL configuration
├── apps/
│   ├── core/               # Base models (TimeStampedModel)
│   ├── products/           # Product & Feature management
│   ├── embeddings/         # Embedding service & provider factory
│   ├── matching/           # Matching algorithm & processing
│   ├── requirements/       # Requirements & file parsing
│   └── reports/            # Report generation
└── manage.py
```

### Core Concepts

**1. Embedding Provider Factory Pattern**
- `EmbeddingServiceFactory` (apps/embeddings/services.py) manages multiple embedding providers
- Supported providers: OpenAI, Sentence-Transformers, OpenAI-compatible (SiliconFlow, ZhipuAI, Qwen)
- New providers can be registered via `register_provider()`
- Provider instances are cached by config ID

**2. Matching Algorithm**
- Uses cosine similarity on pgvector embeddings
- Threshold-based classification:
  - **Full match**: ≥ 0.85
  - **Partial match**: 0.75 - 0.85
  - **No match**: < 0.75
- Thresholds are configurable per-request

**3. File Parser Architecture**
- `FileParserService` supports Excel, CSV, Word files
- Each parser inherits from `BaseFileParser`
- Mapped by MIME type in `PARSERS` dictionary
- Auto-detects file type by extension

**4. Product Hierarchy**
- Products can have `subsystem_type` (asset_mapping, exposure_mapping, big_data, soar, etc.)
- Features have hierarchical levels: `level1_function` → `level2_function` → `level3_function`
- Features include `indicator_type` (product_function, performance, security, etc.)
- `spec_metadata` JSON field stores technical parameters

### Frontend Structure

```
frontend/src/
├── api/              # API service layer (Axios instances)
├── components/       # Reusable Vue components
├── router/           # Vue Router configuration
├── store/            # Pinia stores
├── types/            # TypeScript type definitions
├── utils/            # Utility functions
└── views/            # Page components
```

## API Endpoints

Base URL: `http://localhost:8000/api/v1/`

**Products:**
- `GET /products/` - List products (filterable by subsystem_type, category)
- `POST /products/` - Create product
- `GET /products/{id}/features/` - List features
- `POST /products/{id}/features/` - Add feature

**Requirements:**
- `POST /requirements/` - Create requirement from text or file
- `GET /requirements/{id}/` - Get requirement details

**Matching:**
- `POST /matching/analyze` - Perform matching analysis
  ```json
  {
    "requirement_id": "uuid",
    "threshold": 0.75
  }
  ```
- `GET /matching/results/{req_id}/` - Get matching results

**Embeddings:**
- `GET /embeddings/configs/` - List embedding configurations
- `POST /embeddings/configs/` - Create configuration
- `POST /embeddings/test-connection/{id}/` - Test provider connection

## Configuration

### Embedding Models (Required for Semantic Matching)

Embedding models must be configured via Django Admin or API before matching works:

1. **Access Admin:** http://localhost:8000/admin
2. **Configure Model:**
   - Go to "Embedding Model Configs"
   - Create config with:
     - `provider`: openai, sentence-transformers, openai-compatible, siliconflow, zhipuai, qwen
     - `model_name`: e.g., "text-embedding-3-small"
     - `dimension`: 1536 for OpenAI, 384 for all-MiniLM-L6-v2
     - `is_default`: true
     - `api_key_encrypted`: API key (encrypted at rest)

3. **Or use management command:**
   ```bash
   python manage.py init_embedding_config
   ```

### Environment Variables

Key variables in `.env`:
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` - PostgreSQL config
- `OPENAI_API_KEY` - OpenAI API key
- `ENCRYPTION_KEY` - Fernet key for encrypting API keys
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` - Redis for Celery
- `SECRET_KEY` - Django secret key
- `DEBUG` - Debug mode (True/False)
- `ALLOWED_HOSTS` - Comma-separated hostnames

## Development Patterns

### Adding a New Embedding Provider

1. Create provider class in `apps/embeddings/providers/`:
   ```python
   from .base import BaseEmbeddingProvider

   class MyProvider(BaseEmbeddingProvider):
       def encode(self, texts):
           # Return list of embedding vectors
           pass
   ```

2. Register in `apps/embeddings/services.py`:
   ```python
   EmbeddingServiceFactory.register_provider('my-provider', MyProvider)
   ```

3. Add to `provider` field choices in `EmbeddingModelConfig` model

### Adding a New File Parser

1. Create parser in `apps/requirements/parsers/`:
   ```python
   from .base import BaseFileParser

   class MyParser(BaseFileParser):
       def parse(self, file_path):
           # Return list of requirement texts
           pass
   ```

2. Register in `apps/requirements/services.py`:
   ```python
   FileParserService.PARSERS['mime/type'] = MyParser
   ```

### Testing

- Use `USE_SQLITE=True` environment variable for faster tests with SQLite
- Test settings in `config/settings/testing.py`
- pgvector field becomes JSONField in SQLite mode
- See products/models.py:11-15 for conditional VectorField import

## Important Notes

- **pgvector Required:** System requires PostgreSQL with pgvector extension for production
- **Embedding Config:** Matching will fail without a configured embedding model
- **Async Processing:** Celery is configured but not strictly required for basic functionality
- **Chinese Language:** System defaults to `LANGUAGE_CODE='zh-hans'` and `TIME_ZONE='Asia/Shanghai'`
- **Media Uploads:** Files stored in `backend/media/uploads/`
- **CORS:** Frontend origins (localhost:5173, localhost:3000) pre-configured

## Common Issues

**"Unsupported provider type" error:**
→ Register new provider in `EmbeddingServiceFactory._providers`

**VectorField not found:**
→ Ensure pgvector extension is installed: `CREATE EXTENSION vector;`

**Embedding generation fails:**
→ Check API key configuration and test connection via admin or API

**Frontend can't reach backend:**
→ Check CORS settings in `config/settings/base.py` and ensure backend is running

**Migration conflicts:**
→ Run `python manage.py makemigrations --merge` if needed
