# 🛡️ TigerGraph Agentic Fraud Investigation System (HH_GOA)

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![TigerGraph](https://img.shields.io/badge/TigerGraph-GSQL%20Savanna-orange.svg)](https://savanna.tgcloud.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-red.svg)](https://streamlit.io)
[![Compliance](https://img.shields.io/badge/FinCEN%20SAR-5Ws%2FH%20Compliant-brightgreen.svg)]()
[![Benchmark](https://img.shields.io/badge/Benchmark-20%2F20%20Verified%20(100%25)-success.svg)]()
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)

> **Autonomous AI fraud investigation platform powered by TigerGraph, GraphRAG, and formal bank governance policies. Features multi-hop graph traversal, syndication ring detection, automated FinCEN SAR drafting (5Ws/H), and a cyber-studio analyst console.**

Built for the **TigerGraph × Hacker House Goa 2026 Hackathon**.

---

## 📌 Executive Summary

Modern financial crime syndicates exploit siloed relational databases by scattering coordinated card-not-present fraud across synthetic identities, rotating device fingerprints, and unlinked merchants. 

The **TigerGraph Fraud Investigation Agent** transforms raw fraud alerts into audit-ready regulatory dossiers. By traversing multi-hop subgraphs across millions of transaction entities, the system uncovers concealed crime rings (including 50+ card syndicates), correlates historical precedents, strictly enforces tiered human-in-the-loop approvals (`auto`, `L1`, `L2`), and synthesizes FinCEN-compliant Suspicious Activity Reports (SAR).

---

## 🚀 Key Architectural Pillars

- 🕸️ **Multi-Hop Graph Intelligence (TigerGraph & GSQL)**: Traverses card-window velocity, device sharing, billing region anomalies, and merchant clusters up to 3 hops deep. In benchmark case `HHG-014` / `HHG-006`, uncovers organized rings of **51+ customer cards** linked via shared hardware emulator profiles.
- 🧠 **GraphRAG Precedent Retrieval**: Contextualizes active investigations against a vectorized library of 5,565 closed historical fraud cases (`closed_cases_history.csv`) to eliminate hallucinations and guide defensible decisioning.
- ⚖️ **Deterministic Policy Governance (Rules R1–R10)**: Maps fraud confidence and financial exposure to strict bank operating tiers:
  - `auto`: Direct automated execution for low-risk actions (`ALLOW_TRANSACTION`, `MONITOR_CARD`, `CREATE_CASE`, `VERIFY_WITH_CUSTOMER`).
  - `L1` (Team Lead): First-line fraud analyst review for card blocks and declines ($\le \$5,000$).
  - `L2` (Fraud Manager): Senior managerial authorization for catastrophic exposures ($> \$5,000$), multi-card syndicate freezes, and regulatory filings.
- 📋 **FinCEN SAR 5Ws/H Engine**: Automatically drafts regulatory-grade Suspicious Activity Reports detailing **Who, What, When, Where, Why, and How** whenever policy thresholds are triggered.
- 🔄 **Dynamic Case Writeback**: Real-time writeback of investigated cases and evidence edges into TigerGraph memory (`written_to_graph = true`), establishing graph audit history.
- 🖥️ **Dual Analyst Cockpit**:
  - **Cyber Studio (`:8080`)**: Modern FastAPI + Vis.js interactive graph workspace, real-time entity inspector drawer, and syndicate zoom console.
  - **Streamlit Ops Portal (`:8501`)**: Executive metrics, triage filters, and compliance audit exports.

---

## 📂 Repository Structure

```
HH_GOA/
├── cases/                     # All 20 benchmark case deliverables (HHG-001.json .. HHG-020.json)
│   ├── HHG-001.json           # 100% verified schema & FinCEN compliance
│   ├── ...
│   └── HHG-020.json
├── data/                      # Benchmark and graph datasets
│   ├── case_pack.csv          # 20 benchmark alert cases
│   ├── closed_cases_history.csv # 5,565 historical closed cases for GraphRAG
│   ├── identity.csv           # 144,432 online identity/device records
│   └── transactions.csv       # 590,742 card transactions
├── tigergraph/                # TigerGraph schemas and client layer
│   ├── schema.gsql            # Native GSQL schema definition
│   ├── queries.gsql           # GSQL query algorithms (card_window, device_neighbors)
│   └── client.py              # Unified client (Savanna Cloud + Embedded GSQL Engine)
├── agent/                     # Agentic Investigation Engine
│   ├── investigator.py        # Autonomous multi-step investigation orchestrator
│   ├── policy.py              # Fraud Policy v1.0 & approval governance (R1-R10)
│   └── memory.py              # GraphRAG retriever over 5,565 closed cases
├── static/                    # Cyber Studio Web Console assets
│   ├── index.html             # Graph studio console with syndicate zoom
│   ├── style.css              # Glassmorphic CSS design system
│   ├── app.js                 # Vis.js physics, inspector drawer & filters
│   └── vis-network.min.js     # Standalone local Vis.js library
├── scripts/                   # Evaluation & QA scripts
│   ├── run_benchmark.py       # Benchmark evaluation runner for all 20 cases
│   ├── verify_cases.py        # Strict format validator (100% compliance test)
│   ├── test_real_world_edge_cases.py # 8-point adversarial edge case test suite
│   ├── build_device_index.py  # Global device-card graph indexer
│   └── detailed_case_evaluator.py
├── docs/                      # Submission documentation
│   ├── blog_post.md           # Complete technical blog post
│   ├── social_post.md         # Social media copy for X and LinkedIn
│   └── demo_script.md         # 3-5 minute video demo recording script
├── server.py                  # FastAPI REST API & Cyber Studio server
├── app.py                     # Interactive Streamlit Analyst Studio
└── README.md                  # This file
```

---

## 🚀 Quickstart Guide

### 1. Installation
Requires Python 3.10+. Install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Run the Benchmark Evaluation
Execute the autonomous agent across all 20 benchmark cases:
```bash
python scripts/run_benchmark.py
```

### 3. Validate Strict Format Compliance (20/20 Deliverables)
Verify that all 20 case files strictly meet every requirement of the hackathon answer specification:
```bash
python scripts/verify_cases.py
```
*Output: `[SUCCESS] ALL 20 CASES PASSED 100% STRICT COMPLIANCE CHECKS!`*

### 4. Run the Real-World Adversarial Edge Case Suite
Stress-test the system against 8 adversarial real-world conditions:
```bash
python scripts/test_real_world_edge_cases.py
```
*Output: `[RESULT] ALL ADVERSARIAL REAL-WORLD EDGE CASES PASSED WITH 100% SUCCESS!`*

### 5. Launch the Analyst Consoles

- **Cyber Studio Console (FastAPI + Vis.js)**:
  ```bash
  python -m uvicorn server:app --host 127.0.0.1 --port 8080
  ```
  Open `http://localhost:8080` in your browser.

- **Streamlit Ops Portal**:
  ```bash
  streamlit run app.py --server.port 8501
  ```
  Open `http://localhost:8501` in your browser.

---

## 🧪 Real-World Adversarial QA Suite (8/8 Passed)

| Test # | Adversarial Stress Vector | Risk Mitigated | Status |
| :---: | :--- | :--- | :---: |
| **1** | **Ghost Entities / Corrupted IDs** | Missing customer/card IDs handled gracefully with zero 500 crashes | **PASS** |
| **2** | **Zero-Dollar Transactions ($0.00)** | Account verification pings handled without division-by-zero errors | **PASS** |
| **3** | **Whale Exposure ($250,000.00)** | Extreme losses strictly escalate to `L2` Manager approval tier | **PASS** |
| **4** | **Browser Supernode Disambiguation** | Prevents false-positive ring flags on generic desktop Chrome/Win10 | **PASS** |
| **5** | **Recurring Billing Disputes (R7)** | Protects subscriptions against false card blocks upon customer dispute | **PASS** |
| **6** | **Rapid Geographic Velocity (R8)** | Instant `DECLINE_TRANSACTION` (`L1`) on concurrent distant swipes | **PASS** |
| **7** | **API Robustness & SQLi/XSS Injections** | Injection attacks strictly rejected with sanitised HTTP 404 responses | **PASS** |
| **8** | **FinCEN SAR 5Ws/H Regulatory Integrity** | All 10 SAR cases strictly validate Who, What, When, Where, Why, and How | **PASS** |

---

## 📊 Benchmark Results Summary (20 Cases)

| Case ID | Verdict | Fraud Prob | Identified Pattern | Exposure ($) | Initial Action | Final Action | SAR Filed |
|---|---|---|---|---|---|---|---|
| **HHG-001** | `fraud` | 0.89 | `out_of_region_use` | $77.07 | VERIFY_WITH_CUSTOMER | BLOCK_CARD, CREATE_CASE | No |
| **HHG-002** | `legitimate` | 0.14 | `none` | $0.00 | VERIFY_WITH_CUSTOMER | ALLOW_TRANSACTION, CLOSE_NO_FRAUD | No |
| **HHG-003** | `legitimate` | 0.12 | `none` | $0.00 | VERIFY_WITH_CUSTOMER | ALLOW_TRANSACTION, CLOSE_NO_FRAUD | No |
| **HHG-004** | `fraud` | 0.88 | `card_not_present_new_device` | $128.33 | DECLINE_TRANSACTION | BLOCK_CARD, CREATE_CASE, FILE_REPORT | Yes |
| **HHG-005** | `legitimate` | 0.14 | `none` | $0.00 | MONITOR_CARD | ALLOW_TRANSACTION, CLOSE_NO_FRAUD | No |
| **HHG-006** | `fraud` | 0.88 | `card_not_present_new_device` | $482.12 | DECLINE_TRANSACTION | BLOCK_CARD, CREATE_CASE, FILE_REPORT | Yes |
| **HHG-007** | `legitimate` | 0.14 | `none` | $0.00 | VERIFY_WITH_CUSTOMER | ALLOW_TRANSACTION, CLOSE_NO_FRAUD | No |
| **HHG-008** | `fraud` | 0.88 | `card_not_present_fraud` | $55.68 | DECLINE_TRANSACTION | BLOCK_CARD, CREATE_CASE, FILE_REPORT | Yes |
| **HHG-009** | `fraud` | 0.88 | `card_not_present_fraud` | $30.02 | VERIFY_WITH_CUSTOMER | BLOCK_CARD, CREATE_CASE | No |
| **HHG-010** | `fraud` | 0.91 | `card_not_present_new_device` | $1,000.03 | DECLINE_TRANSACTION | BLOCK_CARD, CREATE_CASE, FILE_REPORT | Yes |
| **HHG-011** | `fraud` | 0.88 | `card_not_present_new_device` | $131.30 | DECLINE_TRANSACTION | BLOCK_CARD, CREATE_CASE, FILE_REPORT | Yes |
| **HHG-012** | `legitimate` | 0.18 | `none` | $0.00 | VERIFY_WITH_CUSTOMER | ALLOW_TRANSACTION, CLOSE_NO_FRAUD | No |
| **HHG-013** | `fraud` | 0.91 | `card_not_present_new_device` | $35.66 | DECLINE_TRANSACTION | BLOCK_CARD, CREATE_CASE, FILE_REPORT | Yes |
| **HHG-014** | `fraud` | 0.95 | `undocumented` (51-Card Ring) | $74.96 | CREATE_CASE, FILE_REPORT | BLOCK_CARD, FILE_REPORT, MONITOR_CONNECTED, ESCALATE | Yes |
| **HHG-015** | `fraud` | 0.91 | `card_not_present_new_device` | $599.94 | DECLINE_TRANSACTION | BLOCK_CARD, CREATE_CASE, FILE_REPORT | Yes |
| **HHG-016** | `fraud` | 0.88 | `card_not_present_new_device` | $59.67 | DECLINE_TRANSACTION | BLOCK_CARD, CREATE_CASE, FILE_REPORT | Yes |
| **HHG-017** | `legitimate` | 0.14 | `none` | $0.00 | VERIFY_WITH_CUSTOMER | ALLOW_TRANSACTION, CLOSE_NO_FRAUD | No |
| **HHG-018** | `legitimate` | 0.12 | `none` (Rule R7 Recurring) | $0.00 | CREATE_CASE, WARN_CUSTOMER | ALLOW_TRANSACTION, CLOSE_NO_FRAUD | No |
| **HHG-019** | `fraud` | 0.91 | `card_not_present_new_device` | $99.92 | DECLINE_TRANSACTION | BLOCK_CARD, CREATE_CASE, FILE_REPORT | Yes |
| **HHG-020** | `legitimate` | 0.14 | `none` | $0.00 | MONITOR_CARD | ALLOW_TRANSACTION, CLOSE_NO_FRAUD | No |

---

## 🌐 Connecting to Live TigerGraph Savanna

The system comes with a dual-engine architecture:
1. **Embedded GSQL Engine** (Default): High-performance local engine for instant, reliable offline evaluation without cloud dependencies.
2. **Live TigerGraph Savanna / Community Edition**: To connect to a live TigerGraph instance, set the following environment variables:
   ```bash
   export TG_HOST="https://your-subdomain.i.tgcloud.io"
   export TG_USERNAME="tigergraph"
   export TG_PASSWORD="your-password"
   export TG_TOKEN="your-api-token"
   ```
   Deploy the schema and queries:
   ```bash
   gsql tigergraph/schema.gsql
   gsql tigergraph/queries.gsql
   ```

---

## 📖 Documentation & Submission Links

- [Technical Blog Post](docs/blog_post.md)
- [Video Demo Recording Script](docs/demo_script.md)
- [Social Media Posts for X & LinkedIn](docs/social_post.md)

---
*Developed for the TigerGraph × Hacker House Goa 2026 Hackathon.*
