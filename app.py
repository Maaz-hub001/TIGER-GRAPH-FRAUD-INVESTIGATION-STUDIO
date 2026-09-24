"""
TigerGraph Agentic Fraud Investigation Studio
Interactive Analyst Dashboard, Knowledge Graph Visualizer, and Case Memory Explorer.
HHGOA 2026 Hackathon Submission
"""

import os
import sys
import json
import pandas as pd
import streamlit as st

# Setup path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tigergraph.client import TigerGraphClient
from agent.investigator import FraudInvestigationAgent

# Configure Page
st.set_page_config(
    page_title="TigerGraph | Agentic Fraud Investigation Studio",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Cyber-Intelligence Aesthetic
st.markdown("""
<style>
    /* Dark cyber theme accents */
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .metric-val {
        font-size: 26px;
        font-weight: 700;
        color: #38bdf8;
    }
    .metric-label {
        font-size: 13px;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .badge-auto {
        background-color: #065f46;
        color: #34d399;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
    }
    .badge-l1 {
        background-color: #854d0e;
        color: #fde047;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
    }
    .badge-l2 {
        background-color: #991b1b;
        color: #fca5a5;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
    }
    .sar-box {
        background-color: #1e1e2d;
        border-left: 4px solid #f59e0b;
        padding: 16px;
        border-radius: 4px;
        font-family: 'Courier New', Courier, monospace;
        font-size: 13px;
        color: #e2e8f0;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_agent():
    tg_client = TigerGraphClient(data_dir=os.path.join(PROJECT_ROOT, "data"))
    agent = FraudInvestigationAgent(tg_client=tg_client)
    return tg_client, agent


tg_client, agent = load_agent()

# Load all 20 case files
CASES_DIR = os.path.join(PROJECT_ROOT, "cases")
case_files = {}
for i in range(1, 21):
    cid = f"HHG-{i:03d}"
    cpath = os.path.join(CASES_DIR, f"{cid}.json")
    if os.path.exists(cpath):
        with open(cpath, "r", encoding="utf-8") as f:
            case_files[cid] = json.load(f)

# Sidebar
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/e/ee/TigerGraph_Logo.png", width=180)
st.sidebar.markdown("### **Investigation Control**")

tg_status = "🟢 Live Savanna" if tg_client.is_live else "⚡ Embedded GSQL Engine"
st.sidebar.info(f"**Backend**: {tg_status}\n\n**Graph**: FraudInvestigationGraph")

case_list = sorted(list(case_files.keys()))
selected_case_id = st.sidebar.selectbox("Select Benchmark Case", case_list, index=13)  # default to HHG-014

st.sidebar.markdown("---")
st.sidebar.markdown("### **Hackathon Information**")
st.sidebar.caption("**Event**: TigerGraph × HHGoa 2026\n\n**Agent**: Agentic Fraud Investigator\n\n**Evaluation**: 20 Benchmark Alerts\n\n**Dataset**: 590K Transactions, 144K Identity records")

# Header Section
st.title("🛡️ TigerGraph Agentic Fraud Investigation Studio")
st.markdown("*Autonomous Graph-Powered Fraud Investigation, Next-Best Action Governance & Regulatory SAR Generation*")

# Top Metrics Bar
c1, c2, c3, c4, c5 = st.columns(5)

total_cases = len(case_files)
fraud_cases = sum(1 for c in case_files.values() if c["case"]["verdict"] == "fraud")
legit_cases = sum(1 for c in case_files.values() if c["case"]["verdict"] == "legitimate")
total_exposure = sum(c["case"]["exposure_usd"] for c in case_files.values())
sars_filed = sum(1 for c in case_files.values() if c["sar"]["file"])

with c1:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{total_cases}</div><div class="metric-label">Benchmark Cases</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#ef4444">{fraud_cases}</div><div class="metric-label">Confirmed Fraud</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#10b981">{legit_cases}</div><div class="metric-label">Cleared Legit (False Alarms)</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#f59e0b">${total_exposure:,.2f}</div><div class="metric-label">Fraud Exposure</div></div>', unsafe_allow_html=True)
with c5:
    st.markdown(f'<div class="metric-card"><div class="metric-val" style="color:#8b5cf6">{sars_filed}</div><div class="metric-label">Regulatory SARs</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Selected Case Details
case_data = case_files[selected_case_id]
case_obj = case_data["case"]
nba = case_data["next_best_actions"]
sar = case_data["sar"]

# Case Banner
b_col1, b_col2, b_col3, b_col4 = st.columns([2, 1, 1, 1])
with b_col1:
    verdict_color = "red" if case_obj["verdict"] == "fraud" else "green"
    st.subheader(f"Case {selected_case_id} — :{verdict_color}[{case_obj['verdict'].upper()}]")
    st.caption(f"**Pattern**: `{case_obj['pattern']}` | **Graph Case ID**: `{case_obj['graph_case_id']}`")
with b_col2:
    st.metric("Fraud Probability", f"{case_obj['fraud_probability']:.2f}")
with b_col3:
    st.metric("Case Exposure", f"${case_obj['exposure_usd']:,.2f}")
with b_col4:
    st.metric("Graph Memory", "Committed 🟢" if case_obj["written_to_graph"] else "Pending")

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Investigation & Next-Best Action",
    "🕸️ Knowledge Graph Subgraph",
    "🧠 GraphRAG Case Memory",
    "📜 Regulatory SAR Filing",
    "⚖️ Policy Governance & Approval"
])

with tab1:
    st.markdown("### **Investigation Progression & Reasoning**")
    
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.markdown("#### **Initial Assessment (Before Evidence)**")
        st.info(f"**Trigger**: {case_data.get('stop_reason', '')}")
        st.markdown("**Initial Actions Recommended:**")
        for act in nba["initial"]:
            route_class = f"badge-{act['route'].lower()}"
            st.markdown(f"- **`{act['action']}`** <span class='{route_class}'>{act['route']}</span>\n  *{act['reason']}*", unsafe_allow_html=True)
            
        st.markdown("#### **Controlled Evidence Requested**")
        ev_reqs = case_data.get("evidence_requests", [])
        if ev_reqs:
            for req in ev_reqs:
                st.markdown(f"**Request**: `{req['type']}` (Step {req['asked_after_step']})")
                st.success(f"**Received/Assumed Response**: {req['assumed_response']}")
        else:
            st.write("*No additional evidence required under policy.*")

    with col_right:
        st.markdown("#### **Final Assessment (After Evidence)**")
        st.markdown(f"**Status**: `{case_obj['status']}`")
        st.markdown(f"**What Changed**: *{nba.get('what_changed', '')}*")
        st.markdown("**Final Actions & Required Approvals:**")
        for act in nba["final"]:
            route_class = f"badge-{act['route'].lower()}"
            st.markdown(f"- **`{act['action']}`** <span class='{route_class}'>{act['route']}</span>\n  *{act['reason']}*", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### **Synthesized Evidence from Knowledge Graph**")
    for idx, ev in enumerate(case_obj["evidence"]):
        with st.expander(f"Evidence #{idx+1}: {ev['claim'][:90]}..."):
            st.markdown(f"**Claim**: {ev['claim']}")
            st.markdown(f"**Source**: `{ev['source']}` | **Query Reference**: `{ev['ref']}`")
            st.markdown(f"**Entity IDs**: `{', '.join(ev['entity_ids']) if ev['entity_ids'] else 'None'}`")

    st.markdown("#### **Executive Case Summary**")
    st.markdown(f"> *{case_obj['summary']}*")

with tab2:
    st.markdown("### **TigerGraph Knowledge Subgraph**")
    st.caption("Visualizing Customer -> Card -> Transactions -> Device Profile -> Syndicate Ring Nodes")
    
    # Graph Details
    g_col1, g_col2 = st.columns([1, 2])
    with g_col1:
        st.markdown("#### **Connected Graph Entities**")
        st.markdown(f"- **Primary Flagged Txn**: `{case_data.get('case_id')}`")
        st.markdown(f"- **Affected Txn IDs**: `{case_obj['affected_txn_ids']}`")
        st.markdown(f"- **Connected Cards**: `{len(case_obj['connected_card_ids'])} cards linked`")
        if case_obj['connected_card_ids']:
            st.caption(", ".join(case_obj['connected_card_ids'][:10]) + ("..." if len(case_obj['connected_card_ids']) > 10 else ""))
        st.markdown(f"- **Device Profiles**: `{case_obj['connected_device_profiles']}`")

    with g_col2:
        st.markdown("#### **Graph Traversal Visualization**")
        # Generate SVG / Canvas visualization of graph nodes
        st.markdown(f"""
        <div style="background-color:#0f172a; padding:20px; border-radius:10px; border:1px solid #334155; text-align:center;">
            <svg width="600" height="280" viewBox="0 0 600 280">
                <!-- Edges -->
                <line x1="80" y1="140" x2="200" y2="140" stroke="#64748b" stroke-width="2" />
                <line x1="200" y1="140" x2="350" y2="70" stroke="#64748b" stroke-width="2" />
                <line x1="200" y1="140" x2="350" y2="140" stroke="#64748b" stroke-width="2" />
                <line x1="200" y1="140" x2="350" y2="210" stroke="#64748b" stroke-width="2" />
                <line x1="350" y1="140" x2="500" y2="140" stroke="#ef4444" stroke-width="2" stroke-dasharray="4" />
                
                <!-- Customer Node -->
                <circle cx="80" cy="140" r="30" fill="#3b82f6" />
                <text x="80" y="145" font-size="12" fill="#fff" text-anchor="middle" font-weight="bold">Customer</text>
                
                <!-- Card Node -->
                <circle cx="200" cy="140" r="28" fill="#8b5cf6" />
                <text x="200" y="145" font-size="12" fill="#fff" text-anchor="middle" font-weight="bold">Card</text>
                
                <!-- Transaction Nodes -->
                <circle cx="350" cy="70" r="22" fill="#f59e0b" />
                <text x="350" y="75" font-size="10" fill="#fff" text-anchor="middle">Txn (t-1)</text>
                
                <circle cx="350" cy="140" r="24" fill="#ef4444" />
                <text x="350" y="145" font-size="10" fill="#fff" text-anchor="middle" font-weight="bold">Flagged</text>
                
                <circle cx="350" cy="210" r="22" fill="#f59e0b" />
                <text x="350" y="215" font-size="10" fill="#fff" text-anchor="middle">Txn (t+1)</text>
                
                <!-- Device Node -->
                <circle cx="500" cy="140" r="32" fill="{'#dc2626' if case_obj['connected_card_ids'] else '#06b6d4'}" />
                <text x="500" y="135" font-size="11" fill="#fff" text-anchor="middle" font-weight="bold">Device</text>
                <text x="500" y="152" font-size="9" fill="#f1f5f9" text-anchor="middle">{'Syndicate Ring' if case_obj['connected_card_ids'] else 'Trusted'}</text>
            </svg>
            <div style="font-size:12px; color:#94a3b8; margin-top:10px;">
                Node Hierarchy: Customer (Blue) → Card (Purple) → Transactions (Amber/Red) → Device Fingerprint (Teal/Crimson)
            </div>
        </div>
        """, unsafe_allow_html=True)

with tab3:
    st.markdown("### **GraphRAG Case Memory**")
    st.caption("Historical case precedents retrieved from 5,565 closed investigations.")
    
    priors = case_obj.get("similar_prior_cases", [])
    if priors:
        st.write(f"Found **{len(priors)}** relevant past cases referenced during investigation:")
        for pid in priors:
            p_match = tg_client.closed_cases_df[tg_client.closed_cases_df["case_id"] == pid]
            if len(p_match) > 0:
                p_row = p_match.iloc[0]
                with st.expander(f"📁 Prior Case {pid} — {p_row['outcome'].upper()} ({p_row['pattern']})"):
                    st.markdown(f"**Customer**: `{p_row['customer_id']}` | **Card**: `{p_row['card_id']}` | **Closed At**: `{p_row['closed_at']}`")
                    st.markdown(f"**Exposure**: `${p_row['exposure_usd']:,.2f}` | **Report Filed**: `{p_row['report_filed']}`")
                    st.markdown(f"**Actions Taken**: `{p_row['actions_taken']}`")
                    st.markdown(f"**Analyst Notes**: {p_row['analyst_notes']}")
    else:
        st.info("No customer-specific historical precedents required for this alert.")

with tab4:
    st.markdown("### **Regulatory Suspicious Activity Report (SAR)**")
    if sar["file"]:
        st.warning("⚠️ **MANDATORY SAR FILING REQUIRED BY POLICY**")
        st.markdown(f"**Filing Justification**: *{sar['reason']}*")
        st.markdown(f"**Total Suspicious Exposure**: `${sar['total_amount_usd']:,.2f}`")
        st.markdown(f"**Activity Dates**: `{sar['activity_dates'][0]}` to `{sar['activity_dates'][1]}`")
        st.markdown(f"**Subject Entities Named**: `{', '.join(sar['subjects'])}`")
        st.markdown("#### **FinCEN 5Ws/H Narrative Statement:**")
        st.markdown(f'<div class="sar-box">{sar["narrative"]}</div>', unsafe_allow_html=True)
    else:
        st.success("✅ **NO SAR REQUIRED** — Activity cleared as legitimate or sub-threshold under Policy 3a.")
        st.caption(f"Reason: {sar['reason']}")

with tab5:
    st.markdown("### **Policy Governance & Approval Routing Station**")
    st.caption("Enforcing separation of duties between Agent Execution, Team Lead (L1), and Fraud Manager (L2).")
    
    for act in nba["final"]:
        act_name = act["action"]
        route = act["route"]
        reason = act["reason"]
        
        with st.container():
            st.markdown(f"#### `{act_name}`")
            if route == "auto":
                st.markdown("🟢 **Status**: `AUTO-EXECUTED BY AGENT` (No approval required)")
            elif route == "L1":
                st.markdown("🟡 **Status**: `PENDING L1 APPROVAL` (Team Lead Authorization Required)")
                st.button(f"Approve {act_name} (L1)", key=f"btn_l1_{act_name}")
            elif route == "L2":
                st.markdown("🔴 **Status**: `PENDING L2 APPROVAL` (Fraud Manager Authorization Required)")
                st.button(f"Approve {act_name} (L2)", key=f"btn_l2_{act_name}")
            st.caption(f"Policy Justification: {reason}")
            st.markdown("---")

st.markdown("<br><br>", unsafe_allow_html=True)
st.caption("Built with TigerGraph Savanna, GSQL, GraphRAG & Streamlit | HHGOA 2026 Submission")
