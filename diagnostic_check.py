import pandas as pd
import time
import os

print("Waiting for registered_managers.csv to be generated...")
while not os.path.exists('registered_managers.csv'):
    time.sleep(2)

print("\n--- RUNNING DIAGNOSTIC CHECK ---")
# 1. Load the files
cqc = pd.read_csv('cqc_merged_with_emails_final.csv')
mgr = pd.read_csv('registered_managers.csv')

print(f"Master List Rows: {len(cqc)}")
print(f"Managers Extracted Rows: {len(mgr)}")

# 2. Raw Comparison (No normalization)
cqc_raw_ids = set(cqc['cqc_location_id'].astype(str))
mgr_raw_ids = set(mgr['cqc_location_id'].astype(str))
raw_overlap = cqc_raw_ids.intersection(mgr_raw_ids)
print(f"\nRAW MATCH RATE: {len(raw_overlap)} out of {len(cqc)} master leads matched perfectly before cleaning.")

# Print format examples
print(f"Example Master ID:  '{list(cqc_raw_ids)[0]}'")
print(f"Example Manager ID: '{list(mgr_raw_ids)[0]}'")

# 3. Normalized Comparison (The Bulletproof Method)
cqc['cqc_location_id_clean'] = cqc['cqc_location_id'].astype(str).str.strip().str.lower()
mgr['cqc_location_id_clean'] = mgr['cqc_location_id'].astype(str).str.strip().str.lower()

cqc_clean_ids = set(cqc['cqc_location_id_clean'])
mgr_clean_ids = set(mgr['cqc_location_id_clean'])
clean_overlap = cqc_clean_ids.intersection(mgr_clean_ids)
print(f"\nNORMALIZED MATCH RATE: {len(clean_overlap)} out of {len(cqc)} master leads matched after stripping spaces and standardizing format.")

missing = cqc_clean_ids - mgr_clean_ids
if missing:
    print(f"\nWARNING: {len(missing)} master leads could NOT find a match in the manager file.")
    print(f"Sample of missing IDs: {list(missing)[:5]}")
else:
    print("\nSUCCESS: 100% of your master leads found a match in the manager file!")
    
# Let's also check how many of the matched ones actually have a non-null manager name
matched_mgrs = mgr[mgr['cqc_location_id_clean'].isin(cqc_clean_ids)]
non_null_mgrs = matched_mgrs['registered_manager'].notna().sum()
print(f"Out of the matched locations, {non_null_mgrs} actually have a Registered Manager name filled in.")
