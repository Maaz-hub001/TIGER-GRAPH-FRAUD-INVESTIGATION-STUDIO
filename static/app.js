// TigerGraph Agentic Fraud Studio - Client Controller
let currentCaseId = "HHG-014";
let network = null;
let allCases = [];
let isPhysicsEnabled = true;
let currentFilter = "all";
let currentGraphData = null;

document.addEventListener("DOMContentLoaded", () => {
    initApp();
});

async function initApp() {
    setupTabSwitching();
    setupGraphControls();
    setupFilterChips();
    setupNodeInspector();
    await loadSystemStatus();
    await loadCasesList();
    await selectCase(currentCaseId);
}

// 1. Load System Telemetry
async function loadSystemStatus() {
    try {
        const res = await fetch("/api/status");
        const data = await res.json();
        const statusText = document.getElementById("engineStatusText");
        statusText.textContent = `${data.engine}: Online (${data.total_transactions.toLocaleString()} Txns / ${data.total_identities.toLocaleString()} Devs)`;
    } catch (e) {
        console.error("Failed to load status:", e);
    }
}

// 2. Load Cases Queue
async function loadCasesList() {
    try {
        const res = await fetch("/api/cases");
        const data = await res.json();
        allCases = data.cases || [];
        applyCaseFilters();

        // Update Header Stats
        const fraudCount = allCases.filter(c => c.verdict === "fraud").length;
        const legitCount = allCases.filter(c => c.verdict === "legitimate").length;
        const totalExp = allCases.reduce((acc, c) => acc + (c.exposure_usd || 0), 0);
        const sarCount = allCases.filter(c => c.sar_filed).length;

        document.getElementById("statBenchmark").textContent = allCases.length;
        document.getElementById("statFraud").textContent = fraudCount;
        document.getElementById("statLegit").textContent = legitCount;
        document.getElementById("statExposure").textContent = `$${totalExp.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        document.getElementById("statSAR").textContent = sarCount;
    } catch (e) {
        console.error("Failed to load cases:", e);
    }
}

function renderCaseList(cases) {
    const container = document.getElementById("caseListContainer");
    container.innerHTML = "";

    cases.forEach(c => {
        const card = document.createElement("div");
        card.className = `case-card ${c.case_id === currentCaseId ? "active" : ""}`;
        card.dataset.caseId = c.case_id;

        const triggerClass = c.trigger_type || "risk_score";
        const verdictClass = c.verdict || "uncertain";

        card.innerHTML = `
            <div class="case-card-header">
                <span class="case-id-badge">${c.case_id}</span>
                <span class="trigger-chip ${triggerClass}">${c.trigger_type.replace('_', ' ')}</span>
            </div>
            <div class="case-card-body">
                <div><strong>Card:</strong> ${c.card_id} (${c.customer_id})</div>
                <div><strong>Flagged Txn:</strong> #${c.flagged_txn_id}</div>
            </div>
            <div class="case-card-footer">
                <span class="verdict-tag ${verdictClass}">${c.verdict.toUpperCase()}</span>
                <span>${c.exposure_usd > 0 ? '$' + c.exposure_usd.toFixed(2) : '$0.00'}</span>
            </div>
        `;

        card.addEventListener("click", () => selectCase(c.case_id));
        container.appendChild(card);
    });

    document.getElementById("caseCountBadge").textContent = `${cases.length} Cases`;
}

// 3. Filter Chips and Search
function setupFilterChips() {
    document.querySelectorAll(".q-chip").forEach(chip => {
        chip.addEventListener("click", () => {
            document.querySelectorAll(".q-chip").forEach(c => c.classList.remove("active"));
            chip.classList.add("active");
            currentFilter = chip.dataset.filter;
            applyCaseFilters();
        });
    });
}

function applyCaseFilters() {
    const q = (document.getElementById("caseSearchInput").value || "").toLowerCase();
    let filtered = allCases.filter(c => {
        const textMatch = !q || 
            c.case_id.toLowerCase().includes(q) ||
            c.customer_id.toLowerCase().includes(q) ||
            c.pattern.toLowerCase().includes(q) ||
            c.verdict.toLowerCase().includes(q);
        if (!textMatch) return false;

        if (currentFilter === "all") return true;
        if (currentFilter === "fraud") return c.verdict === "fraud";
        if (currentFilter === "legitimate") return c.verdict === "legitimate";
        if (currentFilter === "syndicate") {
            return c.pattern === "undocumented" || c.case_id === "HHG-008" || c.case_id === "HHG-014";
        }
        return true;
    });
    renderCaseList(filtered);
}

// 4. Select and Load Case Details
async function selectCase(caseId) {
    currentCaseId = caseId;

    // Highlight card in queue
    document.querySelectorAll(".case-card").forEach(el => {
        el.classList.toggle("active", el.dataset.caseId === caseId);
    });

    document.getElementById("graphActiveCaseTag").textContent = `Active: ${caseId}`;
    document.getElementById("nodeInspector").style.display = "none";

    try {
        const [caseRes, graphRes] = await Promise.all([
            fetch(`/api/cases/${caseId}`),
            fetch(`/api/graph/${caseId}`)
        ]);

        const caseData = await caseRes.json();
        const graphData = await graphRes.json();
        currentGraphData = graphData;

        renderCaseDetail(caseData);
        renderGraph(graphData);
    } catch (e) {
        console.error(`Failed to select case ${caseId}:`, e);
    }
}

// 5. Render Case Detail in Right Panel
function renderCaseDetail(data) {
    const caseObj = data.case;
    const nba = data.next_best_actions;
    const sar = data.sar;

    // Banner
    const isFraud = caseObj.verdict === "fraud";
    const banner = document.getElementById("verdictBanner");
    banner.className = `verdict-banner ${isFraud ? "" : "legitimate"}`;
    
    document.getElementById("verdictTitle").textContent = isFraud ? "FRAUD CONFIRMED" : "CLEARED AS LEGITIMATE";
    document.getElementById("verdictProb").textContent = `P(Fraud): ${caseObj.fraud_probability.toFixed(2)}`;
    document.getElementById("verdictMeta").innerHTML = `Pattern: <code>${caseObj.pattern}</code> | Exposure: $${caseObj.exposure_usd.toFixed(2)} | Graph ID: <code>${caseObj.graph_case_id}</code>`;

    // Stepper Details
    document.getElementById("stepTriggerDetail").textContent = data.stop_reason || "Investigation triggered by bank alert stream.";
    
    // Connected cards indicator
    const connCards = caseObj.connected_card_ids || [];
    const syndicateTag = document.getElementById("syndicateAlertTag");
    if (connCards.length >= 5) {
        syndicateTag.style.display = "inline-flex";
        syndicateTag.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> ${connCards.length}-Card Syndicate Ring`;
        document.getElementById("stepGraphDetail").textContent = `TigerGraph multi-hop traversal uncovered ${connCards.length} connected cards sharing device profile '${caseObj.connected_device_profiles[0]}'.`;
    } else {
        syndicateTag.style.display = "none";
        document.getElementById("stepGraphDetail").textContent = `Graph traversal complete. ${caseObj.evidence.length} evidence connections gathered from customer history and devices.`;
    }

    // Initial Actions
    const initContainer = document.getElementById("initialActionPills");
    initContainer.innerHTML = "";
    (nba.initial || []).forEach(act => {
        const pill = document.createElement("div");
        pill.className = "action-pill";
        pill.innerHTML = `
            <strong>${act.action}</strong>
            <span class="badge-${act.route.toLowerCase()}">${act.route}</span>
        `;
        initContainer.appendChild(pill);
    });

    // Evidence Requests
    const evReqs = data.evidence_requests || [];
    if (evReqs.length > 0) {
        document.getElementById("stepEvidenceDetail").textContent = `${evReqs[0].type}: ${evReqs[0].assumed_response}`;
    } else {
        document.getElementById("stepEvidenceDetail").textContent = "No additional evidence required under policy threshold.";
    }

    // Final Actions
    const finalContainer = document.getElementById("finalActionPills");
    finalContainer.innerHTML = "";
    (nba.final || []).forEach(act => {
        const pill = document.createElement("div");
        pill.className = "action-pill";
        pill.innerHTML = `
            <strong>${act.action}</strong>
            <span class="badge-${act.route.toLowerCase()}">${act.route}</span>
        `;
        finalContainer.appendChild(pill);
    });

    document.getElementById("whatChangedText").textContent = `What Changed: ${nba.what_changed || 'Actions settled after evidence evaluation.'}`;
    document.getElementById("stepWritebackDetail").textContent = `Committed to TigerGraph memory as vertex ${caseObj.graph_case_id} (written_to_graph = true).`;

    // Evidence Accordion
    const evList = document.getElementById("evidenceList");
    evList.innerHTML = "";
    (caseObj.evidence || []).forEach((ev, idx) => {
        const item = document.createElement("div");
        item.style.cssText = "background:rgba(15,23,42,0.6); border:1px solid #334155; padding:10px; border-radius:6px; margin-bottom:8px; font-size:11.5px;";
        item.innerHTML = `
            <div style="font-weight:700; color:#fff; margin-bottom:4px;"><i class="fa-solid fa-link" style="color:#38bdf8;"></i> Evidence #${idx+1}</div>
            <div style="color:#94a3b8; line-height:1.4;">${ev.claim}</div>
            <div style="margin-top:6px; font-family:'JetBrains Mono'; font-size:10px; color:#38bdf8;">Source: ${ev.source} | Ref: ${ev.ref}</div>
        `;
        evList.appendChild(item);
    });

    // SAR Tab
    const sarHeader = document.getElementById("sarHeaderBanner");
    if (sar.file) {
        sarHeader.style.display = "flex";
        document.getElementById("sarStatusText").textContent = "Regulatory Filing Mandatory (Policy 3a)";
        document.getElementById("sarReasonText").textContent = sar.reason;
        document.getElementById("sarExposureText").textContent = `$${sar.total_amount_usd.toFixed(2)}`;
        document.getElementById("sarDateText").textContent = (sar.activity_dates || []).join(" to ");
        document.getElementById("sarSubjectsText").textContent = (sar.subjects || []).join(", ");
        document.getElementById("sarNarrativeBody").textContent = sar.narrative;
    } else {
        sarHeader.style.display = "flex";
        sarHeader.style.borderColor = "#10b981";
        sarHeader.style.background = "rgba(16, 185, 129, 0.15)";
        sarHeader.style.color = "#34d399";
        document.getElementById("sarStatusText").textContent = "Cleared — No Regulatory Filing Required";
        document.getElementById("sarReasonText").textContent = sar.reason;
        document.getElementById("sarExposureText").textContent = "$0.00";
        document.getElementById("sarDateText").textContent = "N/A";
        document.getElementById("sarSubjectsText").textContent = "None";
        document.getElementById("sarNarrativeBody").textContent = "No SAR required for this alert under Policy 3a.";
    }

    // Case Memory Precedents Tab
    const priorsList = document.getElementById("priorCasesList");
    priorsList.innerHTML = "";
    const priors = caseObj.similar_prior_cases || [];
    if (priors.length > 0) {
        priors.forEach(pid => {
            const el = document.createElement("div");
            el.style.cssText = "background:rgba(15,23,42,0.8); border:1px solid #334155; padding:12px; border-radius:6px; margin-bottom:10px;";
            el.innerHTML = `
                <div style="font-weight:700; color:#38bdf8; font-family:'JetBrains Mono';">Precedent: ${pid}</div>
                <div style="font-size:11.5px; color:#cbd5e1; margin-top:4px;">Historical closed investigation referenced from case memory.</div>
            `;
            priorsList.appendChild(el);
        });
    } else {
        priorsList.innerHTML = "<div style='font-size:12px; color:#64748b;'>No customer-specific historical precedents required for this alert.</div>";
    }

    // Governance Station Sign-off List
    const govList = document.getElementById("pendingApprovalsList");
    govList.innerHTML = "";
    (nba.final || []).forEach(act => {
        const item = document.createElement("div");
        item.style.cssText = "display:flex; align-items:center; justify-content:space-between; padding:8px 0; border-bottom:1px solid #1e293b;";
        
        let btnHtml = "";
        if (act.route === "L1") {
            btnHtml = `<button class="btn-approve" onclick="alert('L1 Team Lead Approval Recorded for ${act.action}')">Authorize (L1)</button>`;
        } else if (act.route === "L2") {
            btnHtml = `<button class="btn-approve" style="border-color:#f43f5e;" onclick="alert('L2 Fraud Manager Approval Recorded for ${act.action}')">Authorize (L2)</button>`;
        } else {
            btnHtml = `<span style="font-size:11px; color:#34d399;"><i class="fa-solid fa-check"></i> Executed</span>`;
        }

        item.innerHTML = `
            <div>
                <span class="badge-${act.route.toLowerCase()}">${act.route}</span>
                <strong style="font-size:12px; margin-left:6px; color:#fff;">${act.action}</strong>
            </div>
            ${btnHtml}
        `;
        govList.appendChild(item);
    });

    // Update Bottom GSQL Console text
    if (caseObj.connected_device_profiles && caseObj.connected_device_profiles.length > 0) {
        document.getElementById("gsqlCodeBox").textContent = `// Executing TigerGraph GSQL Algorithm
device_neighbors(device_id = "${caseObj.connected_device_profiles[0]}")
--> Traversed 2-hops: ${connCards.length} connected cards identified sharing hardware device profile.
write_case_to_graph(case_id = "${caseObj.graph_case_id}", status = "${caseObj.status}", verdict = "${caseObj.verdict}")
--> Committed case vertex and INVESTIGATES edges to FraudInvestigationGraph.`;
    } else {
        document.getElementById("gsqlCodeBox").textContent = `// Executing TigerGraph GSQL Algorithm
card_window(card_id = "${caseObj.connected_card_ids[0] || 'CARD'}", hours = 48)
--> Traversed 1-hop: Analyzed 48h temporal window on card.
customer_card_profile(customer_id = "${caseObj.connected_card_ids[0] ? caseObj.connected_card_ids[0].split('-')[0] : 'CUST'}")
--> Verified home billing region match against customer baseline.`;
    }
}

