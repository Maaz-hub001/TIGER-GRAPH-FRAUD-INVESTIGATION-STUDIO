import pandas as pd
import numpy as np

txns = pd.read_csv('data/benchmark_customers_txns.csv')
cases = pd.read_csv('data/case_pack.csv')
ident = pd.read_csv('data/identity.csv')
closed = pd.read_csv('data/closed_cases_history.csv')

print(f"Total benchmark customer txns: {len(txns)}")

# Create device profile in identity
ident['device_profile'] = ident['DeviceInfo'].fillna('') + ' | ' + ident['id_30'].fillna('') + ' | ' + ident['id_31'].fillna('') + ' | ' + ident['id_33'].fillna('')

# Merge identity into txns
txns = pd.merge(txns, ident[['TransactionID', 'device_profile', 'DeviceInfo', 'DeviceType', 'id_15', 'id_23', 'id_30', 'id_31', 'id_33']], on='TransactionID', how='left')

for idx, case_row in cases.iterrows():
    cid = case_row['case_id']
    cust = case_row['customer_id']
    card = case_row['card_id']
    flg_id = case_row['flagged_txn_id']
    trig_type = case_row['trigger_type']
    trig_text = case_row['trigger_text']
    score = case_row['risk_score']
    
    cust_txns = txns[txns['customer_id'] == cust].sort_values('ts')
    flg_row = cust_txns[cust_txns['TransactionID'] == flg_id]
    
    print(f"\n=======================================================")
    print(f"CASE {cid} | Customer {cust} | Card {card} | Trigger: {trig_type} ({score})")
    print(f"Trigger Text: {trig_text}")
    
    if len(flg_row) > 0:
        fr = flg_row.iloc[0]
        print(f"Flagged Txn: {flg_id} at {fr['ts']} | ${fr['TransactionAmt']} | Chan: {fr['channel']} | Addr1: {fr['addr1']} | Product: {fr['ProductCD']} | Email: {fr['P_emaildomain']}")
        if pd.notna(fr['device_profile']) and fr['device_profile'].strip(' |'):
            print(f"Device Profile: {fr['device_profile']} (id_15: {fr['id_15']})")
    
    # Check customer history
    print(f"Customer total txns: {len(cust_txns)}")
    regions = cust_txns['addr1'].value_counts().to_dict()
    print(f"Top regions for {cust}: {list(regions.items())[:3]}")
    channels = cust_txns['channel'].value_counts().to_dict()
    print(f"Channels: {channels}")
    
    # Check prior closed cases
    cust_closed = closed[closed['customer_id'] == cust]
    if len(cust_closed) > 0:
        print(f"Prior closed cases for {cust}: {len(cust_closed)} case(s)")
        for _, c_row in cust_closed.iterrows():
            print(f"  -> {c_row['case_id']} ({c_row['opened_at']}): {c_row['outcome']} | {c_row['pattern']} | Exp: ${c_row['exposure_usd']} | Notes: {c_row['analyst_notes'][:100]}...")
    else:
        print(f"No prior closed cases for customer {cust}.")
