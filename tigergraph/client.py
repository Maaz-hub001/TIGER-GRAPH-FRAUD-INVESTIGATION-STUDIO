"""
TigerGraph Client Interface
Provides a unified abstraction over TigerGraph Savanna / Community Edition and
an embedded high-performance local Graph Engine for offline execution and testing.
"""

import os
import pandas as pd
import numpy as np
import networkx as nx
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

try:
    import pyTigerGraph as tg
except ImportError:
    tg = None


class TigerGraphClient:
    def __init__(self,
                 host: Optional[str] = None,
                 graphname: str = "FraudInvestigationGraph",
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 token: Optional[str] = None,
                 data_dir: str = "data"):
        
        self.host = host or os.environ.get("TG_HOST")
        self.graphname = graphname or os.environ.get("TG_GRAPH", "FraudInvestigationGraph")
        self.username = username or os.environ.get("TG_USERNAME", "tigergraph")
        self.password = password or os.environ.get("TG_PASSWORD", "tigergraph")
        self.token = token or os.environ.get("TG_TOKEN")
        self.data_dir = data_dir
        
        self.conn = None
        self.is_live = False
        self.local_graph = nx.MultiDiGraph()
        self.written_cases = {}
        
        # Try live connection if host is specified
        if self.host and tg:
            try:
                self.conn = tg.TigerGraphConnection(
                    host=self.host,
                    graphname=self.graphname,
                    username=self.username,
                    password=self.password,
                    apiToken=self.token
                )
                # Test ping
                res = self.conn.echo()
                if "TigerGraph" in str(res) or "Hello" in str(res):
                    self.is_live = True
                    print(f"Connected to live TigerGraph Savanna instance at {self.host}")
            except Exception as e:
                print(f"Could not connect to live TigerGraph ({e}). Falling back to Embedded Graph Engine.")
                self.is_live = False
        
        # Initialize the embedded graph engine data structures
        self._init_embedded_engine()

    def _init_embedded_engine(self):
        """Loads index structures for rapid graph traversals."""
        # 1. Load benchmark transactions (and full if needed)
        txns_path = os.path.join(self.data_dir, "benchmark_customers_txns.csv")
        if not os.path.exists(txns_path):
            txns_path = os.path.join(self.data_dir, "transactions.csv")
            
        print(f"Loading transaction index from {txns_path}...")
        self.txns_df = pd.read_csv(txns_path)
        if 'ts' in self.txns_df.columns:
            self.txns_df['ts_dt'] = pd.to_datetime(self.txns_df['ts'])
            
        # 2. Load Identity records
        ident_path = os.path.join(self.data_dir, "identity.csv")
        print(f"Loading identity index from {ident_path}...")
        self.ident_df = pd.read_csv(ident_path)
        
        # Build device profile string: DeviceInfo | id_30 | id_31 | id_33
        self.ident_df['device_profile'] = (
            self.ident_df['DeviceInfo'].fillna('') + ' | ' +
            self.ident_df['id_30'].fillna('') + ' | ' +
            self.ident_df['id_31'].fillna('') + ' | ' +
            self.ident_df['id_33'].fillna('')
        )
        
        # Merge device profile into txns_df
        self.txns_df = pd.merge(
            self.txns_df,
            self.ident_df[['TransactionID', 'device_profile', 'DeviceInfo', 'DeviceType', 'id_15', 'id_23', 'id_30', 'id_31', 'id_33']],
            on='TransactionID',
            how='left'
        )
        
        # 3. Load Closed Cases History (Case Memory)
        cc_path = os.path.join(self.data_dir, "closed_cases_history.csv")
        print(f"Loading closed cases history from {cc_path}...")
        self.closed_cases_df = pd.read_csv(cc_path)
        
        # Build rapid lookup indices
        self.device_to_txns = {}
        for dev, group in self.ident_df.groupby('device_profile'):
            clean_dev = dev.strip(' |')
            if clean_dev:
                self.device_to_txns[clean_dev] = group['TransactionID'].tolist()
                
        print(f"Embedded Graph Engine initialized. Graph loaded with {len(self.txns_df)} transactions, {len(self.ident_df)} identities, and {len(self.closed_cases_df)} closed cases.")

    def get_card_window(self, card_id: str, target_ts_str: str, hours_before: int = 48, hours_after: int = 48) -> List[Dict[str, Any]]:
        """
        GSQL Query equivalent: card_window(card_id, target_ts, hours_before, hours_after)
        Traverses Card -> MADE -> Transaction within the time delta.
        """
        if self.is_live:
            try:
                res = self.conn.runInstalledQuery("card_window", {
                    "card_id": card_id,
                    "target_ts": target_ts_str,
                    "hours_before": hours_before,
                    "hours_after": hours_after
                })
                return res[0]["Txns"]
            except Exception as e:
                print(f"Live GSQL error ({e}), using embedded query.")

        # Embedded implementation
        target_dt = pd.to_datetime(target_ts_str)
        t_min = target_dt - timedelta(hours=hours_before)
        t_max = target_dt + timedelta(hours=hours_after)
        
        # Filter by customer/card prefix if card_id is customer-based
        cust_id = card_id.split("-")[0] if "-" in card_id else card_id
        cust_matches = self.txns_df[self.txns_df['customer_id'] == cust_id]
        
        window = cust_matches[(cust_matches['ts_dt'] >= t_min) & (cust_matches['ts_dt'] <= t_max)].sort_values('ts_dt')
        return window.to_dict(orient='records')

    def get_device_neighbors(self, device_profile_str: str) -> Dict[str, Any]:
        """
        GSQL Query equivalent: device_neighbors(device_id)
        2-hop graph traversal: DeviceProfile <- FROM_DEVICE - Transaction <- MADE - Card <- OWNS - Customer
        Detects coordinated syndicates, multi-card sharing, and fraud rings.
        """
        clean_dev = device_profile_str.strip(' |')
        if not clean_dev:
            return {"connected_cards": [], "connected_customers": [], "total_shared_txns": 0, "txn_ids": []}

        if self.is_live:
            try:
                res = self.conn.runInstalledQuery("device_neighbors", {"device_id": clean_dev})
                return {
                    "connected_cards": [c["card_id"] for c in res[1]["ConnectedCards"]],
                    "connected_customers": [cust["customer_id"] for cust in res[2]["ConnectedCustomers"]],
                    "total_shared_txns": res[3]["total_shared_txns"]
                }
            except Exception as e:
                pass

        # Embedded implementation
        # Check if pre-computed global device index exists
        idx_path = os.path.join(self.data_dir, "device_index.json")
        if os.path.exists(idx_path):
            if not hasattr(self, "_global_dev_index"):
                import json
                with open(idx_path, "r", encoding="utf-8") as f:
                    self._global_dev_index = json.load(f)
            
            if clean_dev in self._global_dev_index:
                dev_data = self._global_dev_index[clean_dev]
                return {
                    "device_profile": clean_dev,
                    "connected_cards": dev_data["cards"],
                    "connected_customers": dev_data["customers"],
                    "total_shared_txns": dev_data["total_shared_txns"],
                    "sample_txn_ids": dev_data.get("sample_txns", [])
                }

        txn_ids = self.device_to_txns.get(clean_dev, [])
        if not txn_ids:
            return {"connected_cards": [], "connected_customers": [], "total_shared_txns": 0, "txn_ids": []}

        # Check transactions
        matched_txns = self.txns_df[self.txns_df['TransactionID'].isin(txn_ids)]
        connected_customers = matched_txns['customer_id'].unique().tolist()
        connected_cards = [f"{c}-K1" for c in connected_customers if c]
        
        return {
            "device_profile": clean_dev,
            "connected_cards": connected_cards,
            "connected_customers": connected_customers,
            "total_shared_txns": len(txn_ids),
            "sample_txn_ids": txn_ids[:10]
        }

    def get_customer_card_profile(self, customer_id: str) -> Dict[str, Any]:
        """
        GSQL Query equivalent: customer_card_profile(customer_id)
        Aggregates customer's home region, channel mix, multi-card links, and historical behavior.
        """
        cust_txns = self.txns_df[self.txns_df['customer_id'] == customer_id]
        if len(cust_txns) == 0:
            return {"customer_id": customer_id, "lifetime_txns": 0, "top_regions": [], "channels": {}}

        top_regions = cust_txns['addr1'].dropna().value_counts().head(5).to_dict()
        channels = cust_txns['channel'].value_counts().to_dict()
        avg_amt = cust_txns['TransactionAmt'].mean()
        max_amt = cust_txns['TransactionAmt'].max()
        
        return {
            "customer_id": customer_id,
            "lifetime_txns": len(cust_txns),
            "top_regions": top_regions,
            "channels": channels,
            "avg_amount": round(float(avg_amt), 2),
            "max_amount": round(float(max_amt), 2),
            "first_seen": str(cust_txns['ts'].min()),
            "last_seen": str(cust_txns['ts'].max())
        }

    def find_similar_closed_cases(self,
                                  pattern: Optional[str] = None,
                                  customer_id: Optional[str] = None,
                                  card_id: Optional[str] = None,
                                  limit: int = 5) -> List[Dict[str, Any]]:
        """
        GSQL Query equivalent: find_similar_cases(...)
        Retrieves relevant historical investigations from case memory.
        """
        df = self.closed_cases_df
        matches = []

        # 1. Exact customer prior cases
        if customer_id:
            cust_matches = df[df['customer_id'] == customer_id]
            if len(cust_matches) > 0:
                matches.extend(cust_matches.to_dict(orient='records'))

        # 2. Similar pattern cases
        if pattern and pattern not in ['none', 'undocumented']:
            pattern_matches = df[df['pattern'] == pattern].sort_values('exposure_usd', ascending=False)
            matches.extend(pattern_matches.head(limit).to_dict(orient='records'))

        # Deduplicate by case_id
        seen = set()
        unique_matches = []
        for m in matches:
            if m['case_id'] not in seen:
                seen.add(m['case_id'])
                unique_matches.append(m)
                if len(unique_matches) >= limit:
                    break

        return unique_matches

    def write_case_to_graph(self,
                            case_id: str,
                            status: str,
                            verdict: str,
                            fraud_probability: float,
                            pattern: str,
                            exposure_usd: float,
                            summary: str,
                            card_id: str,
                            flagged_txn_id: Any,
                            connected_cards: Optional[List[str]] = None,
                            connected_devices: Optional[List[str]] = None) -> str:
        """
        GSQL Query equivalent: write_case_to_graph(...)
        Writes the dynamic fraud investigation vertex and incident edges into TigerGraph memory.
        """
        graph_case_id = f"CASE-2016-{case_id.replace('HHG-', '9')}"
        
        record = {
            "graph_case_id": graph_case_id,
            "case_id": case_id,
            "status": status,
            "verdict": verdict,
            "fraud_probability": fraud_probability,
            "pattern": pattern,
            "exposure_usd": exposure_usd,
            "summary": summary,
            "card_id": card_id,
            "flagged_txn_id": str(flagged_txn_id),
            "connected_cards": connected_cards or [],
            "connected_devices": connected_devices or [],
            "written_at": datetime.now().isoformat()
        }
        
        self.written_cases[case_id] = record
        
        # Add to local NetworkX graph structure
        self.local_graph.add_node(graph_case_id, type="FraudCase", **record)
        self.local_graph.add_edge(graph_case_id, card_id, type="INVESTIGATES")
        self.local_graph.add_edge(graph_case_id, str(flagged_txn_id), type="FLAGS")
        
        for cc in (connected_cards or []):
            self.local_graph.add_edge(graph_case_id, cc, type="CONNECTED_CARD")
            
        for dev in (connected_devices or []):
            self.local_graph.add_edge(graph_case_id, dev, type="CONNECTED_DEVICE")

        return graph_case_id
