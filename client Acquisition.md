Here is the complete, compiled Developer PRD containing every architectural update, the step-by-step data flow, and your repository structure.

You can click the **"Copy code"** button in the top right corner of the block below and paste it directly into your `PRD.md` or `README.md` file.

```markdown
# DEVELOPER PRODUCT REQUIREMENT DOCUMENT (PRD)

**Project Title:** Autonomous Client Acquisition AI Engine (UK Healthcare Recruitment)  
**Architect:** Lead AI Automation Architect  
**Core Stack:** FastAPI (Python), React/Vue, Supabase (PostgreSQL), OpenAI API, Apollo.io API, Firecrawl, Serper.dev, Instantly API, MS Graph API  
**Target Version:** v1.4.0 (Code-First Architecture with Deep Context & Adaptive Routing)

---

## 1. System Architecture & Step-by-Step Flow

This system is an enterprise-grade, code-first outbound sales engine designed to operate autonomously without visual workflow builders. 

### The Step-by-Step Data Flow
1. **Ingestion:** You upload the pre-cleaned CSV $\rightarrow$ FastAPI chunks it and saves it to **Supabase** (`companies` table).
2. **Adaptive Enrichment Routing:** FastAPI's background worker pulls pending companies.
   * *Path A (Website exists):* Hits Apollo's People Search API directly to find the decision-maker.
   * *Path B (No website):* Hits Apollo's Match API to find the domain, then automatically re-routes to Path A.
3. **Verification:** The discovered email is immediately bounced against the **MillionVerifier API**. If safe, it saves to the `contacts` table.
4. **Deep Context Extraction:** FastAPI uses **Firecrawl** (if they have a website) or **Serper.dev** (if they don't) to scrape real-time business context (services, about us, local reputation).
5. **AI Generation:** FastAPI pulls the contact's name, the CSV data, and the scraped context, feeds it to **OpenAI**, and saves a 4-part JSON email sequence back to Supabase.
6. **Dispatch:** FastAPI pushes the lead and the custom copy to the **Instantly API**, which handles the actual sending through Gabriel's Microsoft 365 Outlook.
7. **Tracking & Intent:** Instantly fires webhooks back to FastAPI when a prospect opens or replies. If they reply, **OpenAI** reads the message to classify the intent (`INTERESTED`, `UNSUBSCRIBE`, etc.).
8. **Scheduling:** If `INTERESTED`, FastAPI uses the **Microsoft Graph API** to check available slots and automatically replies with booking times.

---

## 2. Local Repository Structure

A standard monorepo structure separating the FastAPI backend and the React/Vue frontend.

```text
healthcare-ai-acquisition/
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── api/              # REST Endpoints & Webhooks
│   │   │   ├── routes_dashboard.py
│   │   │   ├── routes_ingestion.py
│   │   │   └── webhooks_instantly.py
│   │   ├── core/             # Config, DB Setup, Security
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   ├── models/           # SQLAlchemy DB Schemas
│   │   ├── services/         # Core Logic & 3rd Party APIs
│   │   │   ├── apollo_engine.py
│   │   │   ├── context_scraper.py   # Firecrawl & Serper logic
│   │   │   ├── openai_engine.py
│   │   │   ├── instantly_engine.py
│   │   │   └── outlook_graph.py
│   │   └── worker.py         # Async Background Tasks
│   ├── .env                  # Backend Secrets
│   ├── requirements.txt
│   └── main.py               # FastAPI Entry Point
│
├── frontend/                 # React or Vue Application
│   ├── src/
│   │   ├── components/       # Metric Cards, Data Tables
│   │   ├── pages/            # Dashboard Views
│   │   ├── services/         # Axios API Client
│   │   └── App.js/vue
│   ├── package.json
│   └── .env                  # Frontend Config (FastAPI URL)
│
├── .gitignore
└── README.md

```

---

## 3. Global Database Schema (Supabase / PostgreSQL)

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TYPE enrichment_status_type AS ENUM ('pending', 'enriched', 'failed');
CREATE TYPE enrichment_method_type AS ENUM ('website_route', 'location_fallback_route', 'none');
CREATE TYPE verification_status_type AS ENUM ('unverified', 'safe', 'catch_all', 'invalid');
CREATE TYPE campaign_status_type AS ENUM ('ready', 'active', 'paused', 'replied', 'unsubscribed', 'completed');

CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    cqc_location_id VARCHAR(50) UNIQUE,
    company_name VARCHAR(255) NOT NULL,
    website_url VARCHAR(255) NULL, 
    phone_number VARCHAR(50),
    location_address TEXT,
    city VARCHAR(100),
    region VARCHAR(100),
    service_types TEXT,
    scraped_context TEXT NULL, -- Stores Firecrawl/Serper Markdown
    enrichment_status enrichment_status_type DEFAULT 'pending',
    enrichment_method enrichment_method_type DEFAULT 'none', 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE contacts (
    id SERIAL PRIMARY KEY,
    company_id INT REFERENCES companies(id) ON DELETE CASCADE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    job_title VARCHAR(150),
    email_address VARCHAR(255) UNIQUE,
    verification_status verification_status_type DEFAULT 'unverified',
    campaign_status campaign_status_type DEFAULT 'ready',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE email_campaigns (
    id SERIAL PRIMARY KEY,
    contact_id INT REFERENCES contacts(id) ON DELETE CASCADE,
    email_sequence_json JSONB, 
    current_step INT DEFAULT 1,
    last_sent_at TIMESTAMP WITH TIME ZONE NULL,
    next_send_at TIMESTAMP WITH TIME ZONE NULL
);

CREATE TABLE system_metrics (
    id SERIAL PRIMARY KEY,
    metric_date DATE UNIQUE DEFAULT CURRENT_DATE,
    total_csv_ingested INT DEFAULT 0,
    total_enriched_via_website INT DEFAULT 0,
    total_enriched_via_location INT DEFAULT 0,
    total_sent INT DEFAULT 0,
    total_opened INT DEFAULT 0,
    total_replied INT DEFAULT 0,
    meetings_booked INT DEFAULT 0
);

```

