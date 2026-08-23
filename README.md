# Intelligence Engine 🔍

I built this project to see what it actually takes to build a Retrieval-Augmented Generation (RAG) pipeline from scratch. Most tutorials use perfectly clean datasets. I wanted to see what happens when you feed an LLM raw, messy web scraping output, and how to prevent it from hallucinating.

The result is a hybrid search pipeline that scrapes any website, cleans the data with Pandas, indexes it, and uses Gemini to generate cited answers while checking for contradictions.

## Architecture

Here is how the data flows through the system:

1. **Ingestion:** Uses `trafilatura` to scrape articles. It works on almost any website without needing custom CSS selectors.
2. **Cleaning:** A Pandas ETL pipeline (`advanced_cleaner.py`) that enforces schemas, handles missing values, and normalizes messy unicode text.
3. **Indexing:** Uses ChromaDB for vector storage and builds a local BM25 keyword index. It supports multiple languages out of the box.
4. **Retrieval:** A hybrid search approach. It runs vector and keyword searches in parallel, merges them using Reciprocal Rank Fusion, and then uses a HuggingFace Cross-Encoder to rerank the top candidates.
5. **Generation:** Passes the top context to Gemini Flash, prompting it to generate answers with strict inline UUID citations.
6. **Validation:** A citation validator checks the LLM output to make sure it only cited sources that actually exist in the context.
7. **Analysis:** A contradiction detector that asks Gemini to compare all the retrieved sources and flag if they disagree on anything.

## Project Structure

```text
.
├── ingestion/
│   ├── scraper.py              # Universal scraper without hardcoded CSS selectors
│   └── urls.txt                # Put target URLs here, one per line
├── processing/
│   ├── clean.py                # Basic Pandas pipeline
│   ├── advanced_cleaner.py     # Pandas cleaner for schema enforcement and missing values
│   └── chunker.py              # Generates 300-word chunks with 50-word overlap
├── indexing/
│   ├── embed.py                # Generates embeddings and upserts to ChromaDB
│   ├── vector_store.py         # ChromaDB wrapper
│   └── bm25_index.py           # BM25 keyword index builder
├── retrieval/
│   ├── hybrid_search.py        # Combines Vector and BM25 results
│   └── reranker.py             # HuggingFace Cross-Encoder for final ranking
├── generation/
│   ├── rag_pipeline.py         # Gemini generation logic
│   ├── citation_validator.py   # Checks for hallucinated citations
│   └── contradiction_detector.py # Finds disagreements between sources
├── evaluation/
│   ├── dashboard.py            # Streamlit UI for testing
│   ├── eval_harness.py         # Automated recall testing script
│   ├── metrics.py              # MRR and Recall scoring
│   └── eval_queries.json       # Test queries
├── api/
│   └── main.py                 # FastAPI server with health, ingest, and query routes
├── tests/
│   ├── test_api.py             # FastAPI integration tests
│   └── test_pipeline.py        # Data cleaning unit tests
├── Dockerfile
└── docker-compose.yml
```

## Setup

### 1. Environment Variables
Copy `.env.example` to `.env` and add your keys:
```text
GEMINI_API_KEY=your-key-here    # Required for generation and contradiction detection
```

### 2. Install Dependencies
```bash
python -m venv venv
venv\Scripts\activate          # On Windows
pip install -r requirements.txt
```

### 3. Run the Dashboard
```bash
python -m streamlit run evaluation/dashboard.py
```
Paste any URL in the sidebar, click **Execute Ingestion**, and then ask questions in the main chat interface.

### 4. Run the API Server
```bash
uvicorn api.main:app --reload
```
Available endpoints:
- `GET /health`: Checks if the server is alive.
- `POST /ingest`: Send `{"urls": ["https://..."]}` to scrape and index new URLs.
- `POST /query`: Send `{"query": "your question", "top_k": 5}` to run the pipeline.

### 5. Run Tests and Evaluation
```bash
# Run unit tests
python -m pytest tests/ -v

# Run the evaluation harness
python -m evaluation.eval_harness
```

### 6. Docker
```bash
docker-compose up --build
```

## Key Things I Learned Building This

1. **Data cleaning is everything.** I realized pretty quickly that feeding garbage text into an embedding model ruins the search results. The `advanced_cleaner.py` script ended up being one of the most important parts of the project just to enforce schemas and clean up weird unicode characters.
2. **Vector search isn't enough.** Semantic search is great, but it misses exact keywords like company names or specific product versions. Bolting on a BM25 index and merging the results gave me much better retrieval.
3. **API rate limits are annoying.** My first contradiction detector compared every source against every other source individually. It maxed out my API limits immediately. I had to rewrite it to process everything in a single batch prompt and return a JSON array.
4. **Testing matters.** The evaluation harness (`eval_harness.py`) was crucial. Without a way to automatically measure Recall@5, I had no idea if tweaking the chunk size or changing the embedding model was actually making the system better or worse.
