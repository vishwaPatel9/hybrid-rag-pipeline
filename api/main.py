import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from ingestion.scraper import scrape_urls
from retrieval.hybrid_search import hybrid_search
from retrieval.reranker import rerank_results
from generation.rag_pipeline import generate_answer
from generation.citation_validator import validate_citations
from generation.contradiction_detector import detect_contradictions

app = FastAPI(
    title="Third Bridge Intelligence Engine",
    description="Ingest any URL, then query it with AI-powered hybrid search and Gemini generation.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class IngestRequest(BaseModel):
    urls: List[str] = []

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    check_contradictions: bool = True

class QueryResponse(BaseModel):
    answer: str
    citations_valid: bool
    hallucination_message: str
    contradictions: List[dict]
    retrieved_chunks: List[dict]


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "2.0.0"}


@app.post("/ingest")
def trigger_ingestion(background_tasks: BackgroundTasks, req: IngestRequest = IngestRequest()):
    """Scrape a list of URLs and index them into ChromaDB."""
    from processing.advanced_cleaner import advanced_clean_pipeline
    from processing.chunker import process_chunks
    from indexing.embed import embed_and_store
    from indexing.bm25_index import build_bm25_index
    import pandas as pd

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_json = os.path.join(base_dir, "ingestion", "raw_articles.json")
    cleaned = os.path.join(base_dir, "processing", "cleaned_articles.parquet")
    chunked = os.path.join(base_dir, "processing", "chunked_articles.parquet")

    def run_pipeline():
        if not req.urls:
            return
        articles = scrape_urls(req.urls)
        with open(raw_json, "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=4)
        df_raw = pd.DataFrame(articles)
        df_clean = advanced_clean_pipeline(df_raw)
        df_clean.to_parquet(cleaned, index=False)
        process_chunks(cleaned, chunked)
        embed_and_store(chunked)
        build_bm25_index(chunked)

    background_tasks.add_task(run_pipeline)
    return {"message": f"Ingestion started for {len(req.urls)} URL(s). Processing in background."}


@app.post("/query", response_model=QueryResponse)
def run_query(req: QueryRequest):
    retrieved = hybrid_search(req.query, top_k=20)
    reranked = rerank_results(req.query, retrieved, top_k=req.top_k)

    answer = generate_answer(req.query, reranked)
    validation = validate_citations(answer, reranked)

    contradictions = []
    if req.check_contradictions:
        contradictions = detect_contradictions(req.query, reranked)

    return QueryResponse(
        answer=answer,
        citations_valid=validation['all_valid'],
        hallucination_message=validation['message'],
        contradictions=contradictions,
        retrieved_chunks=reranked
    )
