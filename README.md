# Agent<sup>2</sup>

[![Built at GenAI Genesis 2026](https://img.shields.io/badge/GenAI_Genesis-2026-blue)](#)

**Your real estate agent <ins>agent</ins>.** Text a number, take a short call, and get matched home listings sent to your phone. No apps, no accounts, no browsing.

---

## What is this?

Agent<sup>2</sup> is an end-to-end AI-powered home buying assistant. A user texts our number, receives a call from an AI voice agent, describes what kind of home they want in plain conversation, and gets real listings texted back. Behind the scenes, the system:

1. **Listens** to the conversation via a Telnyx/PersonaPlex voice pipeline
2. **Extracts** structured search criteria (location, budget, bedrooms, features, etc.) from the transcript using an LLM
3. **Scrapes** Zillow for matching listings, scores them against the criteria, and ranks by fit
4. **Contacts agents** on the caller's behalf by automating the "Contact Agent" form on Zillow with Playwright

The whole flow — from a spoken sentence like *"I'm looking for a two-bedroom house in Toronto, pet-friendly, near schools"* to a filled-out contact form on a real listing — is automated.

---

## How it works

```
User texts Agent2 number
        |
        v
  AI calls user back (Telnyx + PersonaPlex voice agent)
        |
        v
  Conversation transcript
        |
        v
  LLM extracts search criteria (location, price, beds, features...)
        |
        v
  Zillow scraper finds listings via ScraperAPI
        |
        v
  Listings scored & ranked against criteria
        |
        v
  Top listings sent to user via SMS
        |
        v
  Contact agent form filled on user's behalf (Playwright)
```

---

## Setup

### Prerequisites

- Python 3.10+
- A [ScraperAPI](https://www.scraperapi.com/) key (for Zillow scraping)
- A Telnyx or Twilio account (for SMS/voice)
- An OpenAI-compatible LLM endpoint (for criteria extraction)

### Install

```bash
git clone https://github.com/your-org/genaigenesis2026.git
cd genaigenesis2026

pip install -r requirements.txt
playwright install chromium
```

For the voice agent (in a separate environment if needed):

```bash
cd personaplex
pip install -r requirements.txt
```

### Environment variables

Copy `.env.example` to `.env` and fill in:

```
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...

OPENAI_API_KEY=...
GPT_OSS_BASE_URL=https://your-llm-endpoint/v1
GPT_OSS_MODEL=openai/gpt-oss-120b

SCRAPER_API_KEY=...
```

For the voice agent, also copy `personaplex/.env.example` to `personaplex/.env`.

### Run the web server

```bash
uvicorn app.main:app --reload
```

The landing page is served at `http://localhost:8000`. The SMS webhook is at `/sms`.

---

## Quick demo (end-to-end)

Run the full pipeline from a sample transcript to contact agent form fill:

```bash
python run_e2e.py
```

This will:
1. Read `trans.txt` (sample call transcript)
2. Call the LLM to extract search criteria
3. Scrape Zillow for matching listings
4. Open a browser and fill the "Contact Agent" form on the top listing

---

## Run individual pieces

### Extract search criteria from a transcript

```python
from app.agents.build_search_criteria import extract_search_criteria

transcript = open("trans.txt").read()
criteria = extract_search_criteria(transcript)
# Returns: { location, intent, price, bedrooms, bathrooms, property_type, features, ... }
```

### Scrape Zillow listings

```python
from data.zillow.scraper import search

results = search(criteria)
# results["matches"]  — listings that fit all criteria
# results["nearest"]  — close alternatives with violations noted
# results["message"]  — human-readable summary
```

### Contact an agent on a listing

```python
from app.contact import Lead, run_contact_flow

result = run_contact_flow(
    "https://www.zillow.com/homedetails/52-Birchmount-Rd-Toronto-ON-M1N-3J6/461061694_zpid/",
    Lead(),  # uses default name, email, phone
    mode="preview",  # fill form but don't submit
    headless=False,   # visible browser for demo
)
```

### Run tests

```bash
python -m pytest tests/test_search_criteria.py -v -s   # transcript -> criteria
python -m pytest tests/test_contact_agent.py -v -s      # contact agent form fill
python -m pytest tests/test_scrape_and_validate.py -v -s # full scrape + rank pipeline
```

---

## Project structure

```
genaigenesis2026/
|
|-- app/                          # Main application
|   |-- main.py                   # FastAPI app, serves landing page + SMS webhook
|   |-- config.py                 # Loads .env (Twilio, LLM endpoints)
|   |-- routers/
|   |   +-- sms.py                # SMS webhook: text -> confirmation -> outbound call
|   |-- agents/
|   |   +-- build_search_criteria.py  # LLM: transcript -> structured search criteria
|   +-- contact/
|       |-- contact_agent.py      # Playwright: open listing, click CTA, fill form
|       |-- fill_form.py          # Character-by-character typing into form fields
|       |-- locators.py           # Finds "Contact Agent" button, form, submit
|       +-- debug.py              # Saves screenshots/HTML on failure
|
|-- personaplex/                  # Voice agent (separate sub-app)
|   |-- app/
|   |   |-- config.py             # Telnyx + PersonaPlex config
|   |   |-- audio_utils.py        # Audio format conversion (L16 <-> Opus)
|   |   |-- routers/
|   |   |   |-- voice.py          # Telnyx <-> PersonaPlex WebSocket bridge
|   |   |   +-- sms.py            # SMS webhook, outbound call trigger
|   |   +-- services/
|   |       |-- telnyx_voice.py   # Telnyx Call Control
|   |       |-- personaplex_client.py  # PersonaPlex WebSocket client
|   |       +-- recorder.py       # Call recording to WAV
|   +-- requirements.txt
|
|-- data/
|   +-- zillow/
|       |-- scraper.py            # URL builder, search, score & rank listings
|       |-- parse.py              # Parse Zillow HTML (JSON + HTML fallback)
|       |-- detail.py             # Fetch listing detail page for features
|       |-- playwright_fetch.py   # HTTP fetch via ScraperAPI
|       +-- run.py                # CLI entry point for standalone scraping
|
|-- templates/
|   +-- build_search_criteria/
|       |-- system_prompt.jinja   # LLM instructions + JSON schema
|       +-- user_prompt.jinja     # Transcript input template
|
|-- static/                       # Landing page
|   |-- index.html
|   |-- css/style.css
|   +-- js/main.js
|
|-- tests/
|   |-- test_search_criteria.py   # Transcript -> criteria extraction
|   |-- test_contact_agent.py     # Contact agent form fill
|   +-- test_scrape_and_validate.py  # Full scrape + rank pipeline
|
|-- docs/                         # Technical docs
|   |-- ZILLOW_SCRAPER.md
|   +-- TRANSCRIPT_TO_CRITERIA.md
|
|-- run_e2e.py                    # End-to-end demo script
|-- trans.txt                     # Sample call transcript
|-- requirements.txt
|-- Procfile
+-- .env.example
```

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python, FastAPI, Uvicorn |
| **Voice agent** | Telnyx (calls + SMS), PersonaPlex (AI voice) |
| **AI / NLP** | Railtracks, OpenAI-compatible LLM endpoint |
| **Scraping** | ScraperAPI (Zillow search), BeautifulSoup (parsing) |
| **Browser automation** | Playwright + Stealth (contact agent form fill) |
| **Frontend** | HTML, CSS, JavaScript (landing page) |

---

## Search criteria schema

The LLM extracts this structure from a conversation:

```json
{
  "location": {
    "query": "Toronto",
    "city": "Toronto",
    "state_province": null,
    "neighborhood": null
  },
  "intent": "buy",
  "price": { "min": null, "max": 500000 },
  "bedrooms": { "min": 2, "max": null },
  "bathrooms": { "min": null, "max": null },
  "property_type": ["house"],
  "size": { "sqft_min": null, "sqft_max": null },
  "year_built": { "min": null, "max": null },
  "features": {
    "required": ["pet_friendly", "near_schools"],
    "nice_to_have": ["parking", "basement"]
  },
  "keywords": []
}
```

Supported property types: `house`, `condo`, `townhouse`, `land`

Supported features: `parking`, `garage`, `pool`, `basement`, `waterfront`, `pet_friendly`, `new_construction`, `laundry`, `ac`, `near_schools`, `near_transit`

---

## Listing scoring

After scraping, each listing is scored against the criteria:

- **Price**: within budget = +0.3, over budget = penalty scaled by overshoot
- **Bedrooms/bathrooms**: meeting minimums = bonus, below = violation
- **Property type**: matched from title/URL
- **Features**: checked from detail page (Facts & Features tab). Required features missing = violation; nice-to-have = bonus
- **Keywords**: matched against listing title

Listings are split into **exact matches** (no violations) and **nearest alternatives** (ranked by score, with violations listed).

---

## Further reading

- [Zillow Scraper docs](docs/ZILLOW_SCRAPER.md) — how the scraping and parsing pipeline works
- [Transcript to Criteria docs](docs/TRANSCRIPT_TO_CRITERIA.md) — how LLM extraction works
