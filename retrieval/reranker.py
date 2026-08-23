from sentence_transformers import CrossEncoder

# Lazy-loaded to avoid OOM during test collection and module import
_reranker_model = None

def _get_reranker():
    global _reranker_model
    if _reranker_model is None:
        _reranker_model = CrossEncoder('cross-encoder/mmarco-mMiniLMv2-L12-H384-v1')
    return _reranker_model

def rerank_results(query, retrieved_docs, top_k=5):
    if not retrieved_docs:
        return []

    print(f"Reranking {len(retrieved_docs)} candidates using Cross-Encoder...")

    model = _get_reranker()
    # CrossEncoder expects list of (query, document) pairs
    pairs = [[query, doc['text']] for doc in retrieved_docs]
    scores = model.predict(pairs)

    for doc, score in zip(retrieved_docs, scores):
        doc['rerank_score'] = float(score)

    reranked_docs = sorted(retrieved_docs, key=lambda x: x['rerank_score'], reverse=True)
    return reranked_docs[:top_k]
