"""
Benchmark Evaluation Runner
Executes the TigerGraph Fraud Investigation Agent across all 20 benchmark cases (HHG-001 to HHG-020),
validates schema compliance, and writes deliverables into cases/<case_id>.json.
"""

import os
import sys
import json
import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tigergraph.client import TigerGraphClient
from agent.investigator import FraudInvestigationAgent


def run_benchmark():
    print("=================================================================")
    print("  TigerGraph Agentic Fraud Investigation - Benchmark Runner")
    print("=================================================================\n")

    data_dir = "data"
    cases_dir = "cases"
    os.makedirs(cases_dir, exist_ok=True)

    # Initialize Graph Client & Agent
    tg_client = TigerGraphClient(data_dir=data_dir)
    agent = FraudInvestigationAgent(tg_client=tg_client)

    # Load 20 benchmark cases
    cases_csv_path = os.path.join(data_dir, "case_pack.csv")
    cases_df = pd.read_csv(cases_csv_path)
    print(f"Loaded {len(cases_df)} benchmark cases from {cases_csv_path}.\n")

    summary_records = []

    for idx, row in cases_df.iterrows():
        case_id = row["case_id"]
        print(f"[{idx+1:02d}/20] Investigating {case_id} (Trigger: {row['trigger_type']}) on card {row['card_id']}...")
        
        # Run autonomous agent investigation
        result = agent.investigate_case(row.to_dict())

        # Save to cases/<case_id>.json
        out_path = os.path.join(cases_dir, f"{case_id}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        case_obj = result["case"]
        nba = result["next_best_actions"]
        sar = result["sar"]

        summary_records.append({
            "case_id": case_id,
            "verdict": case_obj["verdict"],
            "prob": case_obj["fraud_probability"],
            "pattern": case_obj["pattern"],
            "exposure": case_obj["exposure_usd"],
            "initial_actions": [a["action"] for a in nba["initial"]],
            "final_actions": [a["action"] for a in nba["final"]],
            "sar_filed": sar["file"],
            "tool_calls": result["tool_calls"],
            "latency_s": result["latency_s"]
        })

    print("\n=================================================================")
    print("                    BENCHMARK RESULTS SUMMARY                     ")
    print("=================================================================")
    summary_df = pd.DataFrame(summary_records)
    print(summary_df.to_string(index=False))

    print(f"\nSuccessfully generated all 20 case files in '{cases_dir}/'.")


if __name__ == "__main__":
    run_benchmark()
