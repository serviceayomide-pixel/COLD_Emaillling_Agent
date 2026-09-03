Sprint 1: The Credit Burner (Days 1 - 2)
Goal: Ingest the CSV, exhaust the Apollo credits, and verify the emails.

Spin up the Database: Create your Supabase project, grab the PostgreSQL connection string, and run your SQL table creations.

Build the Ingestion Script: Write the FastAPI endpoint to upload and chunk the 50,000-row CQC CSV into Supabase.

Write the Core Worker: Build the background task that pulls domains from Supabase, hits the Apollo APIs (using the Website path first, then Location fallback), and immediately routes the found emails through MillionVerifier.

Let it Rip: Do not build anything else. Hit "start" on this worker script and let it run continuously for 24-48 hours until it burns through all 30,000 Apollo credits. You will wake up to a database packed with thousands of verified, safe-to-send decision-maker emails.

Sprint 2: The AI Factory (Day 3)
Goal: Generate the email copy for all verified leads.

Add the Scraper: Write the async Python functions for Firecrawl (for domains) and Serper.dev (for the fallbacks) to pull the company context.

Hook up OpenAI: Connect the OpenAI API to your FastAPI app. Feed it the scraped context, the contact name, and the company details.

Batch Generation: Write a loop that pulls batches of 50 verified contacts from Supabase at a time, runs them through OpenAI, and saves the 4-part JSON email sequence right back into the database. Let this script run until every verified lead has a drafted email sequence waiting.

Sprint 3: The Delivery & Dashboard (Days 4 - 5)
Goal: Connect to Gabriel's Outlook and build the visual UI.

The Instantly Bridge: Write the final FastAPI script that takes the fully prepped leads (email + OpenAI drafts) and pushes them via API into Instantly. Set the daily pacing rules so it starts dripping out emails safely.

The Webhooks: Expose your FastAPI webhook route so Instantly can start pinging you when people open or reply. Add the quick OpenAI intent classifier to pause campaigns if a reply comes in.

The Quick UI: Spin up your React or Vue project using Tremor or PrimeVue. Build three simple API calls to your backend to pull the stats (GET /api/dashboard/stats) and display them on a clean, dark-mode dashboard. Deploy it to Vercel.

Why this works: By the time you start coding the React/Vue frontend on Day 4, Gabriel's database is already fully enriched, the AI drafts are finished, and the emails are literally sending in the background. You get to hand over a massive, fully populated system that is already generating value, completing the gig with maximum efficiency.