# Graph-Powered Agentic Fraud Investigation & Next-Best Action with TigerGraph

*By Team Lead Maaz Ahmad Ansari — TigerGraph × Hacker House Goa 2026 Hackathon*

---

## 1. Introduction & The Core Problem

Fraud teams at major financial institutions face a critical operational bottleneck. Every day, detection models generate thousands of real-time alerts. Fraud analysts are forced to manually stitch together fragmented transaction ledgers, investigate device fingerprints, verify customer identities, review internal risk policies, and decide what action to take. By the time this manual process finishes, funds are often irreversibly transferred.

Furthermore, **isolated signals are deeply uncertain**:
- Many transactions with risk scores above 0.70 turn out to be legitimate cardholder purchases, business travel, or benign recurring charges.
- Sophisticated fraud syndicates use card testing micro-authorizations, mobile emulators, and rotating proxies that score near zero on traditional isolated tabular models.
- **Blocking a legitimate customer on a single weak signal is a serious policy violation.** Conversely, failing to recognize coordinated syndicate attacks exposes the bank to catastrophic losses.

To solve this, we built an **Autonomous, Policy-Governed Agentic Fraud Investigation System** powered by **TigerGraph Savanna, GSQL Graph Algorithms, and GraphRAG**. The system automatically navigates uncertain fraud signals, performs multi-hop graph traversals to uncover hidden fraud syndicates, queries 5,565 historical closed cases for precedent memory, recommends next-best actions under strict governance tiers (Auto, L1, L2), files regulatory Suspicious Activity Reports (SAR), and writes closed cases back into the graph memory.

---

## 2. System Architecture

The architecture combines TigerGraph's high-performance native graph database with multi-step agentic workflow orchestration, GraphRAG memory retrieval, and policy governance:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Analyst Investigation Studio (Streamlit)                  │
│       [Case Queue]   [Knowledge Graph Canvas]   [SAR Viewer]   [Approval]     │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼───────────────────────────────────────┐
│                    TigerGraph Agentic Investigation Engine                    │
│                                                                              │
│   ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────┐   │
│   │   Trigger Handler    │  │  Pattern Recognition │  │ SAR 5Ws/H Engine │   │
│   │  (Score/Report/Req)  │  │ (R1-R10, Patterns)   │  │ (FinCEN Format)  │   │
│   └──────────┬───────────┘  └──────────┬───────────┘  └────────▲─────────┘   │
│              │                         │                       │             │
│   ┌──────────▼───────────┐  ┌──────────▼───────────┐  ┌────────┴─────────┐   │
│   │ Uncertainty Assessor │  │ Evidence Requester   │  │ Next-Best Action │   │
│   │ & Risk Calibrator    │  │ (Step-Up / Customer) │  │ Governance (L1/2)│   │
│   └──────────────────────┘  └──────────────────────┘  └──────────────────┘   │
└──────────────────────▲───────────────────────────────▲───────────────────────┘
                       │                               │
        ┌──────────────┴───────────────┐   ┌───────────┴───────────────┐
        │  TigerGraph Knowledge Graph  │   │   GraphRAG & Case Memory  │
        │ - Schema & Graph Nodes       │   │ - 5,565 Closed Cases      │
        │ - Multi-hop GSQL Algorithms  │   │ - Fraud Policy v1.0       │
        │ - Real-time Writeback Edge   │   │ - Precedent Index         │
        └──────────────────────────────┘   └───────────────────────────┘
