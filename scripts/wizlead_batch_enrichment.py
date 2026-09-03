"""
Wizlead Batch Enrichment Pipeline
===================================
Pulls pending leads from Supabase → uploads to Wizlead Find Email Batch
→ waits for results → verifies found emails → saves verified emails back to Supabase.

Run this once per month to enrich your next batch of leads.

Usage:
    python wizlead_batch_enrichment.py

Credit cost estimate per run:
    5,000 leads uploaded
    ~2,000-2,500 emails found × 3 credits  = ~7,500 credits
    ~2,000-2,500 emails verified × 0.5 credits = ~1,250 credits
    TOTAL: ~8,750 credits (safely within 10,000)
"""

import os
import csv
import io
import json
import time
import requests
from supabase import create_client, Client
from datetime import datetime

# ── Configuration ─────────────────────────────────────────────────────────────
# Secrets are read from environment variables — never hardcode them in source code.
# Set these in your .env file or Railway environment before running this script.
SUPABASE_URL      = os.environ["SUPABASE_URL"]
SUPABASE_KEY      = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
WIZLEAD_API_KEY   = os.environ["WIZLEAD_API_KEY"]
WIZLEAD_BASE_URL  = "https://api.wizleads.io"
TABLE_NAME        = "cqc_leads"

BATCH_SIZE        = 500   # Leads to pull per run
POLL_INTERVAL_SEC = 30     # How often to check task status
MAX_POLL_MINUTES  = 120    # Bail out if task takes longer than this
SUPABASE_PAGE_SIZE = 1000  # Supabase max rows per request

HEADERS = {"x-api-key": WIZLEAD_API_KEY}


# ── Helpers ───────────────────────────────────────────────────────────────────

def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def poll_task(task_id: str, label: str) -> dict:
    """
    Poll a Wizlead task until it reaches a terminal state.
    Returns the final task dict.
    """
    log(f"Polling {label} task {task_id}...")
    max_polls = (MAX_POLL_MINUTES * 60) // POLL_INTERVAL_SEC

    for attempt in range(1, max_polls + 1):
        resp = requests.get(
            f"{WIZLEAD_BASE_URL}/tasks/{task_id}",
            headers=HEADERS,
            timeout=15
        )
        resp.raise_for_status()
        task = resp.json()
        status = task.get("status", "Unknown")

        done_count  = sum(task.get("dones", {}).values())
        total_count = sum(task.get("totals", {}).values())
        progress    = f"{done_count}/{total_count}" if total_count else "..."

        log(f"  [{label}] Status: {status} | Progress: {progress} | Poll #{attempt}")

        if status in ("Done", "Aborted", "Failed"):
            if status != "Done":
                raise RuntimeError(f"{label} task ended with status: {status} | Error: {task.get('errmsg')}")
            return task

        time.sleep(POLL_INTERVAL_SEC)

    raise TimeoutError(f"{label} task did not complete within {MAX_POLL_MINUTES} minutes.")


def download_csv_from_task(task: dict) -> list[dict]:
    """Download result CSV from Wizlead S3 link and return as list of dicts."""
    download_url = task.get("link")
    if not download_url:
        raise ValueError("No download link in completed task.")

    log(f"  Downloading results from S3...")
    resp = requests.get(download_url, timeout=60)
    resp.raise_for_status()

    content = resp.content.decode("utf-8-sig")  # Handle BOM if present
    reader  = csv.DictReader(io.StringIO(content))
    rows    = list(reader)
    log(f"  Downloaded {len(rows)} rows from CSV.")
    return rows