// 6. Render Vis.js Network Graph
function renderGraph(graphData) {
    const container = document.getElementById("networkCanvas");

    // Augment nodes with rich styling and glowing shadows
    const styledNodes = graphData.nodes.map(n => {
        const copy = Object.assign({}, n);
        copy.borderWidth = 2;
        if (n.group === "customer") {
            copy.color = { background: "#0284c7", border: "#38bdf8", highlight: { background: "#38bdf8", border: "#fff" } };
            copy.shadow = { enabled: true, color: 'rgba(56, 189, 248, 0.4)', size: 12 };
        } else if (n.group === "card") {
            copy.color = { background: "#7e22ce", border: "#c084fc", highlight: { background: "#a855f7", border: "#fff" } };
            copy.shadow = { enabled: true, color: 'rgba(168, 85, 247, 0.4)', size: 10 };
        } else if (n.group === "transaction") {
            const isRed = n.color === "#ef4444";
            copy.color = { 
                background: isRed ? "#b91c1c" : "#047857", 
                border: isRed ? "#ef4444" : "#10b981",
                highlight: { background: isRed ? "#ef4444" : "#10b981", border: "#fff" }
            };
            copy.shadow = { enabled: true, color: isRed ? 'rgba(239, 68, 68, 0.6)' : 'rgba(16, 185, 129, 0.6)', size: 14 };
        } else if (n.group === "device") {
            copy.color = { background: "#0e7490", border: "#22d3ee", highlight: { background: "#06b6d4", border: "#fff" } };
            copy.shadow = { enabled: true, color: 'rgba(6, 182, 212, 0.4)', size: 10 };
        } else if (n.group === "syndicate") {
            copy.color = { background: "#be123c", border: "#fda4af", highlight: { background: "#f43f5e", border: "#fff" } };
            copy.shadow = { enabled: true, color: 'rgba(244, 63, 94, 0.8)', size: 22 };
        } else if (n.group === "fraud_case") {
            copy.color = { background: "#a16207", border: "#fde047", highlight: { background: "#eab308", border: "#fff" } };
            copy.shadow = { enabled: true, color: 'rgba(234, 179, 8, 0.5)', size: 10 };
        } else if (n.group === "connected_card") {
            copy.color = { background: "#4c0519", border: "#f43f5e" };
            copy.shadow = { enabled: true, color: 'rgba(244, 63, 94, 0.3)', size: 6 };
        }
        return copy;
    });

    const data = {
        nodes: new vis.DataSet(styledNodes),
        edges: new vis.DataSet(graphData.edges)
    };

    const options = {
        nodes: {
            font: { color: '#f8fafc', face: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', size: 10.5, strokeWidth: 3, strokeColor: '#070a13' }
        },
        edges: {
            width: 2,
            font: { color: '#94a3b8', size: 9.5, face: 'Consolas, monospace', align: 'middle', strokeWidth: 3, strokeColor: '#070a13' },
            arrows: { to: { enabled: true, scaleFactor: 0.6 } },
            smooth: { type: 'continuous' }
        },
        physics: {
            enabled: isPhysicsEnabled,
            solver: 'forceAtlas2Based',
            forceAtlas2Based: {
                gravitationalConstant: -95,
                centralGravity: 0.018,
                springLength: 150,
                springConstant: 0.07,
                damping: 0.35
            },
            stabilization: { iterations: 140 }
        },
        interaction: {
            hover: true,
            tooltipDelay: 100,
            zoomView: true
        }
    };

    if (network) {
        network.destroy();
    }

    network = new vis.Network(container, data, options);

    // Auto fit upon stabilization with generous padding
    network.once("stabilizationIterationsDone", () => {
        network.fit({ 
            animation: { duration: 600, easingFunction: "easeInOutQuad" },
            padding: 55
        });
    });

    setTimeout(() => {
        if (network) network.fit({ padding: 55 });
    }, 400);

    // Click on node opens inspector
    network.on("click", (params) => {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const nodeData = graphData.nodes.find(n => n.id === nodeId);
            showNodeInspector(nodeData);
        } else {
            document.getElementById("nodeInspector").style.display = "none";
        }
    });
}

