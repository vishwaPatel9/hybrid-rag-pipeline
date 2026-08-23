import os
import pickle
from indexing.vector_store import get_collection
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BM25_INDEX_PATH = os.path.join(BASE_DIR, "data", "bm25_index.pkl")

# Lazy-loaded to prevent OOM during test collection
_embed_model = None

def _get_embed_model():
    global _embed_model
    if _embed_model is None:
        _embed_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    return _embed_model


def get_bm25_results(query, top_k=20):
    try:
        with open(BM25_INDEX_PATH, 'rb') as f:
            data = pickle.load(f)
    except FileNotFoundError:
        print("BM25 index not found. Run bm25_index.py first.")
        return []
        
    bm25 = data["bm25"]
    ids = data["ids"]
    
    tokenized_query = query.lower().split()
    doc_scores = bm25.get_scores(tokenized_query)
    
    scored_docs = list(zip(ids, doc_scores))
    scored_docs.sort(key=lambda x: x[1], reverse=True)
    
    return [doc[0] for doc in scored_docs[:top_k]]

def get_vector_results(query, top_k=20):
    collection = get_collection()
    query_embedding = _get_embed_model().encode([query]).tolist()
    
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k
    )
    if not results['ids']:
        return [], [], []
    return results['ids'][0], results['documents'][0], results['metadatas'][0]

def reciprocal_rank_fusion(vector_ids, bm25_ids, k=60):
    rrf_scores = {}
    
    for rank, doc_id in enumerate(vector_ids):
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (k + rank + 1)
        
    for rank, doc_id in enumerate(bm25_ids):
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (k + rank + 1)
        
    sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
    return sorted_ids

def hybrid_search(query, top_k=20):
    print(f"Executing hybrid search for: '{query}'")
    bm25_top_ids = get_bm25_results(query, top_k=50)
    vector_top_ids, docs, metas = get_vector_results(query, top_k=50)
    
    doc_meta_map = {}
    for vid, doc, meta in zip(vector_top_ids, docs, metas):
        doc_meta_map[vid] = {"text": doc, "metadata": meta}
        
    fused_ids = reciprocal_rank_fusion(vector_top_ids, bm25_top_ids)
    final_ids = fused_ids[:top_k]
    
    missing_ids = [did for did in final_ids if did not in doc_meta_map]
    if missing_ids:
        collection = get_collection()
        missing_res = collection.get(ids=missing_ids)
        if missing_res and missing_res['ids']:
            for did, doc, meta in zip(missing_res['ids'], missing_res['documents'], missing_res['metadatas']):
                doc_meta_map[did] = {"text": doc, "metadata": meta}
            
    final_results = []
    for did in final_ids:
        if did in doc_meta_map:
            final_results.append({
                "id": did,
                "text": doc_meta_map[did]["text"],
                "metadata": doc_meta_map[did]["metadata"]
            })
            
    return final_results