def build_csv_bytes(rows: list[dict], fieldnames: list[str]) -> bytes:
    """Build a CSV file in memory from a list of dicts."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


# ── Step 1: Pull pending leads from Supabase ─────────────────────────────────

def pull_pending_leads(supabase: Client) -> list[dict]:
    log(f"Pulling up to {BATCH_SIZE} pending leads from Supabase...")

    all_leads = []
    page = 0

    while len(all_leads) < BATCH_SIZE:
        start = page * SUPABASE_PAGE_SIZE
        end   = start + SUPABASE_PAGE_SIZE - 1

        result = (
            supabase.table(TABLE_NAME)
            .select("id, cqc_location_id, company_name, contact_first_name, contact_last_name, website_url")
            .eq("enrichment_status", "pending")
            .not_.is_("contact_first_name", "null")
            .not_.is_("contact_last_name", "null")
            .not_.is_("website_url", "null")
            # Exclude bad website values
            .neq("website_url", "dual registration")
            .neq("website_url", "-")
            .range(start, end)
            .execute()
        )

        batch = result.data
        if not batch:
            break

        all_leads.extend(batch)
        page += 1

        if len(batch) < SUPABASE_PAGE_SIZE:
            break  # Last page

    leads = all_leads[:BATCH_SIZE]
    log(f"Pulled {len(leads)} leads.")
    return leads


# ── Step 2: Upload to Wizlead Find Email Batch ────────────────────────────────

def submit_find_email_batch(leads: list[dict]) -> str:
    """
    Upload leads CSV to Wizlead Find Email Batch.
    Returns the task_id.
    """
    log(f"Building CSV for {len(leads)} leads...")

    # Build rows for CSV - column names must match column_mapping below
    csv_rows = [
        {
            "cqc_id":    lead["cqc_location_id"],
            "firstName": lead["contact_first_name"],
            "lastName":  lead["contact_last_name"],
            "website":   lead["website_url"],
        }
        for lead in leads
    ]

    csv_bytes = build_csv_bytes(csv_rows, ["cqc_id", "firstName", "lastName", "website"])

    column_mapping = json.dumps({
        "firstName":        "firstName",
        "lastName":         "lastName",
        "company_website":  "website"
    })

    log("Submitting Find Email Batch task to Wizlead...")
    resp = requests.post(
        f"{WIZLEAD_BASE_URL}/email/find-email-batch",
        headers=HEADERS,
        data={
            "task_name":       f"CQC_Find_Email_{datetime.now().strftime('%Y%m%d_%H%M')}",
            "column_mapping":  column_mapping,
        },
        files={
            "file": ("leads.csv", csv_bytes, "text/csv")
        },
        timeout=60
    )

    if resp.status_code == 402:
        raise RuntimeError("Wizlead: Insufficient credits! Top up and retry.")
    if resp.status_code != 200:
        raise RuntimeError(f"Wizlead Error {resp.status_code}: {resp.text}")

    resp.raise_for_status()
    data = resp.json()
    task_id       = data["task_id"]
    rows          = data["rows"]
    credits_blocked = data["credits_blocked"]

    log(f"Find Email task submitted! task_id={task_id} | rows={rows} | credits_blocked={credits_blocked}")
    return task_id


# ── Step 3: Parse Find Email results ─────────────────────────────────────────

def parse_find_results(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Split results into:
    - found: rows where Wizlead returned an email
    - not_found: rows where no email was found
    """
    found     = []
    not_found = []

    for row in rows:
        # Wizlead returns 'enriched_email' column in the result CSV
        email = (row.get("enriched_email") or "").strip()
        if email and "@" in email:
            # Normalise: copy to 'email' key for downstream use
            row["email"] = email
            found.append(row)
        else:
            not_found.append(row)

    log(f"  Emails found: {len(found)} | Not found: {len(not_found)}")
    return found, not_found


# ── Step 4: Upload found emails to Verify Email Batch ────────────────────────

def submit_verify_email_batch(found_rows: list[dict]) -> str:
    """
    Upload found emails to Wizlead Verify Email Batch.
    Returns the task_id.
    """
    if not found_rows:
        log("No emails to verify.")
        return None

    log(f"Building verify CSV for {len(found_rows)} emails...")

    csv_rows = [{"cqc_id": r.get("cqc_id", ""), "email": r.get("email", "")} for r in found_rows]
    csv_bytes = build_csv_bytes(csv_rows, ["cqc_id", "email"])

    column_mapping = json.dumps({"email": "email"})

    log("Submitting Verify Email Batch task to Wizlead...")
    resp = requests.post(
        f"{WIZLEAD_BASE_URL}/email/verify-email-batch",
        headers=HEADERS,
        data={
            "task_name":      f"CQC_Verify_Email_{datetime.now().strftime('%Y%m%d_%H%M')}",
            "column_mapping": column_mapping,
        },
        files={
            "file": ("emails.csv", csv_bytes, "text/csv")
        },
        timeout=60
    )

    if resp.status_code == 402:
        raise RuntimeError("Wizlead: Insufficient credits for verification!")

    resp.raise_for_status()
    data    = resp.json()
    task_id = data["task_id"]
    log(f"Verify task submitted! task_id={task_id} | rows={data['rows']} | credits_blocked={data['credits_blocked']}")
    return task_id


# ── Step 5: Save results back to Supabase ────────────────────────────────────