```

---

## 3. How TigerGraph is Used

### Native Graph Schema
Our GSQL schema models the complete financial ecosystem:
- **Vertices**:
  - `Customer`: Primary entity holding account relationships.
  - `Card`: Credit and debit payment tokens (`card1` to `card6`).
  - `Transaction`: Real-time financial events with timestamp, amount, product code, and risk score.
  - `DeviceProfile`: Hardware fingerprint composite (`DeviceInfo | OS | Browser | Screen`).
  - `BillingRegion`: Anonymized geographic billing regions (`addr1`, `addr2`).
  - `EmailDomain`: Purchaser and recipient email domains.
  - `ClosedCase`: Historical case memory from the first four months.
  - `FraudCase`: Agent-generated dynamic case vertices written back in real time.
- **Edges**:
  - `OWNS` (`Customer` → `Card`)
  - `MADE` (`Card` → `Transaction`)
  - `FROM_DEVICE` (`Transaction` → `DeviceProfile`)
  - `BILLED_IN` (`Transaction` → `BillingRegion`)
  - `NEXT` (`Transaction` → `Transaction`, temporal order)
  - `INVOLVES` / `ON_CARD` / `CONNECTED_TO` (ClosedCase links)
  - `INVESTIGATES` / `FLAGS` / `CONNECTED_DEVICE` (Dynamic writeback links)

### GSQL Algorithms for Fraud Detection
We authored dedicated GSQL queries that expose graph algorithms directly to the agent:
1. **`card_window`**: Extracts the sub-graph of transactions within a 48-hour delta to detect transaction bursts and card testing patterns (sequences of micro-authorizations under $5 preceding larger purchases).
2. **`device_neighbors`**: Multi-hop graph traversal algorithm:
   $$\text{DeviceProfile} \xleftarrow{\text{FROM\_DEVICE}} \text{Transaction} \xleftarrow{\text{MADE}} \text{Card} \xleftarrow{\text{OWNS}} \text{Customer}$$
   This query was instrumental in discovering the **52-customer syndicate fraud ring** in case **HHG-014**, where 114 transactions across 52 different cardholders originated from a single hardware device profile (`SM-G935F Build/NRD90M | Android 7.0 | chrome 62.0 for android | 1920x1080`).
3. **`write_case_to_graph`**: Dynamically writes the resolved fraud case vertex and incident edges into TigerGraph, enabling future alerts to immediately retrieve it as prior case memory.

---

## 4. Agentic Capabilities Implemented

1. **Autonomous Multi-Step Investigation Loop**:
   - Ingests triggers (model score, customer report, analyst request).
   - Traverses graph neighborhoods to extract evidence claims with strict provenance citations.
   - Grounded reasoning: LLM and rule synthesis avoids hallucinations by anchoring every claim to a specific query reference (e.g. `query:device_neighbors`, `query:customer_card_profile`).
2. **Uncertainty Evaluation & Controlled Evidence Gathering**:
   - The agent never jumps to an irreversible block on an isolated signal.
   - Under Policy Rule R1, when assessed probability is below 0.70 on a single signal, the agent recommends `VERIFY_WITH_CUSTOMER` or `STEP_UP_AUTH`.
   - Simulates policy-approved customer validation, captures the response in `evidence_requests`, and updates its verdict defensibly.
3. **Next-Best Action & Approval Governance**:
   - Distinct **Initial** (pre-evidence) and **Final** (post-evidence) actions.
   - Enforces bank governance tiers:
     - `auto`: Direct agent execution (`ALLOW_TRANSACTION`, `MONITOR_CARD`, `CREATE_CASE`, `VERIFY_WITH_CUSTOMER`).
     - `L1` (Team Lead): `DECLINE_TRANSACTION`, `BLOCK_CARD` ($\le \$2,500$).
     - `L2` (Fraud Manager): `BLOCK_CARD` ($> \$2,500$), `BLOCK_ALL_CARDS`, `FILE_REPORT`.
4. **FinCEN-Compliant SAR Generation**:
   - Whenever `FILE_REPORT` is recommended, the agent drafts a regulatory narrative covering the **5Ws and H** (Who, What, When, Where, How, Why), with subject IDs, exposure amounts, and activity dates.
5. **Case Memory Writeback**:
   - Resolves investigations and commits a `FraudCase` node into TigerGraph with `written_to_graph = true`.

---

## 5. Benchmark Performance (20 Cases)

We evaluated the agent across all 20 exam benchmark cases (`HHG-001` through `HHG-020`):
- **Accuracy on Legitimate Cases**: 100% precision on clearing false alarms (e.g., HHG-018 recurring subscription under Rule R7, HHG-007 home-region in-person spend, HHG-002 consistent online spend).
- **Syndicate Ring Detection**: Uncovered the 52-card syndicate in HHG-014 and escalated under Rule R6/R9 with a full regulatory SAR.
- **Card Testing & Cloning**: Accurately distinguished card cloning (HHG-001 concurrent spend in distant regions) and card testing sequences.
- **Compliance**: Passed 100% of strict format validations with zero schema errors.

---

## 6. What We Learned & Future Improvements

### Key Learnings:
- **Graph Structure Trumps Isolated Model Scores**: Isolated machine learning scores frequently fail on coordinated fraud (giving 0.01-0.08 scores to syndicate members), while a 2-hop graph traversal instantly exposes the syndicate.
- **Separation of Policy and Reasoning**: Hardcoding approval routing rules while allowing the agent to synthesize evidence prevents policy breaches and hallucinations.

### What We Would Improve with More Time:
1. **Real-time Streaming Graph Ingestion**: Connect TigerGraph with Apache Kafka to update device and region edges in sub-second streaming latency.
2. **Community Detection Algorithms**: Run TigerGraph Louvain or Weakly Connected Components (WCC) across the global transaction graph to proactively identify emerging fraud rings before alerts fire.
3. **Voice/SMS Interactive Agent**: Connect customer verification directly to an automated conversational voice agent for live biometric verification.

---
*Built with TigerGraph, GSQL, Python, and Streamlit for Hacker House Goa 2026.*
