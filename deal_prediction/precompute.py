"""
Precomputes and caches baseline pipeline execution results
so the Streamlit dashboard loads high-fidelity predictions instantly,
while retaining live re-execution buttons.
"""

import os
import json
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from deal_prediction.pipeline import run_deal_prediction_pipeline
from deal_prediction.backtest import run_historical_backtest


def precompute_all():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    universe_path = os.path.join(base_dir, "data", "company_universe_100.json")
    backtest_path = os.path.join(base_dir, "data", "backtest_2020.json")
    
    print("1. Running pipeline on current 100-company universe...")
    with open(universe_path, "r", encoding="utf-8") as f:
        companies = json.load(f)
        
    current_predictions = run_deal_prediction_pipeline(companies, top_pct=0.5)
    
    out_current = os.path.join(base_dir, "data", "predictions_current_100.json")
    with open(out_current, "w", encoding="utf-8") as f:
        json.dump(current_predictions, f, indent=4, ensure_ascii=False)
    print(f"Saved {len(current_predictions)} predictions to {out_current}")
    
    print("\n2. Running backtest on 2020 historical dataset...")
    backtest_results = run_historical_backtest(backtest_path, top_pct=0.5)
    
    out_backtest = os.path.join(base_dir, "data", "backtest_results_2020.json")
    with open(out_backtest, "w", encoding="utf-8") as f:
        json.dump(backtest_results, f, indent=4, ensure_ascii=False)
    print(f"Saved backtest report to {out_backtest}")
    print("\nPrecomputation complete.")


if __name__ == "__main__":
    precompute_all()