def save_results_to_supabase(supabase: Client, verify_rows: list[dict], not_found_rows: list[dict], all_leads: list[dict]):
    """
    Update cqc_leads in Supabase:
    - valid email found   → contact_email, enrichment_status = 'enriched'
    - invalid/catchall    → enrichment_status = 'invalid_email'
    - not found           → enrichment_status = 'no_email'
    """

    # Build lookup: cqc_id → lead row
    id_map = {lead["cqc_location_id"]: lead for lead in all_leads}

    valid_updates   = []
    invalid_updates = []

    for row in verify_rows:
        cqc_id = (row.get("cqc_id") or "").strip()
        email  = (row.get("email") or "").strip()
        status = (row.get("verify_status") or "").strip().lower()  # correct column name

        if status == "valid" and email:
            valid_updates.append({
                "cqc_location_id":  cqc_id,
                "contact_email":    email,
                "enrichment_status": "enriched",
                "enriched_at":      datetime.utcnow().isoformat(),
            })
        else:
            invalid_updates.append({
                "cqc_location_id":  cqc_id,
                "enrichment_status": "invalid_email",
            })

    # Not found rows - explicitly delete them
    not_found_ids = [
        (row.get("cqc_id") or "").strip()
        for row in not_found_rows
        if (row.get("cqc_id") or "").strip()
    ]

    log(f"Saving to Supabase: {len(valid_updates)} enriched | {len(invalid_updates)} invalid | {len(not_found_ids)} to delete")

    def batch_upsert(rows, label, chunk=200):
        for i in range(0, len(rows), chunk):
            supabase.table(TABLE_NAME).upsert(
                rows[i:i+chunk], on_conflict="cqc_location_id"
            ).execute()
        log(f"  Saved {len(rows)} {label} rows.")

    def batch_delete(ids, label, chunk=200):
        for i in range(0, len(ids), chunk):
            chunk_ids = ids[i:i+chunk]
            supabase.table(TABLE_NAME).delete().in_("cqc_location_id", chunk_ids).execute()
        log(f"  Deleted {len(ids)} {label} rows.")

    if valid_updates:
        batch_upsert(valid_updates, "enriched")
    if invalid_updates:
        batch_upsert(invalid_updates, "invalid")
    if not_found_ids:
        batch_delete(not_found_ids, "not_found")


# ── Main Pipeline ─────────────────────────────────────────────────────────────

def main():
    print()
    print("=" * 60)
    print("  WIZLEAD BATCH EMAIL ENRICHMENT PIPELINE")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    log("Connected to Supabase.")

    # ── STEP 1: Pull leads ─────────────────────────────────────────────
    leads = pull_pending_leads(supabase)
    if not leads:
        log("No pending leads found. All done or need to check enrichment_status.")
        return

    # ── STEP 2: Submit Find Email batch ───────────────────────────────
    find_task_id = submit_find_email_batch(leads)

    # ── STEP 3: Wait for Find Email to complete ───────────────────────
    find_task = poll_task(find_task_id, "FindEmail")
    log(f"Find Email complete. Total emails found: {find_task.get('enrich_final', '?')}")

    # ── STEP 4: Download Find Email results ───────────────────────────
    find_rows = download_csv_from_task(find_task)
    found_rows, not_found_rows = parse_find_results(find_rows)

    if not found_rows:
        log("No emails found in this batch. Updating Supabase with no_email status.")
        save_results_to_supabase(supabase, [], not_found_rows, leads)
        return

    # ── STEP 5: Submit Verify Email batch ─────────────────────────────
    verify_task_id = submit_verify_email_batch(found_rows)

    # ── STEP 6: Wait for Verify Email to complete ─────────────────────
    verify_task = poll_task(verify_task_id, "VerifyEmail")
    log("Verify Email complete.")

    # ── STEP 7: Download Verify results ───────────────────────────────
    verify_rows = download_csv_from_task(verify_task)

    # ── STEP 8: Save everything to Supabase ───────────────────────────
    save_results_to_supabase(supabase, verify_rows, not_found_rows, leads)

    # ── Final Summary ──────────────────────────────────────────────────
    total_verified = sum(1 for r in verify_rows if (r.get("verify_status") or "").lower() == "valid")
    print()
    print("=" * 60)
    print("  ENRICHMENT COMPLETE")
    print(f"  Leads processed:      {len(leads):,}")
    print(f"  Emails found:         {len(found_rows):,}")
    print(f"  Emails verified:      {total_verified:,}")
    print(f"  No email found:       {len(not_found_rows):,}")
    print(f"  Ready to email:       {total_verified:,}")
    print(f"  Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
