"""
FastAPI Backend Server for TigerGraph Agentic Fraud Investigation Studio
Provides REST API endpoints for cases, graph topology, live investigation, and GraphRAG memory.
"""

import os
import sys
import json
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# Setup paths
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tigergraph.client import TigerGraphClient
from agent.investigator import FraudInvestigationAgent

app = FastAPI(title="TigerGraph Fraud Studio API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Graph Client & Agent
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
CASES_DIR = os.path.join(PROJECT_ROOT, "cases")

tg_client = TigerGraphClient(data_dir=DATA_DIR)
agent = FraudInvestigationAgent(tg_client=tg_client)


@app.get("/api/status")
def get_system_status():
    return {
        "status": "online",
        "engine": "TigerGraph Savanna" if tg_client.is_live else "Embedded GSQL Engine",
        "is_live_cloud": tg_client.is_live,
        "graph_name": tg_client.graphname,
        "total_transactions": len(tg_client.txns_df),
        "total_identities": len(tg_client.ident_df),
        "total_closed_cases": len(tg_client.closed_cases_df),
        "benchmark_cases_count": 20
    }


@app.get("/api/cases")
def list_cases():
    cases_summary = []
    cases_csv_path = os.path.join(DATA_DIR, "case_pack.csv")
    import pandas as pd
    cases_df = pd.read_csv(cases_csv_path)

    for idx, row in cases_df.iterrows():
        cid = row["case_id"]
        cpath = os.path.join(CASES_DIR, f"{cid}.json")
        verdict = "uncertain"
        prob = 0.5
        pattern = "none"
        exposure = 0.0
        sar_filed = False

        if os.path.exists(cpath):
            with open(cpath, "r", encoding="utf-8") as f:
                cdata = json.load(f)
                case_obj = cdata.get("case", {})
                verdict = case_obj.get("verdict", "uncertain")
                prob = case_obj.get("fraud_probability", 0.5)
                pattern = case_obj.get("pattern", "none")
                exposure = case_obj.get("exposure_usd", 0.0)
                sar_filed = cdata.get("sar", {}).get("file", False)

        cases_summary.append({
            "case_id": cid,
            "opened_at": row["opened_at"],
            "trigger_type": row["trigger_type"],
            "trigger_text": row["trigger_text"],
            "flagged_txn_id": str(row["flagged_txn_id"]),
            "card_id": row["card_id"],
            "customer_id": row["customer_id"],
            "risk_score": float(row["risk_score"]) if pd.notna(row["risk_score"]) else None,
            "verdict": verdict,
            "fraud_probability": prob,
            "pattern": pattern,
            "exposure_usd": exposure,
            "sar_filed": sar_filed
        })

    return {"cases": cases_summary}


@app.get("/api/cases/{case_id}")
def get_case_detail(case_id: str):
    cpath = os.path.join(CASES_DIR, f"{case_id}.json")
    if not os.path.exists(cpath):
        raise HTTPException(status_code=404, detail="Case file not found")
    with open(cpath, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/graph/{case_id}")
def get_graph_topology(case_id: str):
    cpath = os.path.join(CASES_DIR, f"{case_id}.json")
    if not os.path.exists(cpath):
        raise HTTPException(status_code=404, detail="Case file not found")

    with open(cpath, "r", encoding="utf-8") as f:
        data = json.load(f)

    case_obj = data["case"]
    cust_id = case_id  # fallback
    import pandas as pd
    cases_df = pd.read_csv(os.path.join(DATA_DIR, "case_pack.csv"))
    c_match = cases_df[cases_df["case_id"] == case_id]
    if len(c_match) > 0:
        cust_id = c_match.iloc[0]["customer_id"]
        card_id = c_match.iloc[0]["card_id"]
        flg_txn = str(c_match.iloc[0]["flagged_txn_id"])
    else:
        card_id = f"{cust_id}-K1"
        flg_txn = "3500000"

    nodes = []
    edges = []

    # 1. Customer Node
    nodes.append({
        "id": cust_id,
        "label": f"Customer\n{cust_id}",
        "group": "customer",
        "shape": "dot",
        "size": 28,
        "color": "#38bdf8",
        "font": {"color": "#ffffff", "face": "Plus Jakarta Sans"}
    })

    # 2. Card Node
    nodes.append({
        "id": card_id,
        "label": f"Card\n{card_id}",
        "group": "card",
        "shape": "dot",
        "size": 22,
        "color": "#a855f7",
        "font": {"color": "#ffffff", "face": "Plus Jakarta Sans"}
    })
    edges.append({"from": cust_id, "to": card_id, "label": "OWNS", "color": {"color": "#64748b"}})

    # 3. Flagged Transaction Node
    is_fraud = case_obj["verdict"] == "fraud"
    flg_color = "#ef4444" if is_fraud else "#10b981"
    nodes.append({
        "id": flg_txn,
        "label": f"Flagged Txn\n#{flg_txn}\n${case_obj.get('exposure_usd', 0):.2f}",
        "group": "transaction",
        "shape": "dot",
        "size": 26,
        "color": flg_color,
        "font": {"color": "#ffffff", "face": "Plus Jakarta Sans"}
    })
    edges.append({"from": card_id, "to": flg_txn, "label": "MADE", "color": {"color": "#f59e0b"}})

    # 4. Device Profile Node
    dev_profiles = case_obj.get("connected_device_profiles", [])
    if dev_profiles:
        dev_id = f"DEV-{case_id}"
        dev_text = dev_profiles[0]
        # Short label
        short_dev = dev_text.split(" | ")[0] if " | " in dev_text else dev_text
        nodes.append({
            "id": dev_id,
            "label": f"Device Profile\n{short_dev[:25]}",
            "group": "device",
            "shape": "dot",
            "size": 24,
            "color": "#06b6d4",
            "font": {"color": "#ffffff", "face": "Plus Jakarta Sans"}
        })
        edges.append({"from": flg_txn, "to": dev_id, "label": "FROM_DEVICE", "color": {"color": "#06b6d4"}})

        # 5. Connected Cards (Syndicate Ring Nodes if present)
        connected_cards = case_obj.get("connected_card_ids", [])
        if connected_cards:
            ring_cluster_id = f"RING-{case_id}"
            nodes.append({
                "id": ring_cluster_id,
                "label": f"Syndicate Ring\n({len(connected_cards)} Cards)",
                "group": "syndicate",
                "shape": "diamond",
                "size": 32,
                "color": "#f43f5e",
                "font": {"color": "#ffffff", "face": "Plus Jakarta Sans", "bold": True}
            })
            edges.append({"from": dev_id, "to": ring_cluster_id, "label": "EXPLOITS", "color": {"color": "#f43f5e"}, "dashes": True})

            for cc in connected_cards[:8]:
                nodes.append({
                    "id": cc,
                    "label": cc,
                    "group": "connected_card",
                    "shape": "dot",
                    "size": 14,
                    "color": "#fb7185",
                    "font": {"color": "#cbd5e1", "size": 10}
                })
                edges.append({"from": ring_cluster_id, "to": cc, "color": {"color": "#f43f5e"}})

    # 6. FraudCase Graph Writeback Node
    graph_case_id = case_obj.get("graph_case_id")
    if graph_case_id:
        nodes.append({
            "id": graph_case_id,
            "label": f"Graph Case\n{graph_case_id}",
            "group": "fraud_case",
            "shape": "square",
            "size": 20,
            "color": "#eab308",
            "font": {"color": "#ffffff", "face": "Plus Jakarta Sans"}
        })
        edges.append({"from": graph_case_id, "to": card_id, "label": "INVESTIGATES", "color": {"color": "#eab308"}})
        edges.append({"from": graph_case_id, "to": flg_txn, "label": "FLAGS", "color": {"color": "#eab308"}})

    return {
        "nodes": nodes,
        "edges": edges,
        "summary": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "case_id": case_id,
            "verdict": case_obj["verdict"],
            "pattern": case_obj["pattern"]
        }
    }


@app.post("/api/investigate/{case_id}")
def rerun_investigation(case_id: str):
    import pandas as pd
    cases_df = pd.read_csv(os.path.join(DATA_DIR, "case_pack.csv"))
    c_match = cases_df[cases_df["case_id"] == case_id]
    if len(c_match) == 0:
        raise HTTPException(status_code=404, detail="Case not found in case pack")

    res = agent.investigate_case(c_match.iloc[0].to_dict())
    
    # Update on disk
    cpath = os.path.join(CASES_DIR, f"{case_id}.json")
    with open(cpath, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)

    return res


# Mount static files
STATIC_DIR = os.path.join(PROJECT_ROOT, "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8080, reload=True)
