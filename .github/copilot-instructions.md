# AI Coding Guidelines for Sellica Techwear Assistant

## Project Overview
Sellica is a RAG (Retrieval-Augmented Generation) system that powers a bilingual (English/Uzbek) AI assistant for a techwear shop. The system retrieves relevant product information using vector similarity search and generates contextual responses via Groq API.

## Core Architecture
- **Data Flow**: GitHub repo → Vectorization → Search → Prompt Building → AI Generation
- **Key Components**: `DocumentSearch` (vector similarity), `PromptBuilder` (language-aware prompts), `GroqClient` (Llama 3.3 70B), `DataManager` (async caching)
- **Storage**: JSONL files with 1024-D embeddings using BAAI/bge-m3 model

## Critical Patterns

### Vector Operations
- Use MPS device for M4 GPU acceleration: `torch.backends.mps.is_available()`
- Normalize embeddings during encoding: `normalize_embeddings=True`
- Batch processing for efficiency: `batch_size=32`

### Language Handling
- Detect Uzbek queries using keywords: `['bor', 'nima', 'qancha', 'nech', 'salom', 'mi', 'uchun']`
- Select context based on detected language (English vs Uzbek fields)
- Maintain bilingual product data structure: `{"search_en": "...", "context_uz": "..."}`

### Token Optimization
- Filter search results by score threshold (default: 0.32)
- Include only relevant language context in prompts
- Use compact prompt format: `System prompt\n\n<ctx>\n{context}\n</ctx>\n\nU: {query}\nA:`

### Async Data Management
- Cache searchers in memory with access-time tracking
- Auto-cleanup inactive data after 60 seconds
- Load from GitHub on cold start, persist to local `temp_vault/`

## Development Workflows

### Data Ingestion
```bash
python modules/full_ingest.py  # Pull from GitHub, vectorize, save to data/vectors.jsonl
```

### Testing
```bash
python modules/test_manager.py  # Test async loading, caching, cleanup
python -m modules.test_manager  # Alternative test runner
```

### Environment Setup
- Copy `.env` with required keys: `GROQ_API_KEY`, `TELEGRAM_TOKEN`, `GITHUB_TOKEN`
- Set `DEBUG_MODE=true` for detailed logging
- Install dependencies: `pip install sentence-transformers torch groq python-telegram-bot requests python-dotenv`

## Code Conventions

### Module Structure
- Place new modules in `modules/` directory
- Import pattern: `from modules.{module} import {Class}`
- Use relative paths for data files: `os.path.join(base_dir, "data", "vectors.jsonl")`

### Error Handling
- Check file existence before operations
- Validate API keys on initialization
- Graceful fallbacks for missing data

### Debugging
- Wrap debug prints with `if DEBUG_MODE:`
- Include token usage stats in AI responses
- Log vector shapes and similarity scores

## Integration Points

### Telegram Bot
- Reuse RAG components (`searcher`, `prompt_engine`, `ai`)
- Handle async message processing
- Match main.py flow exactly

### GitHub Data Source
- Repo: `frey50/DATAINC`
- Path structure: `Datasets/{shop_id}/`
- Support JSON/JSONL files only

### External APIs
- Groq: Llama 3.3 70B versatile model
- Temperature: 0.6, Max tokens: 1024
- Stream: false for synchronous responses

## Performance Considerations
- Vectorize once, search many times
- Cache embeddings on GPU memory
- Limit context to top 3 results
- Monitor prompt token ratios (<80% ideal)

## File Reference Examples
- Vector database: `data/vectors.jsonl`
- Configuration: `config.py` (loads from `.env`)
- Main entry: `main.py` (CLI interface)
- Bot interface: `modules/telegram_bot.py`