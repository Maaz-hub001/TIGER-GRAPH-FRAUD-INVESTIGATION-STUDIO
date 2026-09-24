"""
Strict Compliance Validator for Hackathon Case Deliverables
Validates cases/HHG-001.json through HHG-020.json against README.md specifications.
"""

import os
import json
import sys

VALID_PATTERNS = {
    "card_testing",
    "card_not_present_fraud",
    "card_not_present_new_device",
    "out_of_region_use",
    "account_takeover",
    "undocumented",
    "none"
}

VALID_STATUSES = {"open", "closed_fraud", "closed_legitimate", "escalated"}
VALID_VERDICTS = {"fraud", "legitimate", "uncertain"}
VALID_ROUTES = {"auto", "L1", "L2"}


def validate_all_cases(cases_dir: str = "cases"):
    print("=================================================================")
    print("          STRICT COMPLIANCE VALIDATOR (README.md)                ")
    print("=================================================================\n")

    errors = []
    warnings = []

    for i in range(1, 21):
        cid = f"HHG-{i:03d}"
        file_path = os.path.join(cases_dir, f"{cid}.json")

        if not os.path.exists(file_path):
            errors.append(f"Missing file: {file_path}")
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            errors.append(f"{cid}: JSON decode error ({e})")
            continue

        # Top-level checks
        required_top = ["case_id", "case", "evidence_requests", "next_best_actions", "sar", "stop_reason", "tool_calls", "tokens", "latency_s"]
        for k in required_top:
            if k not in data:
                errors.append(f"{cid}: Missing top-level key '{k}'")

        if data.get("case_id") != cid:
            errors.append(f"{cid}: case_id mismatch '{data.get('case_id')}'")

        # Case object checks
        case = data.get("case", {})
        required_case = [
            "status", "verdict", "fraud_probability", "pattern", "pattern_description",
            "affected_txn_ids", "first_suspicious_txn_id", "connected_card_ids",
            "connected_device_profiles", "exposure_usd", "evidence", "similar_prior_cases",
            "summary", "written_to_graph", "graph_case_id"
        ]
        for k in required_case:
            if k not in case:
                errors.append(f"{cid}: Missing case key '{k}'")

        if case.get("status") not in VALID_STATUSES:
            errors.append(f"{cid}: Invalid status '{case.get('status')}'")

        if case.get("verdict") not in VALID_VERDICTS:
            errors.append(f"{cid}: Invalid verdict '{case.get('verdict')}'")

        if not (0.0 <= case.get("fraud_probability", -1) <= 1.0):
            errors.append(f"{cid}: fraud_probability out of [0, 1]")

        if case.get("pattern") not in VALID_PATTERNS:
            errors.append(f"{cid}: Invalid pattern '{case.get('pattern')}'")

        if case.get("pattern") == "undocumented" and not case.get("pattern_description"):
            errors.append(f"{cid}: pattern is undocumented but pattern_description is empty")

        if case.get("pattern") != "undocumented" and case.get("pattern_description") != "":
            errors.append(f"{cid}: pattern is not undocumented but pattern_description is non-empty")

        # Legitimate verdict constraints
        if case.get("verdict") == "legitimate":
            if case.get("affected_txn_ids") != []:
                errors.append(f"{cid}: Legitimate verdict must have empty affected_txn_ids")
            if case.get("exposure_usd") != 0.0:
                errors.append(f"{cid}: Legitimate verdict must have exposure_usd == 0")

        # Evidence list checks
        evidence = case.get("evidence", [])
        if not isinstance(evidence, list):
            errors.append(f"{cid}: evidence must be a list")
        for ev in evidence:
            for ek in ["claim", "source", "ref", "entity_ids"]:
                if ek not in ev:
                    errors.append(f"{cid}: Evidence missing key '{ek}'")

        # Next best actions checks
        nba = data.get("next_best_actions", {})
        for nk in ["initial", "final", "what_changed"]:
            if nk not in nba:
                errors.append(f"{cid}: next_best_actions missing key '{nk}'")

        for phase in ["initial", "final"]:
            for act in nba.get(phase, []):
                for ak in ["action", "route", "reason"]:
                    if ak not in act:
                        errors.append(f"{cid}: Action in {phase} missing key '{ak}'")
                if act.get("route") not in VALID_ROUTES:
                    errors.append(f"{cid}: Action has invalid route '{act.get('route')}'")

        # SAR checks
        sar = data.get("sar", {})
        for sk in ["file", "reason", "narrative", "subjects", "total_amount_usd", "activity_dates"]:
            if sk not in sar:
                errors.append(f"{cid}: sar missing key '{sk}'")

        file_report_in_final = any(a.get("action") == "FILE_REPORT" for a in nba.get("final", []))
        if sar.get("file") != file_report_in_final:
            errors.append(f"{cid}: sar.file ({sar.get('file')}) does not match FILE_REPORT presence in final actions ({file_report_in_final})")

        if sar.get("file") is False:
            if sar.get("narrative") != "":
                errors.append(f"{cid}: sar.file is false but narrative is not empty")
            if sar.get("subjects") != []:
                errors.append(f"{cid}: sar.file is false but subjects is not empty")
            if sar.get("total_amount_usd") != 0:
                errors.append(f"{cid}: sar.file is false but total_amount_usd is not 0")
            if sar.get("activity_dates") != []:
                errors.append(f"{cid}: sar.file is false but activity_dates is not empty")
        else:
            if not sar.get("narrative"):
                errors.append(f"{cid}: sar.file is true but narrative is empty")
            if len(sar.get("subjects", [])) == 0:
                errors.append(f"{cid}: sar.file is true but subjects is empty")
            if len(sar.get("activity_dates", [])) != 2:
                errors.append(f"{cid}: sar.file is true but activity_dates does not contain 2 dates")

    print(f"Validation completed on 20 cases.")
    if errors:
        print(f"\n[FAIL] FOUND {len(errors)} ERRORS:")
        for e in errors:
            print(f"  - {e}")
        return False
    else:
        print("[SUCCESS] ALL 20 CASES PASSED 100% STRICT COMPLIANCE CHECKS!")
        return True


if __name__ == "__main__":
    success = validate_all_cases()
    sys.exit(0 if success else 1)
