import pandas as pd
import json
import time

print("Building global device-to-customer graph index...")
t0 = time.time()

ident = pd.read_csv('data/identity.csv')
ident['device_profile'] = (
    ident['DeviceInfo'].fillna('') + ' | ' +
    ident['id_30'].fillna('') + ' | ' +
    ident['id_31'].fillna('') + ' | ' +
    ident['id_33'].fillna('')
).str.strip(' |')

online_txn_ids = set(ident['TransactionID'])
print(f"Total online transactions: {len(online_txn_ids)}")

txn_to_cust = {}
for chunk in pd.read_csv('data/transactions.csv', chunksize=100000, usecols=['TransactionID', 'customer_id', 'card1']):
    m = chunk[chunk['TransactionID'].isin(online_txn_ids)]
    for _, r in m.iterrows():
        txn_to_cust[r['TransactionID']] = (r['customer_id'], f"{r['customer_id']}-K1")

print(f"Mapped {len(txn_to_cust)} online transactions to customers in {time.time()-t0:.1f}s.")

# Aggregate by device profile
device_index = {}
for _, r in ident.iterrows():
    dev = r['device_profile']
    if not dev:
        continue
    tx_id = r['TransactionID']
    cust_info = txn_to_cust.get(tx_id)
    if dev not in device_index:
        device_index[dev] = {
            "txns": [],
            "customers": set(),
            "cards": set()
        }
    device_index[dev]["txns"].append(tx_id)
    if cust_info:
        device_index[dev]["customers"].add(cust_info[0])
        device_index[dev]["cards"].add(cust_info[1])

# Convert sets to sorted lists
out_index = {}
for dev, d in device_index.items():
    if len(d["cards"]) > 1 or len(d["txns"]) > 1:
        out_index[dev] = {
            "total_shared_txns": len(d["txns"]),
            "customers": sorted(list(d["customers"])),
            "cards": sorted(list(d["cards"])),
            "sample_txns": d["txns"][:10]
        }

with open('data/device_index.json', 'w') as f:
    json.dump(out_index, f)

print(f"Built device index with {len(out_index)} multi-transaction device profiles. Saved to data/device_index.json.")
