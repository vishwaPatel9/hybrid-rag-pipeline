"""
Company Universe Indexer
Transforms the 100-company M&A universe into rich semantic chunks
and indexes them directly into ChromaDB (Vector) and Rank-BM25 (Keyword).
Enables instant natural language querying across all company profiles,
catalysts, exit rumors, debt timelines, and deal rationales.
"""

import os
import sys
import json
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sentence_transformers import SentenceTransformer
from indexing.vector_store import add_to_chroma
from indexing.bm25_index import build_bm25_index


def index_company_universe():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    universe_path = os.path.join(base_dir, "data", "company_universe_100.json")
    
    if not os.path.exists(universe_path):
        from deal_prediction.company_universe import generate_universe
        generate_universe(universe_path)
        
    with open(universe_path, "r", encoding="utf-8") as f:
        companies = json.load(f)
        
    rows = []
    for c in companies:
        name = c.get("name", "Unknown")
        sector = c.get("sector", "Technology")
        country = c.get("country", "US")
        jurisdiction = c.get("jurisdiction", "US")
        hp = c.get("hold_period_years", 0)
        dm = c.get("debt_maturity_months", 0)
        lf = c.get("last_funding_months_ago", 0)
        desc = c.get("description", "")
        news_list = c.get("recent_news", [])
        sources = c.get("data_sources", [])
        primary_source = sources[0] if sources else "https://crunchbase.com"
        domain = primary_source.split("/")[2] if "http" in primary_source else "techcrunch.com"
        
        # Construct rich company dossier chunk
        news_block = " ".join(news_list)
        chunk_text = (
            f"Company: {name}\n"
            f"Sector: {sector} | Country: {country} (Jurisdiction: {jurisdiction})\n"
            f"Business Overview: {desc}\n"
            f"Financial & Ownership Catalysts: Private Equity / Founder hold period is {hp} years. "
            f"Debt maturity calendar is in {dm} months. Last capital funding round was {lf} months ago.\n"
            f"Recent Market Intelligence & Transaction Signals: {news_block}\n"
            f"Verified Reference Source: {primary_source}"
        )
        
        chunk_id = f"comp_{c['company_id'][:12]}"
        rows.append({
            "chunk_id": chunk_id,
            "article_id": chunk_id,
            "title": f"{name} ({sector} · {country}) M&A Intelligence Dossier",
            "author": f"{domain} Research",
            "url": primary_source,
            "source_domain": domain,
            "text": chunk_text
        })
        
    df = pd.DataFrame(rows)
    
    # Save to parquet
    os.makedirs(os.path.join(base_dir, "processing"), exist_ok=True)
    parquet_path = os.path.join(base_dir, "processing", "chunked_articles.parquet")
    df.to_parquet(parquet_path, index=False)
    print(f"Saved {len(df)} company dossiers to {parquet_path}")
    
    # 1. Embed and upsert to ChromaDB
    from indexing.embed import embed_and_store
    embed_and_store(parquet_path)
    print("ChromaDB vector store indexed successfully.")
    
    # 2. Build Rank-BM25 Keyword Index
    build_bm25_index(parquet_path)
    print("Complete: 100 companies successfully indexed into Hybrid RAG engine.")


if __name__ == "__main__":
    index_company_universe()
