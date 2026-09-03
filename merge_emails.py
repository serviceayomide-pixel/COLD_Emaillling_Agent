import pandas as pd
import glob

print("Loading CQC leads...")
cqc = pd.read_csv('cqc_cleaned.csv')
cqc['cqc_location_id_clean'] = cqc['cqc_location_id'].astype(str).str.strip()

print("Extracting emails and names from 'find' files...")
find_dfs = [pd.read_csv(f) for f in glob.glob('lead missed from database/find-email*.csv')]
find_emails = pd.concat(find_dfs, ignore_index=True)
valid_finds = find_emails.dropna(subset=['enriched_email'])[['cqc_id', 'enriched_email', 'firstName', 'lastName']].rename(
    columns={
        'enriched_email': 'contact_email', 
        'firstName': 'contact_first_name', 
        'lastName': 'contact_last_name'
    }
)
valid_finds['cqc_id_clean'] = valid_finds['cqc_id'].astype(str).str.strip()
valid_finds.drop_duplicates(subset=['cqc_id_clean'], inplace=True)

print("Extracting emails from 'verify' files...")
verify_dfs = [pd.read_csv(f) for f in glob.glob('lead missed from database/verify-email*.csv')]
verify_emails = pd.concat(verify_dfs, ignore_index=True)
valid_verifys = verify_emails[verify_emails['verify_status'] == 'valid'][['cqc_id', 'email']].rename(
    columns={'email': 'contact_email'}
)
valid_verifys['cqc_id_clean'] = valid_verifys['cqc_id'].astype(str).str.strip()
valid_verifys.drop_duplicates(subset=['cqc_id_clean'], inplace=True)

print("Combining and prioritizing verified emails...")
# We want to pull the first & last name from the 'find' files and attach them to the 'verify' files
valid_verifys = valid_verifys.merge(valid_finds[['cqc_id_clean', 'contact_first_name', 'contact_last_name']], on='cqc_id_clean', how='left')

# Combine them all and drop duplicates based on the CQC ID, keeping the verified version if available
all_valid_emails = pd.concat([valid_verifys, valid_finds], ignore_index=True).drop_duplicates(subset=['cqc_id_clean'])

print("Merging into main CQC leads...")
# Left join onto the main database
cqc_merged = pd.merge(
    cqc, 
    all_valid_emails[['cqc_id_clean', 'contact_email', 'contact_first_name', 'contact_last_name']], 
    how='left', 
    left_on='cqc_location_id_clean', 
    right_on='cqc_id_clean'
)

# Clean up temporary columns
cqc_merged.drop(columns=['cqc_location_id_clean', 'cqc_id_clean'], inplace=True, errors='ignore')

print("Saving the merged database...")
output_file = 'cqc_merged_with_emails_final.csv'
cqc_merged.to_csv(output_file, index=False)
print(f"Saved merged database to {output_file}.")
print(f"Total rows in new file: {len(cqc_merged)}")
print(f"Rows with contact_email: {cqc_merged['contact_email'].notna().sum()}")
print(f"Rows with contact_first_name: {cqc_merged['contact_first_name'].notna().sum()}")
