import pandas as pd

print("Loading Master Database...")
cqc = pd.read_csv('cqc_merged_with_emails_final.csv')

print("Loading Manager Data...")
mgr = pd.read_csv('registered_managers.csv')

# Clean IDs to ensure perfect match
cqc['cqc_location_id_clean'] = cqc['cqc_location_id'].astype(str).str.strip().str.lower()
mgr['cqc_location_id_clean'] = mgr['cqc_location_id'].astype(str).str.strip().str.lower()

# Drop duplicate manager rows if any exist in the raw data to prevent row explosion
mgr = mgr.drop_duplicates(subset=['cqc_location_id_clean'])

print("Merging Manager Names...")
# Left join managers into cqc
cqc_merged = pd.merge(cqc, mgr[['cqc_location_id_clean', 'registered_manager']], on='cqc_location_id_clean', how='left')

# Drop the temporary clean ID column
cqc_merged.drop(columns=['cqc_location_id_clean'], inplace=True)

# Now, we should check if contact_first_name is empty. 
# If it is, and we have a registered_manager name, we can fill it in!
# Let's split registered_manager into first and last name for the database!

def split_name(full_name):
    if pd.isna(full_name) or not isinstance(full_name, str):
        return pd.Series([None, None])
    parts = str(full_name).strip().split()
    if len(parts) == 0:
        return pd.Series([None, None])
    if len(parts) == 1:
        return pd.Series([parts[0], None])
    return pd.Series([parts[0], " ".join(parts[1:])])

print("Formatting Manager Names into First & Last Name...")
cqc_merged[['mgr_first', 'mgr_last']] = cqc_merged['registered_manager'].apply(split_name)

# If contact_first_name is missing, use mgr_first
cqc_merged['contact_first_name'] = cqc_merged['contact_first_name'].fillna(cqc_merged['mgr_first'])
# If contact_last_name is missing, use mgr_last
cqc_merged['contact_last_name'] = cqc_merged['contact_last_name'].fillna(cqc_merged['mgr_last'])

# Drop temporary columns
cqc_merged.drop(columns=['mgr_first', 'mgr_last', 'registered_manager'], inplace=True)

print("Saving final master database...")
cqc_merged.to_csv('cqc_merged_with_emails_final.csv', index=False)
print(f"Total rows: {len(cqc_merged)}")
print(f"Total leads with a First Name: {cqc_merged['contact_first_name'].notna().sum()}")
print(f"Total leads with an Email: {cqc_merged['contact_email'].notna().sum()}")
