import pandas as pd

cases = pd.read_csv('data/case_pack.csv')
txns = pd.read_csv('data/benchmark_customers_txns.csv')
ident = pd.read_csv('data/identity.csv')

flagged_txns = txns[txns['TransactionID'].isin(cases['flagged_txn_id'])]
print('Found flagged txns in extracted data:', len(flagged_txns))

merged = pd.merge(cases, flagged_txns, left_on='flagged_txn_id', right_on='TransactionID', suffixes=('', '_txn'))
merged = pd.merge(merged, ident[['TransactionID', 'DeviceInfo', 'DeviceType', 'id_15', 'id_23', 'id_30', 'id_31', 'id_33']], on='TransactionID', how='left')

for idx, r in merged.iterrows():
    print(f"{r['case_id']}: Txn={r['flagged_txn_id']}, Cust={r['customer_id']}, Card={r['card_id']}, Amt=${r['TransactionAmt']}, Score={r['risk_score']}, Trigger={r['trigger_type']}, Chan={r['channel']}, Addr1={r['addr1']}, Dev={r['DeviceInfo']}, OS={r['id_30']}, Browser={r['id_31']}, Screen={r['id_33']}, id15={r['id_15']}")