function showNodeInspector(node) {
    if (!node) return;
    const inspector = document.getElementById("nodeInspector");
    const title = document.getElementById("inspectorTitle");
    const body = document.getElementById("inspectorBody");

    inspector.style.display = "block";
    title.innerHTML = `<i class="fa-solid fa-circle-nodes"></i> Entity: ${node.id}`;

    let details = `
        <div><strong>Type:</strong> <span style="text-transform:uppercase; color:#38bdf8;">${node.group}</span></div>
        <div style="margin-top:6px;"><strong>Identifier:</strong> <code>${node.id}</code></div>
    `;

    if (node.group === "customer") {
        details += `<div style="margin-top:6px; color:#94a3b8;">Primary customer record linked across card accounts and identity profiles.</div>`;
    } else if (node.group === "card") {
        details += `<div style="margin-top:6px; color:#94a3b8;">Card payment account evaluated under temporal transaction window.</div>`;
    } else if (node.group === "transaction") {
        details += `<div style="margin-top:6px; color:#94a3b8;">Flagged transaction event intercepted by fraud detection monitoring stream.</div>`;
    } else if (node.group === "device") {
        details += `<div style="margin-top:6px; color:#94a3b8;">Hardware/OS fingerprint signature evaluated via GSQL <code>device_neighbors</code> traversal.</div>`;
    } else if (node.group === "syndicate") {
        const connectedCards = (currentGraphData.nodes || [])
            .filter(n => n.group === "connected_card")
            .map(n => n.id);
        
        details += `
            <div style="margin-top:8px; padding:10px; background:rgba(244,63,94,0.18); border:1px solid rgba(244,63,94,0.5); border-radius:6px;">
                <div style="color:#fb7185; font-weight:800; font-size:12px; margin-bottom:4px;"><i class="fa-solid fa-triangle-exclamation"></i> Multi-Card Fraud Syndicate Ring</div>
                <div style="font-size:11px; color:#cbd5e1; line-height:1.4;">Uncovered via GSQL <code>device_neighbors</code> 2-hop traversal. Multiple unrelated external cardholders exploited across single hardware emulator signature.</div>
            </div>
            <div style="margin-top:10px;">
                <strong style="font-size:11px; color:#38bdf8;">Exploited Connected Cards (${connectedCards.length}):</strong>
                <div style="margin-top:6px; display:flex; flex-wrap:wrap; gap:4px; max-height:130px; overflow-y:auto; padding-right:4px;">
                    ${connectedCards.map(c => `<span style="background:#1e293b; border:1px solid #475569; padding:2px 6px; border-radius:4px; font-family:'JetBrains Mono',monospace; font-size:10px; color:#f8fafc;">${c}</span>`).join('')}
                </div>
            </div>
            <div style="margin-top:12px; padding-top:8px; border-top:1px solid #334155; font-size:11px;">
                <div><span class="badge-l1">L1</span> <strong>Action:</strong> BLOCK_CARD</div>
                <div style="margin-top:4px;"><span class="badge-l2">L2</span> <strong>Action:</strong> FILE_REPORT (FinCEN SAR)</div>
                <div style="margin-top:4px;"><span class="badge-auto">auto</span> <strong>Action:</strong> MONITOR_CONNECTED_CARDS</div>
            </div>
        `;
    } else if (node.group === "fraud_case") {
        details += `<div style="margin-top:6px; color:#fde047;">Persisted TigerGraph vertex created via autonomous writeback loop.</div>`;
    }

    body.innerHTML = details;
}

