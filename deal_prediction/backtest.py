import os
import json
import sys

# Ensure we can import the pipeline
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from deal_prediction.pipeline import run_deal_prediction_pipeline

def run_historical_backtest():
    """
    Runs the pipeline on the historical 2020 dataset and calculates Precision/Recall.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "data", "historical_real_companies.json")
    
    if not os.path.exists(data_path):
        print("Historical dataset not found. Please run historical_real_data.py first.")
        return None
        
    print("=== STARTING REAL HISTORICAL BACKTEST ===")
    # We use top_pct=0.5 because our mini-dataset only has 10 companies.
    # Predicting the top 5 to see how many were actually acquired.
    results = run_deal_prediction_pipeline(data_path, top_pct=0.5)
    
    # The output 'results' contains the top N predicted companies.
    predicted_acquired_ids = set([c["company_id"] for c in results])
    
    # Load original data to find ground truth
    with open(data_path, 'r', encoding='utf-8') as f:
        all_companies = json.load(f)
        
    actual_acquired_ids = set([c["company_id"] for c in all_companies if c.get("actual_ma_in_2021")])
    
    true_positives = predicted_acquired_ids.intersection(actual_acquired_ids)
    
    precision = len(true_positives) / len(predicted_acquired_ids) if predicted_acquired_ids else 0
    recall = len(true_positives) / len(actual_acquired_ids) if actual_acquired_ids else 0
    
    print("\n=== BACKTEST RESULTS ===")
    print(f"Total Companies Evaluated: {len(all_companies)}")
    print(f"Total Actually Acquired: {len(actual_acquired_ids)}")
    print(f"Model Predicted Acquired (Funnel Top 50%): {len(predicted_acquired_ids)}")
    print(f"True Positives (Correct Predictions): {len(true_positives)}")
    print(f"Precision (Hit Rate): {precision * 100:.1f}%")
    print(f"Recall (Coverage): {recall * 100:.1f}%")
    
    return {
        "precision": precision,
        "recall": recall,
        "true_positives": len(true_positives),
        "total_predicted": len(predicted_acquired_ids),
        "total_actual": len(actual_acquired_ids),
        "predictions": results
    }

if __name__ == "__main__":
    run_historical_backtest()