---

## 4. Phase-by-Phase Technical Specifications

### PHASE 1: System Infrastructure

* **Components:** FastAPI Engine, Supabase Cloud Cluster, PgBouncer Connection Pooler.
* **Environment Variables:** `DATABASE_URL`, `OPENAI_API_KEY`, `APOLLO_API_KEY`, `MILLIONVERIFIER_API_KEY`, `FIRECRAWL_API_KEY`, `SERPER_API_KEY`, `INSTANTLY_API_KEY`, `MICROSOFT_CLIENT_ID`.

### PHASE 2: CSV Data Ingestion Engine

* **Technical Logic:** Parse files via chunks (`chunksize=1000`). Clean URLs to a root domain. If blank, insert as `NULL`. Execute bulk inserts via `ON CONFLICT DO NOTHING`.

### PHASE 3: Adaptive Enrichment Routing Engine (Core Logic)

* **[Condition A]: `website_url` is NOT NULL (Website Route)**
1. Call Apollo People Search API (`POST /v1/mixed_people/api_search`) using the domain and target titles (Director, CEO, etc.).
2. If found, update `enrichment_method` to `'website_route'` and save email.


* **[Condition B]: `website_url` IS NULL (Location Fallback Route)**
1. Call Apollo Organization Match API (`POST /v1/organizations/match`) using company name and city.
2. Extract the returned domain, update `companies.website_url`, and immediately re-route the domain into Condition A.
3. If found, update `enrichment_method` to `'location_fallback_route'`.


* **Verification:** Bounce all found emails against MillionVerifier. Only save contacts with code `1` (Safe to send).

### PHASE 4: Deep Context Extraction (Pre-AI Research)

* **Objective:** Gather deep business context to feed the AI generator. This step *only* runs for companies with a verified contact.
* **[Route A]: Has Website $\rightarrow$ Firecrawl:**
* Send the domain to Firecrawl API (`/scrape`). Limit scope to the homepage and `/about` pages. Save returned markdown to `companies.scraped_context`.


* **[Route B]: No Website $\rightarrow$ Serper.dev Fallback:**
* Send `"{Company Name} {City} UK care agency services"` to Serper API. Concatenate the top 3 snippet descriptions. Save to `companies.scraped_context`.



### PHASE 5: AI Personalization Engine

* **Technical Logic:** Merge CSV attributes (`company_name`, `region`), Apollo attributes (`first_name`), and the newly acquired `scraped_context` into an OpenAI system prompt. Command OpenAI to reference the scraped context in the opening line to prove deep research. Use Structured JSON Outputs (`openai.beta.chat.completions.parse`) to generate a 4-part email sequence (`mail_1_body` through `mail_4_body`).

### PHASE 6: Campaign Dispatch

* **Technical Logic:** Invoke Instantly API (`POST /v1/campaigns/add-leads`) passing the personalized JSON content blocks to queue sending via Microsoft Outlook. Ensure daily pacing (30-50 per inbox).

### PHASE 7: Tracking & Intent Classification

* **Technical Logic:** Expose `POST /api/webhooks/instantly`. On `lead_replied` webhook, pass the reply text to OpenAI for intent classification (`INTERESTED`, `UNSUBSCRIBE`, `NEUTRAL`) and update the database state.

### PHASE 8: Calendar Automation

* **Technical Logic:** If intent is `INTERESTED`, query Microsoft Graph API (`GET /me/calendar/calendarView`) for availability and auto-reply with 2-3 specific booking slots.

---

## 5. REST API Interface Specs

* `GET /api/dashboard/stats`: Returns JSON aggregate metrics (sent volume, meetings booked, enrichment sources).
* `GET /api/leads?page=1&limit=50`: Returns paginated contact statuses for the frontend data grid.
* `POST /api/upload-csv`: Handles multipart form data for CQC CSV ingestion.
* `PATCH /api/leads/{id}`: Manual override for pausing/resuming campaigns.

---

## 6. Frontend Dashboard Integration Layer

* **Framework:** React (Tremor UI / Shadcn) OR Vue (PrimeVue).
* **Metric Cards:** Display data widgets showcasing Sourced Leads, Enriched via Website, Enriched via Location Fallback, Sent Volume, and Booked Meetings.
* **Data Log Table:** Interactive grid tracking lead profiles with built-in button controls enabling manual pause/resume overrides.

```

```