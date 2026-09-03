import requests
url = 'https://rojuifpeywxpflaimvks.supabase.co/rest/v1/cqc_leads?contact_email=eq.NaN'
headers = {
    'apikey': 'sb_publishable_YHkcdUt88BPCa2PqzfhUIQ_7VTuVl5w',
    'Authorization': 'Bearer sb_publishable_YHkcdUt88BPCa2PqzfhUIQ_7VTuVl5w'
}
response = requests.get(url, headers=headers)
print(f"Rows with string 'NaN' as email: {len(response.json())}")

url2 = 'https://rojuifpeywxpflaimvks.supabase.co/rest/v1/cqc_leads?contact_email=is.null'
response2 = requests.get(url2, headers=headers)
print(f"Rows with actual NULL email: {len(response2.json())}")
