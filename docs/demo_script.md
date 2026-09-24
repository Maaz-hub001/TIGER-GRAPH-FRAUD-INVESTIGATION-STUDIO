# 3–5 Minute End-to-End Demo Video Script

**Title**: Autonomous Fraud Investigation & Next-Best Action with TigerGraph  
**Presenter**: Team Lead  
**Target Duration**: 3:30 – 4:30 minutes  

---

### Segment 1: Introduction & Problem Statement (0:00 – 0:45)
- **Visual**: Start with the Streamlit Analyst Studio home screen showing the Top Metrics Bar (20 Cases, Confirmed Fraud, Cleared Legit, Total Exposure, Regulatory SARs).
- **Narration**:
  > *"Hello judges and the TigerGraph community! Fraud investigation teams at financial institutions are under immense pressure. Analysts manually spend hours piecing together transaction histories, IP connections, device records, and past case files—often after money has already left the bank.*
  >
  > *Furthermore, isolated machine learning risk scores are notoriously noisy: legitimate travelers get blocked on weak signals, while coordinated syndicates slip under the radar with low individual transaction scores.*
  >
  > *Today, we present our solution: an **Autonomous Agentic Fraud Investigation System powered by TigerGraph, GSQL, and GraphRAG**. Our agent investigates uncertain alerts, traverses the knowledge graph to uncover hidden syndicates, consults 5,565 closed cases for memory, recommends next-best actions under strict governance approval routes, drafts regulatory SAR narratives, and commits resolved cases back into TigerGraph."*

---

### Segment 2: Architecture & TigerGraph Schema (0:45 – 1:30)
- **Visual**: Switch to Tab 2: "Knowledge Graph Subgraph" and show the system architecture diagram and interactive SVG/canvas node graph.
- **Narration**:
  > *"Let's look at the underlying architecture. We modeled the complete banking ecosystem in TigerGraph:*
  > *Customer nodes own Card nodes, Cards make Transactions, Transactions link to Device Profiles, Billing Regions, and Email Domains. Closed Cases from historical investigations form our initial graph memory, and dynamic Fraud Case vertices are written back as investigations conclude.*
  >
  > *We authored dedicated GSQL queries: `card_window` for analyzing temporal spend bursts, and `device_neighbors` for multi-hop syndicate detection.*
  >
  > *Now, let's watch the agent in action on real benchmark cases."*

---

### Segment 3: Investigating a Coordinated Syndicate Ring (HHG-014) (1:30 – 2:45)
- **Visual**: Select `HHG-014` from the sidebar dropdown.
- **Narration**:
  > *"Let's look at Case HHG-014. The trigger was an analyst request: several cards this month show activity from the same unusual device profile. The flagged transaction on card C13487-K1 was for $74.96.*
  >
  > *An isolated model would see a standard low-value transaction. But our agent executed a multi-hop graph traversal in TigerGraph on the device profile: `SM-G935F Build/NRD90M | Android 7.0 | chrome 62.0`.*
  >
  > *Instantly, TigerGraph revealed the full picture: this single device profile is shared across **52 distinct customer cards** and generated 114 transactions! This is a coordinated emulator testing farm.*
  >
  > *Notice the progression:*
  > 1. *Initial action: Under Rule R6, the agent immediately flagged the shared origin, recommending CREATE_CASE, FILE_REPORT, and MONITOR_CONNECTED_CARDS.*
  > 2. *Evidence request: It requested analyst confirmation.*
  > 3. *Final action: Following confirmation, the agent escalated under Policy Rule R9 with actions: BLOCK_CARD, CREATE_CASE, FILE_REPORT (routed to L2 Fraud Manager), and MONITOR_CONNECTED_CARDS for all 52 compromised accounts.*
  >
  > *Now look at Tab 4: The agent automatically synthesized a FinCEN-compliant Suspicious Activity Report (SAR) narrative covering the 5Ws and H—naming all subject accounts, devices, and total exposure."*

---

### Segment 4: Handling Legitimate False Alarms & Recurring Disputes (HHG-018) (2:45 – 3:35)
- **Visual**: Switch to `HHG-018` in the dropdown.
- **Narration**:
  > *"Now, what about the other half of the benchmark—the cases that look suspicious but are actually legitimate?*
  >
  > *In Case HHG-018, customer C02354 reported an unrecognized $39.08 charge. A naive bot would immediately block the card, causing customer friction.*
  >
  > *Our agent queried the customer's lifetime graph in TigerGraph and discovered something crucial: the customer has **32 identical monthly charges of $39.08** spanning 6 months!*
  >
  > *The agent recognized this as a textbook Rule R7 scenario: 'Disputed but legitimate recurring subscription'.*
  > *Instead of blocking, its initial recommendation followed policy: CREATE_CASE, VERIFY_WITH_CUSTOMER, and WARN_CUSTOMER.*
  > *Upon receiving the recurring charge reminder, the customer confirmed the subscription. The agent immediately cleared the alert to CLOSE_NO_FRAUD without blocking the card or filing an unnecessary SAR.*
  >
  > *This demonstrates true agentic uncertainty management."*

---

### Segment 5: Graph Memory & Governance Station (3:35 – 4:15)
- **Visual**: Navigate to Tab 3 (GraphRAG Case Memory) and Tab 5 (Policy Governance & Approval).
- **Narration**:
  > *"Every case closed by the agent is written directly into TigerGraph memory with a `FraudCase` vertex linked to the card and transactions. Under Tab 3, future investigations instantly retrieve these precedents using GraphRAG.*
  >
  > *Under Tab 5, we have our human-in-the-loop Governance Console. Routine actions execute automatically, while high-impact actions like card blocks over $2,500 or regulatory SAR filings cleanly pause for L1 Team Lead and L2 Fraud Manager sign-offs.*
  >
  > *We ran this agent across all 20 benchmark cases, and every single case generated a 100% compliant answer file in `cases/` that passed our strict automated validation test suite."*

---

### Segment 6: Conclusion (4:15 – 4:30)
- **Visual**: Return to the full dashboard overview with TigerGraph logo.
- **Narration**:
  > *"By combining TigerGraph's high-performance native graph traversals with agentic reasoning and policy governance, we turn noisy fraud signals into fast, defensible, and auditable financial action.*
  >
  > *Thank you!"*
