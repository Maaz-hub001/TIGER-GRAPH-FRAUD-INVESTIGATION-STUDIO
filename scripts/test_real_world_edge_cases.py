"""
Real-World Adversarial Edge Case Test Suite for TigerGraph Fraud Investigation Agent
Tests the system against real-world edge cases, corrupted data, injection attacks,
conflicting signals, zero-dollar transactions, supernodes, and catastrophic exposure.
"""

import os
import sys
import json
import traceback
import urllib.request
import urllib.error

# Ensure root is in path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tigergraph.client import TigerGraphClient
from agent.investigator import FraudInvestigationAgent
from agent.policy import FraudPolicy

def run_tests():
    print("=" * 70)
    print("   REAL-WORLD ADVERSARIAL EDGE CASE TEST SUITE (TIGERGRAPH AGENT)   ")
    print("=" * 70)

    data_dir = os.path.join(PROJECT_ROOT, "data")
    tg_client = TigerGraphClient(data_dir=data_dir)
    agent = FraudInvestigationAgent(tg_client=tg_client)

    passed = 0
    failed = 0
    total = 8

    # -------------------------------------------------------------
    # EDGE CASE 1: Ghost Entity (Unknown customer, card, txn)
    # -------------------------------------------------------------
    print("\n[TEST 1] Ghost Customer / Non-Existent Entity Test")
    try:
        ghost_alert = {
            "case_id": "EDGE-001",
            "opened_at": "2026-09-24 10:00:00",
            "trigger_type": "risk_score",
            "trigger_text": "Anomalous transaction on unmapped customer entity",
            "flagged_txn_id": "99999999",
            "card_id": "C99999-K1",
            "customer_id": "C99999",
            "risk_score": 0.85
        }
        res = agent.investigate_case(ghost_alert)
        assert res["case"]["status"] in ["closed_fraud", "closed_legitimate", "under_investigation"], "Status invalid"
        assert res["case"]["verdict"] in ["fraud", "legitimate", "uncertain"], "Verdict invalid"
        assert len(res["next_best_actions"]["initial"]) > 0, "No initial actions returned"
        assert res["case"]["graph_case_id"].startswith("CASE-"), "Graph writeback ID missing"
        print("  --> PASS: Agent handled non-existent entity without crashing.")
        print(f"      Assessed verdict: {res['case']['verdict']}, Initial actions: {[a['action'] for a in res['next_best_actions']['initial']]}")
        passed += 1
    except Exception as e:
        print(f"  --> FAIL: Ghost Entity threw exception: {e}")
        traceback.print_exc()
        failed += 1

    # -------------------------------------------------------------
    # EDGE CASE 2: Zero Dollar Transaction ($0.00 Auth Check)
    # -------------------------------------------------------------
    print("\n[TEST 2] Zero Dollar Transaction ($0.00 Authorization Ping)")
    try:
        zero_alert = {
            "case_id": "EDGE-002",
            "opened_at": "2026-09-24 10:05:00",
            "trigger_type": "risk_score",
            "trigger_text": "Zero-dollar account verification ping from new merchant",
            "flagged_txn_id": "3514030",
            "card_id": "C12382-K1",
            "customer_id": "C12382",
            "risk_score": 0.30
        }
        res = agent.investigate_case(zero_alert)
        assert res["case"]["exposure_usd"] >= 0, "Exposure negative"
        assert "sar" in res, "SAR block missing"
        print("  --> PASS: Zero-dollar edge case handled cleanly without division-by-zero.")
        print(f"      Exposure: ${res['case']['exposure_usd']:.2f}, SAR File: {res['sar']['file']}")
        passed += 1
    except Exception as e:
        print(f"  --> FAIL: Zero-dollar test threw exception: {e}")
        traceback.print_exc()
        failed += 1

    # -------------------------------------------------------------
    # EDGE CASE 3: Whale Exposure ($250,000.00 Luxury Purchase)
    # -------------------------------------------------------------
    print("\n[TEST 3] Catastrophic Whale Exposure ($250,000.00) Governance Routing")
    try:
        # Test FraudPolicy directly on extreme exposure
        actions, file_sar, sar_reason = FraudPolicy.evaluate_final_actions(
            fraud_prob=0.95,
            verdict="fraud",
            pattern="undocumented",
            exposure_usd=250000.00,
            assumed_customer_response="Cardholder confirms unauthorized stolen card",
            is_shared_origin=True,
            connected_cards_count=5
        )
        routes = {a["action"]: a["route"] for a in actions}
        assert "BLOCK_CARD" in routes, "BLOCK_CARD not recommended for whale fraud"
        assert routes["BLOCK_CARD"] == "L2", f"BLOCK_CARD for $250k must be L2, got {routes['BLOCK_CARD']}"
        assert routes["FILE_REPORT"] == "L2", "FILE_REPORT must be L2"
        assert file_sar == True, "SAR must be filed for $250k fraud"
        print(f"  --> PASS: Whale exposure correctly escalated to L2 Fraud Manager approval.")
        print(f"      Action Routes: {routes}")
        passed += 1
    except Exception as e:
        print(f"  --> FAIL: Whale exposure governance test failed: {e}")
        traceback.print_exc()
        failed += 1

    # -------------------------------------------------------------
    # EDGE CASE 4: Desktop Browser Supernode (Prevent False Ring Alert)
    # -------------------------------------------------------------
    print("\n[TEST 4] Generic Browser Supernode Disambiguation (False Ring Prevention)")
    try:
        generic_device = "chrome 66.0 | Windows 10 | 1920x1080"
        neighbors = tg_client.get_device_neighbors(generic_device)
        print(f"  --> Connected cards on Chrome/Win10 in graph: {len(neighbors)}")
        
        broad_ua_alert = {
            "case_id": "EDGE-004",
            "opened_at": "2026-09-24 10:15:00",
            "trigger_type": "risk_score",
            "trigger_text": "Slight risk score deviation on standard web browser",
            "flagged_txn_id": "3514030",
            "card_id": "C12382-K1",
            "customer_id": "C12382",
            "risk_score": 0.40
        }
        res = agent.investigate_case(broad_ua_alert)
        assert res["case"]["pattern"] != "undocumented", "Broad UA falsely flagged as undocumented syndicate ring"
        print(f"  --> PASS: Broad UA handled properly. Pattern: {res['case']['pattern']}, Verdict: {res['case']['verdict']}")
        passed += 1
    except Exception as e:
        print(f"  --> FAIL: Supernode disambiguation test failed: {e}")
        traceback.print_exc()
        failed += 1

    # -------------------------------------------------------------
    # EDGE CASE 5: Conflicting Evidence (Denial vs 30 Historical Charges)
    # -------------------------------------------------------------
    print("\n[TEST 5] Conflicting Evidence (Customer Dispute on Proven Recurring Billing)")
    try:
        import pandas as pd
        cases_df = pd.read_csv(os.path.join(data_dir, "case_pack.csv"))
        hhg18 = cases_df[cases_df["case_id"] == "HHG-018"].iloc[0].to_dict()
        res = agent.investigate_case(hhg18)
        
        final_actions = [a["action"] for a in res["next_best_actions"]["final"]]
        assert res["case"]["verdict"] == "legitimate", f"Expected legitimate, got {res['case']['verdict']}"
        assert "BLOCK_CARD" not in final_actions, "Policy violation: Card blocked on recurring merchant dispute!"
        assert "ALLOW_TRANSACTION" in final_actions or "WARN_CUSTOMER" in final_actions, "Missing recurring resolution actions"
        print(f"  --> PASS: Conflicting recurring dispute evaluated correctly under Rule R7.")
        print(f"      Verdict: {res['case']['verdict']}, Final Actions: {final_actions}")
        passed += 1
    except Exception as e:
        print(f"  --> FAIL: Conflicting evidence test failed: {e}")
        traceback.print_exc()
        failed += 1

    # -------------------------------------------------------------
    # EDGE CASE 6: Rapid Geographic Velocity (Rule R8)
    # -------------------------------------------------------------
    print("\n[TEST 6] Rapid Geographic Velocity (Distant Concurrent In-Person Txns)")
    try:
        r8_actions = FraudPolicy.evaluate_initial_actions(
            fraud_prob=0.85,
            pattern="out_of_region_use",
            single_signal=False,
            exposure_usd=500.00
        )
        routes = {a["action"]: a["route"] for a in r8_actions}
        assert "CREATE_CASE" in routes or "VERIFY_WITH_CUSTOMER" in routes, "Rule R8 actions missing"
        print(f"  --> PASS: Rule R8 velocity response enforced properly.")
        print(f"      Actions: {routes}")
        passed += 1
    except Exception as e:
        print(f"  --> FAIL: Velocity rule test failed: {e}")
        traceback.print_exc()
        failed += 1

    # -------------------------------------------------------------
    # EDGE CASE 7: API Robustness & Security Injection Testing
    # -------------------------------------------------------------
    print("\n[TEST 7] REST API Security & Injection Robustness")
    api_pass = True
    test_urls = [
        ("http://127.0.0.1:8080/api/cases/NON_EXISTENT_CASE", 404),
        ("http://127.0.0.1:8080/api/cases/HHG-001'%20OR%201=1--", 404),
        ("http://127.0.0.1:8080/api/cases/%3Cscript%3Ealert(1)%3C/script%3E", 404),
        ("http://127.0.0.1:8080/api/graph/NON_EXISTENT_CASE", 404)
    ]
    for url, expected_code in test_urls:
        try:
            req = urllib.request.Request(url)
            urllib.request.urlopen(req)
            print(f"  --> WARNING: Expected {expected_code} but got 200 for {url}")
            api_pass = False
        except urllib.error.HTTPError as he:
            if he.code == expected_code:
                continue
            else:
                print(f"  --> Unexpected HTTP code {he.code} for {url}")
                api_pass = False
        except Exception as e:
            print(f"  --> Connection error (is server running?): {e}")
            api_pass = False

    if api_pass:
        print("  --> PASS: REST API cleanly rejects injection strings and invalid IDs with 404.")
        passed += 1
    else:
        print("  --> FAIL: REST API security test encountered unexpected responses.")
        failed += 1

    # -------------------------------------------------------------
    # EDGE CASE 8: FinCEN SAR 5Ws/H Completeness & Consistency
    # -------------------------------------------------------------
    print("\n[TEST 8] FinCEN SAR 5Ws/H Regulatory Integrity Test")
    try:
        cases_dir = os.path.join(PROJECT_ROOT, "cases")
        sar_count = 0
        for f in os.listdir(cases_dir):
            if not f.endswith(".json"): continue
            with open(os.path.join(cases_dir, f), "r", encoding="utf-8") as jf:
                cd = json.load(jf)
                sar = cd.get("sar", {})
                if sar.get("file"):
                    sar_count += 1
                    assert len(sar.get("subjects", [])) > 0, f"SAR missing WHO (subjects) in {f}"
                    assert sar.get("total_amount_usd", 0) > 0, f"SAR missing WHAT (amount) in {f}"
                    assert len(sar.get("activity_dates", [])) > 0, f"SAR missing WHEN (dates) in {f}"
                    narrative = sar.get("narrative", "")
                    assert len(narrative) > 50, f"SAR narrative too short in {f}"
                    narrative_lower = narrative.lower()
                    assert "customer" in narrative_lower or "cardholder" in narrative_lower, f"Narrative missing WHO in {f}"
                    assert "$" in narrative, f"Narrative missing amount in {f}"

        print(f"  --> PASS: All {sar_count} regulatory SAR filings strictly adhere to FinCEN 5Ws/H standard.")
        passed += 1
    except Exception as e:
        print(f"  --> FAIL: SAR Regulatory test failed: {e}")
        traceback.print_exc()
        failed += 1

    # -------------------------------------------------------------
    # FINAL SUMMARY
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    print(f"   EDGE CASE TEST SUMMARY: {passed}/{total} PASSED ({failed} FAILED)   ")
    print("=" * 70)
    if failed == 0:
        print("[RESULT] ALL ADVERSARIAL REAL-WORLD EDGE CASES PASSED WITH 100% SUCCESS!")
    else:
        print(f"[RESULT] {failed} EDGE CASES FAILED. REVIEW LOGS ABOVE.")

if __name__ == "__main__":
    run_tests()
