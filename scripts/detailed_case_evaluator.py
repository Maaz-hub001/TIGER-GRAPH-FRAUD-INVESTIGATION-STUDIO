import pandas as pd
import numpy as np

txns = pd.read_csv('data/benchmark_customers_txns.csv')
cases = pd.read_csv('data/case_pack.csv')
ident = pd.read_csv('data/identity.csv')
closed = pd.read_csv('data/closed_cases_history.csv')

ident['device_profile'] = ident['DeviceInfo'].fillna('') + ' | ' + ident['id_30'].fillna('') + ' | ' + ident['id_31'].fillna('') + ' | ' + ident['id_33'].fillna('')
txns = pd.merge(txns, ident[['TransactionID', 'device_profile', 'DeviceInfo', 'DeviceType', 'id_15', 'id_23', 'id_30', 'id_31', 'id_33']], on='TransactionID', how='left')
txns['ts_dt'] = pd.to_datetime(txns['ts'])

print("Analyzing 20 benchmark cases...")
for idx, r in cases.iterrows():
    cid = r['case_id']
    cust = r['customer_id']
    card = r['card_id']
    flg = r['flagged_txn_id']
    trig = r['trigger_type']
    score = r['risk_score']
    text = r['trigger_text']
    
    flg_row = txns[txns['TransactionID'] == flg].iloc[0]
    flg_ts = flg_row['ts_dt']
    flg_amt = flg_row['TransactionAmt']
    flg_reg = flg_row['addr1']
    flg_chan = flg_row['channel']
    flg_dev = flg_row['device_profile']
    flg_id15 = flg_row['id_15']
    
    # Customer overall history
    cust_txns = txns[txns['customer_id'] == cust].sort_values('ts_dt')
    top_regs = cust_txns['addr1'].value_counts()
    primary_reg = top_regs.index[0] if len(top_regs) > 0 else np.nan
    
    # Window +/- 48h
    w = cust_txns[(cust_txns['ts_dt'] >= flg_ts - pd.Timedelta(hours=48)) & (cust_txns['ts_dt'] <= flg_ts + pd.Timedelta(hours=48))]
    
    # Check testing pattern (sub-$5 authorizations within 1 hour before flagged txn)
    sub5_hour = cust_txns[(cust_txns['ts_dt'] >= flg_ts - pd.Timedelta(hours=1)) & (cust_txns['ts_dt'] <= flg_ts) & (cust_txns['TransactionAmt'] < 5.0)]
    
    # Check recurring charges (same amount on similar days of month)
    same_amt = cust_txns[np.isclose(cust_txns['TransactionAmt'], flg_amt, atol=0.01)]
    
    print(f"\n--- {cid} (Flagged {flg}, Score {score}, {trig}) ---")
    print(f"Trigger: {text}")
    print(f"Flagged: {flg_ts} | ${flg_amt} | {flg_chan} | Addr1: {flg_reg} (Cust Primary Addr1: {primary_reg}, counts: {dict(top_regs.head(3))})")
    print(f"Device: {flg_dev} | id_15: {flg_id15}")
    print(f"Window +/- 48h txns count: {len(w)}")
    if len(sub5_hour) > 0:
        print(f"Testing sequence sub-$5 in 1h: {len(sub5_hour)} txns -> {sub5_hour['TransactionAmt'].tolist()}")
    if len(same_amt) > 1:
        print(f"Recurring charges count with amount ${flg_amt}: {len(same_amt)} across dates: {same_amt['ts'].str[:10].tolist()}")
    
    # Check device sharing across all identity
    if pd.notna(flg_dev) and flg_dev.strip(' |'):
        clean_dev = flg_dev.strip(' |')
        dev_matches = ident[ident['device_profile'] == flg_dev]
        if len(dev_matches) > 1:
            print(f"SHARED DEVICE ALERT: {len(dev_matches)} transactions share device profile '{clean_dev}'!")