function setupNodeInspector() {
    document.getElementById("btnCloseInspector").addEventListener("click", () => {
        document.getElementById("nodeInspector").style.display = "none";
    });
}

// 7. UI Controls & Tab Switching
function setupTabSwitching() {
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

            btn.classList.add("active");
            const tabId = btn.dataset.tab;
            document.getElementById(tabId).classList.add("active");
        });
    });

    // Copy SAR Button
    document.getElementById("btnCopySAR").addEventListener("click", () => {
        const text = document.getElementById("sarNarrativeBody").textContent;
        navigator.clipboard.writeText(text);
        alert("FinCEN SAR Narrative copied to clipboard!");
    });

    // Case Search Filter
    document.getElementById("caseSearchInput").addEventListener("input", () => {
        applyCaseFilters();
    });

    window.addEventListener("resize", () => {
        if (network) network.fit();
    });
}

function setupGraphControls() {
    document.getElementById("btnFitGraph").addEventListener("click", () => {
        if (network) network.fit({ animation: { duration: 500 } });
    });

    document.getElementById("btnTogglePhysics").addEventListener("click", () => {
        isPhysicsEnabled = !isPhysicsEnabled;
        if (network) network.setOptions({ physics: { enabled: isPhysicsEnabled } });
    });

    // Interactive Syndicate Ring Button
    const syndicateTag = document.getElementById("syndicateAlertTag");
    if (syndicateTag) {
        syndicateTag.addEventListener("click", () => {
            focusSyndicateRing();
        });
    }

    document.getElementById("btnRerunInvestigate").addEventListener("click", async () => {
        const btn = document.getElementById("btnRerunInvestigate");
        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Reasoning...`;
        btn.disabled = true;

        try {
            await fetch(`/api/investigate/${currentCaseId}`, { method: "POST" });
            await selectCase(currentCaseId);
            await loadCasesList();
        } catch (e) {
            console.error("Re-run failed:", e);
        } finally {
            btn.innerHTML = `<i class="fa-solid fa-bolt"></i> Re-Run Agent`;
            btn.disabled = false;
        }
    });
}

function focusSyndicateRing() {
    if (!network || !currentGraphData) return;
    const ringNode = currentGraphData.nodes.find(n => n.group === "syndicate");
    if (ringNode) {
        network.focus(ringNode.id, {
            scale: 1.15,
            animation: { duration: 750, easingFunction: "easeInOutQuad" }
        });
        const ringClusterIds = currentGraphData.nodes
            .filter(n => n.group === "connected_card" || n.id === ringNode.id)
            .map(n => n.id);
        network.selectNodes(ringClusterIds, true);
        showNodeInspector(ringNode);
    }
}
