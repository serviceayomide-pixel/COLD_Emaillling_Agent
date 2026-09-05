import pandas as pd
import time

start = time.time()
print("Reading ODS file (this may take a few minutes for 23MB)...")

try:
    # Read the second sheet (usually index 1 is the main data after the Readme, but let's try reading the sheet named 'HSCA Active Locations' or similar)
    # We will let pandas load it.
    xls = pd.ExcelFile('01_June_2026_HSCA_Active_Locations.ods', engine='odf')
    
    # Find the right sheet
    sheet_to_load = xls.sheet_names[1] if len(xls.sheet_names) > 1 else xls.sheet_names[0]
    for s in xls.sheet_names:
        if 'Locations' in s or 'Data' in s or 'HSCA' in s:
            if 'README' not in s.upper():
                sheet_to_load = s
                break
                
    print(f"Loading data from sheet: {sheet_to_load}")
    df = pd.read_excel(xls, sheet_name=sheet_to_load)
    
    print(f"Successfully loaded {len(df)} rows. Columns found: {len(df.columns)}")
    
    # Find the exact names of the Location ID and Registered Manager columns
    loc_col = None
    mgr_col = None
    
    for col in df.columns:
        col_str = str(col).lower()
        if 'location id' in col_str and 'primary' not in col_str:
            loc_col = col
        if 'registered manager' in col_str or 'manager name' in col_str:
            mgr_col = col
            
    if loc_col and mgr_col:
        print(f"Found Location column: '{loc_col}'")
        print(f"Found Manager column: '{mgr_col}'")
        
        # Extract just these two columns
        extracted = df[[loc_col, mgr_col]].dropna(subset=[loc_col])
        
        # Clean the ID column just in case
        extracted[loc_col] = extracted[loc_col].astype(str).str.strip()
        
        # Rename for simplicity
        extracted = extracted.rename(columns={loc_col: 'cqc_location_id', mgr_col: 'registered_manager'})
        
        # Save to CSV
        extracted.to_csv('registered_managers.csv', index=False)
        print(f"Saved {len(extracted)} managers to 'registered_managers.csv'")
    else:
        print("Could not find the required columns!")
        print(f"Columns available: {list(df.columns)}")
        
except Exception as e:
    print(f"Error parsing ODS: {e}")

print(f"Finished in {time.time() - start:.2f} seconds")
