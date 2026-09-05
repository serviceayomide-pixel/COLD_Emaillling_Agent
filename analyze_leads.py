import pandas as pd
import glob

# Read main leads file
cqc = pd.read_csv('cqc_cleaned.csv')
print(f'Total CQC leads (excluding header): {len(cqc)}')

# Read all email files
email_files = glob.glob('lead missed from database/*.csv')
dfs = []
for f in email_files:
    try:
        df = pd.read_csv(f)
        dfs.append(df)
    except Exception as e:
        print(f"Error reading {f}: {e}")

if dfs:
    emails = pd.concat(dfs, ignore_index=True)
    print(f'Total email rows: {len(emails)}')
    print(f'Unique CQC IDs in emails: {emails["cqc_id"].nunique()}')
    if "enriched_email" in emails.columns:
        print(f'Valid emails found (not null): {emails["enriched_email"].notna().sum()}')
    elif "email" in emails.columns:
        print(f'Valid emails found (not null): {emails["email"].notna().sum()}')
    else:
        print(f'Columns in emails: {emails.columns}')
else:
    print("No email files found or read.")
