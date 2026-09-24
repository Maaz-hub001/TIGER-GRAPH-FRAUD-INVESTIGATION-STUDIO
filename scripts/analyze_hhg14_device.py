import pandas as pd

ident = pd.read_csv('data/identity.csv')
txns = pd.read_csv('data/benchmark_customers_txns.csv')
cases = pd.read_csv('data/case_pack.csv')

ident['device_profile'] = ident['DeviceInfo'].fillna('') + ' | ' + ident['id_30'].fillna('') + ' | ' + ident['id_31'].fillna('') + ' | ' + ident['id_33'].fillna('')

# Find the device for HHG-014 (txn 3478561)
hhg14_dev = ident[ident['TransactionID'] == 3478561]['device_profile'].iloc[0]
print(f"HHG-014 Device Profile: '{hhg14_dev}'")

# Search all txns with this device profile in identity
matches = ident[ident['device_profile'] == hhg14_dev]
print(f"Total transactions with HHG-014 device profile in identity.csv: {len(matches)}")
print("Sample matching txns:", matches['TransactionID'].head(10).tolist())

# Now let's see which cards/customers these matching transactions belong to
# We can search transactions.csv for these TransactionIDs
matched_tx_ids = set(matches['TransactionID'])

print("\nSearching transactions.csv for connected cards...")
found_rows = []
for chunk in pd.read_csv('data/transactions.csv', chunksize=100000, usecols=['TransactionID', 'customer_id', 'card1', 'card2', 'card4', 'card6', 'TransactionAmt', 'ts', 'risk_score']):
    m = chunk[chunk['TransactionID'].isin(matched_tx_ids)]
    if len(m) > 0:
        found_rows.append(m)

df_dev_txns = pd.concat(found_rows, ignore_index=True)
print(f"Found {len(df_dev_txns)} transactions matching HHG-014 device!")
print(f"Distinct customers involved: {df_dev_txns['customer_id'].nunique()}")
print(df_dev_txns[['TransactionID', 'customer_id', 'ts', 'TransactionAmt', 'risk_score']].head(15))
