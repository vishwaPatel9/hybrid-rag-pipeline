import os
import pickle
import pandas as pd
from rank_bm25 import BM25Okapi

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BM25_INDEX_PATH = os.path.join(BASE_DIR, "data", "bm25_index.pkl")

def build_bm25_index(chunked_file):
    print(f"Loading chunks from {chunked_file}...")
    df = pd.read_parquet(chunked_file)
    
    texts = df['text'].tolist()
    print("Tokenizing corpus for BM25...")
    tokenized_corpus = [doc.lower().split() for doc in texts]
    
    print("Building BM25 index...")
    bm25 = BM25Okapi(tokenized_corpus)
    
    os.makedirs(os.path.dirname(BM25_INDEX_PATH), exist_ok=True)
    with open(BM25_INDEX_PATH, 'wb') as f:
        pickle.dump({
            "bm25": bm25,
            "ids": df['chunk_id'].tolist(),
            "corpus": texts
        }, f)
        
    print(f"BM25 index saved to {BM25_INDEX_PATH}")

if __name__ == "__main__":
    chunked_file = os.path.join(BASE_DIR, "processing", "chunked_articles.parquet")
    build_bm25_index(chunked_file)
