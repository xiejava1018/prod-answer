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

## Development Commands

### Backend (Django)

```bash
cd backend

# Environment setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Database operations
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Run tests
python manage.py test

# Django Admin
# Access at http://localhost:8000/admin/
```

**Important:** This project requires PostgreSQL with pgvector extension for production. For testing, set `USE_SQLITE=True` to use SQLite (vector operations will be degraded).

### Frontend (Vue 3 + TypeScript)

```bash
cd frontend

# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

Frontend dev server runs on http://localhost:5173 and proxies `/api` requests to backend on port 8000.

### Database Setup (PostgreSQL)

```bash
# Create database
createdb prod_answer

# Enable pgvector extension
psql -d prod_answer -c "CREATE EXTENSION vector;"
```

## Architecture

### Backend Structure (Django Apps)

The backend follows a **modular Django apps architecture**:

- **`apps/core/`** - Base models (TimeStampedModel), shared utilities
- **`apps/products/`** - Product and Feature models with hierarchical structure support
- **`apps/embeddings/`** - Multi-provider AI embedding services (OpenAI, HuggingFace, custom)
- **`apps/matching/`** - Semantic similarity matching algorithms and cosine similarity calculations
- **`apps/requirements/`** - File parsing (Excel, CSV, Word) and requirement extraction
- **`apps/reports/`** - Report generation and export functionality

**Key Patterns:**
- **Provider Pattern** - Extensible embedding providers in `apps/embeddings/providers/`
- **Strategy Pattern** - Pluggable matching algorithms in `apps/matching/services.py`
- **Factory Pattern** - Service instantiation (e.g., `EmbeddingServiceFactory`)
- **Parser Pattern** - File parsers in `apps/requirements/parsers/` (base.py, csv_parser.py, excel_parser.py, word_parser.py)

**Database Models:**
- `Product` - Products with metadata, category, and subsystem_type
- `Feature` - Hierarchical features with VectorField for embeddings
- `Requirement` - User requirements from text or file uploads
- `EmbeddingModelConfig` - AI model configurations (OpenAI, local models)
- `MatchResult` - Matching results with similarity scores

### Frontend Structure (Vue 3)

- **`src/api/`** - Axios API client with typed interfaces
- **`src/views/`** - Vue components (Composition API with `<script setup>`)
- **`src/store/`** - Pinia state management
- **`src/router/`** - Vue Router configuration
- **`src/utils/`** - Utility functions

**Key Features:**
- Auto-imports for Vue components and composables (unplugin-auto-import)
- Element Plus UI library with auto-registration
- TypeScript with strict typing
- Vite for fast development and optimized builds

### API Endpoints

All APIs are prefixed with `/api/v1/`:

**Products:**
- `GET /api/v1/products/` - List products (with filtering, search, pagination)
- `POST /api/v1/products/` - Create product
- `GET /api/v1/products/{id}/` - Product detail
- `GET /api/v1/products/{id}/features/` - List features
- `POST /api/v1/products/{id}/features/` - Add feature

**Embeddings:**
- `GET /api/v1/embeddings/configs/` - List embedding model configs
- `POST /api/v1/embeddings/configs/` - Create config
- `POST /api/v1/embeddings/test-connection/{id}/` - Test API connectivity
- `POST /api/v1/embeddings/generate-batch/` - Batch generate embeddings

**Requirements:**
- `POST /api/v1/requirements/` - Create requirement (text or file)
- `GET /api/v1/requirements/{id}/` - Get requirement detail

**Matching:**
- `POST /api/v1/matching/analyze` - Run matching analysis
- `GET /api/v1/matching/results/{req_id}/` - Get match results

**Reports:**
- `POST /api/v1/reports/export/` - Export report (Excel/CSV/PDF)

## Configuration

### Environment Variables (.env)

Required in backend directory:

```bash
# Database
DB_NAME=prod_answer
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# OpenAI (optional - for OpenAI embeddings)
OPENAI_API_KEY=your-api-key

# Celery (optional - for async tasks)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Encryption
ENCRYPTION_KEY=your-encryption-key
```

### Django Settings

Settings are split by environment:
- `config/settings/base.py` - Common settings
- `config/settings/development.py` - Development overrides
- `config/settings/production.py` - Production overrides
- `config/settings/test.py` - Test configuration

**Key configurations:**
- Language: `zh-hans` (Chinese)
- Timezone: `Asia/Shanghai`
- REST Framework: Session authentication, pagination, filtering
- CORS: Allows frontend on localhost:5173
- Logging: Console + file (logs/django.log)

## Adding New Features

### New Embedding Provider

1. Create provider class in `apps/embeddings/providers/`:
```python
from apps.embeddings.providers.base import BaseEmbeddingProvider

class MyProvider(BaseEmbeddingProvider):
    def encode(self, texts):
        # Return list of vectors
        pass

    def test_connection(self):
        # Test API connectivity
        pass
```

2. Register in factory (check `apps/embeddings/services.py`)

### New File Parser

1. Create parser in `apps/requirements/parsers/`:
```python
from apps.requirements.parsers.base import BaseFileParser

class MyParser(BaseFileParser):
    def parse(self, file_path):
        # Return list of requirement texts
        pass
```

2. Register in `apps/requirements/services.py`

### Frontend Component

- Use `<script setup lang="ts">` with Composition API
- Components are auto-imported (no manual imports needed)
- Use Element Plus components directly
- API calls go through `src/api/` with typed interfaces

## Important Notes

- **PostgreSQL + pgvector** is required for full vector search functionality
- **SQLite fallback** exists for testing but with degraded features
- **Chinese language** support is enabled (`LANGUAGE_CODE='zh-hans'`)
- **Session authentication** is used (JWT planned for future)
- **Celery** is optional but recommended for async embedding generation
- **Logging** is configured to both console and `backend/logs/django.log`

## Troubleshooting

**Python version compatibility:** Use Python 3.11 or 3.12 (Python 3.14 may have dependency issues)

**pgvector issues:** Ensure extension is enabled: `psql -d prod_answer -c "CREATE EXTENSION vector;"`

**CORS errors:** Check `CORS_ALLOWED_ORIGINS` in `config/settings/base.py`

**Embedding failures:** Verify API keys in Django Admin or environment variables

## Testing

The project has minimal test coverage. Tests can be run with:
```bash
# Backend
cd backend
python manage.py test

# Frontend (not configured yet)
cd frontend
npm run test  # Not set up
```

## Documentation

- `README.md` - Project overview and setup
- `docs/STARTUP_GUIDE.md` - Detailed startup instructions
- `docs/API.md` - Complete API documentation
- `docs/EMBEDDING_GUIDE.md` - AI/ML configuration guide
- `docs/SUPABASE_MIGRATION_GUIDE.md` - Database migration instructions
