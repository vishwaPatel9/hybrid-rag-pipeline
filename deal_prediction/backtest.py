"""
Historical Backtest Engine
Evaluates the deal prediction pipeline on historical 2020 data
and benchmarks predictions against verified 2021 M&A transaction outcomes.
Calculates Precision (Hit Rate), Recall (Coverage), F1 Score, and Confusion Matrix.
"""

import os
import json
import sys
from typing import Dict, Any, Optional

# Ensure deal_prediction module can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from deal_prediction.pipeline import run_deal_prediction_pipeline


def run_historical_backtest(
    data_path: Optional[str] = None,
    top_pct: float = 0.5,
    country_filter: Optional[list] = None
) -> Optional[Dict[str, Any]]:
    """
    Runs the full 5-stage pipeline on the 2020 benchmark dataset
    and calculates statistical validation metrics against realized 2021 outcomes.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not data_path:
        data_path = os.path.join(base_dir, "data", "backtest_2020.json")

    if not os.path.exists(data_path):
        print(f"Backtest dataset not found at {data_path}. Running backtest_data.py...")
        from deal_prediction.backtest_data import generate_backtest_dataset
        generate_backtest_dataset(data_path)

    with open(data_path, "r", encoding="utf-8") as f:
        all_companies = json.load(f)

    # Filter if needed
    if country_filter:
        all_companies = [c for c in all_companies if c.get("country") in country_filter or c.get("jurisdiction") in country_filter]

    # Run the pipeline on the historical dataset
    ranked_results = run_deal_prediction_pipeline(
        all_companies,
        top_pct=top_pct,
        country_filter=country_filter
    )

    # Ground truth evaluation
    actual_acquired_ids = set(c["company_id"] for c in all_companies if c.get("actual_ma_in_2021"))
    predicted_target_ids = set(c["company_id"] for c in ranked_results)

    true_positives = predicted_target_ids.intersection(actual_acquired_ids)
    false_positives = predicted_target_ids - actual_acquired_ids
    false_negatives = actual_acquired_ids - predicted_target_ids
    true_negatives = len(all_companies) - len(actual_acquired_ids) - len(false_positives)

    precision = len(true_positives) / len(predicted_target_ids) if predicted_target_ids else 0.0
    recall = len(true_positives) / len(actual_acquired_ids) if actual_acquired_ids else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    print("=== HISTORICAL BACKTEST VALIDATION REPORT ===")
    print(f"Total Universe Size: {len(all_companies)}")
    print(f"Actual 2021 M&A Realized Outcomes: {len(actual_acquired_ids)}")
    print(f"Model Predicted Targets (Top {int(top_pct*100)}% slice): {len(predicted_target_ids)}")
    print(f"True Positives (Correct Predictions): {len(true_positives)}")
    print(f"False Positives: {len(false_positives)}")
    print(f"Precision (Hit Rate): {precision * 100:.1f}%")
    print(f"Recall (Deal Coverage): {recall * 100:.1f}%")
    print(f"F1 Calibration Score: {f1:.3f}")

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "true_positives": len(true_positives),
        "false_positives": len(false_positives),
        "false_negatives": len(false_negatives),
        "true_negatives": true_negatives,
        "total_universe": len(all_companies),
        "total_actual": len(actual_acquired_ids),
        "total_predicted": len(predicted_target_ids),
        "predictions": ranked_results
    }


if __name__ == "__main__":
    run_historical_backtest()
