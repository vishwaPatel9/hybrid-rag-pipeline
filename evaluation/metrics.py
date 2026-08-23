import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval.hybrid_search import hybrid_search

def calculate_mrr(retrieved_ids, expected_ids):
    for i, rid in enumerate(retrieved_ids):
        if rid in expected_ids:
            return 1.0 / (i + 1)
    return 0.0

def calculate_recall_at_k(retrieved_ids, expected_ids, k=5):
    retrieved_at_k = retrieved_ids[:k]
    hits = sum(1 for eid in expected_ids if eid in retrieved_at_k)
    return hits / len(expected_ids) if expected_ids else 0.0

def calculate_precision_at_k(retrieved_ids, expected_ids, k=5):
    retrieved_at_k = retrieved_ids[:k]
    hits = sum(1 for rid in retrieved_at_k if rid in expected_ids)
    return hits / k if k > 0 else 0.0

def run_evaluation():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    queries_path = os.path.join(base_dir, "evaluation", "eval_queries.json")
    
    try:
        with open(queries_path, 'r') as f:
            eval_data = json.load(f)
    except FileNotFoundError:
        print("eval_queries.json not found.")
        return

    mrr_scores = []
    recall_scores = []
    precision_scores = []

    for item in eval_data:
        query = item['query']
        expected_ids = item['expected_article_ids']
        
        print(f"Evaluating: '{query}'")
        results = hybrid_search(query, top_k=20)
        
        # Extract the underlying article_id from the retrieved chunks
        retrieved_article_ids = [chunk['metadata'].get('article_id') for chunk in results]
        
        mrr = calculate_mrr(retrieved_article_ids, expected_ids)
        recall = calculate_recall_at_k(retrieved_article_ids, expected_ids, k=5)
        precision = calculate_precision_at_k(retrieved_article_ids, expected_ids, k=5)
        
        mrr_scores.append(mrr)
        recall_scores.append(recall)
        precision_scores.append(precision)

    avg_mrr = sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0
    avg_recall = sum(recall_scores) / len(recall_scores) if recall_scores else 0
    avg_precision = sum(precision_scores) / len(precision_scores) if precision_scores else 0

    print("\n--- RETRIEVAL EVALUATION METRICS ---")
    print(f"Mean Reciprocal Rank (MRR): {avg_mrr:.4f}")
    print(f"Average Recall@5:           {avg_recall:.4f}")
    print(f"Average Precision@5:        {avg_precision:.4f}")

if __name__ == "__main__":
    run_evaluation()
