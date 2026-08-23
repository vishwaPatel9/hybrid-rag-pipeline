import json
import os
import pandas as pd
import sys

# Ensure we can import from the root directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval.hybrid_search import hybrid_search

def run_evaluation_harness(queries_file: str, output_csv: str):
    """
    Automated evaluation harness to test Retrieval Recall.
    Matches the 'lightweight evaluation harnesses' requirement from the JD.
    """
    print(f"Starting Evaluation Harness using {queries_file}...")
    
    with open(queries_file, 'r', encoding='utf-8') as f:
        test_cases = json.load(f)
        
    results = []
    
    for idx, test in enumerate(test_cases):
        query = test['query']
        expected_ids = test.get('expected_article_ids', [])
        
        try:
            # Run hybrid search
            retrieved_chunks = hybrid_search(query, top_k=5)
            # Extract UUIDs (assuming the chunk dictionary has an 'id' or we parse it from metadata)
            # Since chunk schema varies, we safely fallback to an empty string if id is missing
            retrieved_uuids = [str(chunk.get('id', '')) for chunk in retrieved_chunks]
            
            # Calculate Recall
            found_expected = any(eid in retrieved_uuids for eid in expected_ids)
        except Exception as e:
            print(f"Error evaluating query {idx+1}: {e}")
            retrieved_uuids = []
            found_expected = False
            
        results.append({
            "test_id": idx + 1,
            "query": query,
            "expected_uuids": ", ".join(expected_ids),
            "retrieved_uuids": ", ".join(retrieved_uuids),
            "pass": found_expected
        })
        
        print(f"Test {idx+1}: {'PASS' if found_expected else 'FAIL'} - {query[:50]}...")
        
    df_results = pd.DataFrame(results)
    
    # Calculate overall metrics
    pass_rate = df_results['pass'].mean() * 100
    print(f"\n--- Evaluation Complete ---")
    print(f"Total Tests: {len(test_cases)}")
    print(f"Overall Recall (Top-5): {pass_rate:.2f}%")
    
    df_results.to_csv(output_csv, index=False)
    print(f"Detailed report saved to {output_csv}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    queries_path = os.path.join(base_dir, "evaluation", "eval_queries.json")
    output_path = os.path.join(base_dir, "evaluation", "eval_report.csv")
    
    if os.path.exists(queries_path):
        run_evaluation_harness(queries_path, output_path)
    else:
        print("eval_queries.json not found. Cannot run harness.")
