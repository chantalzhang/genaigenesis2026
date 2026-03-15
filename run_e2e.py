"""End-to-end: transcript -> search criteria -> scrape -> pick listing -> contact agent."""
import json
import sys
sys.path.insert(0, ".")

from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

ROOT = Path(__file__).resolve().parent

# -- Step 1: Extract search criteria from transcript --
print("=" * 60)
print("STEP 1: Extracting search criteria from transcript")
print("=" * 60)

transcript = (ROOT / "trans.txt").read_text(encoding="utf-8")
from app.agents.build_search_criteria import extract_search_criteria
criteria = extract_search_criteria(transcript)
print(json.dumps(criteria, indent=2))

# -- Step 2: Scrape Zillow listings --
print("\n" + "=" * 60)
print("STEP 2: Scraping Zillow listings")
print("=" * 60)

from data.zillow.scraper import search
data = search(criteria, fetch_details=False)

results = data["results"]
print(f"\nSearch URL: {data['search_url']}")
print(f"Message: {results['message']}")
print(f"Exact matches: {len(results['matches'])}")
print(f"Nearest: {len(results['nearest'])}")

all_listings = results["matches"] + results["nearest"]
if not all_listings:
    print("\nNo listings found. Exiting.")
    sys.exit(1)

print("\n-- Top 5 listings --")
for i, l in enumerate(all_listings[:5]):
    title = (l.get("title") or "N/A").encode("ascii", "replace").decode()
    print(f"  {i+1}. {title[:60]}")
    print(f"     Price: {l.get('price', '?')}  Beds: {l.get('beds', '?')}  Baths: {l.get('baths', '?')}")
    print(f"     URL: {l.get('url', 'N/A')}")
    print(f"     Score: {l.get('_score', '?')}  Violations: {l.get('_violations', [])}")

# -- Step 3: Try listings until contact agent works --
from app.contact import Lead, run_contact_flow
lead = Lead()

MAX_ATTEMPTS = 3
result = None

for attempt, picked in enumerate(all_listings[:MAX_ATTEMPTS], 1):
    listing_url = picked.get("url", "")
    if not listing_url:
        continue

    title = (picked.get("title") or "N/A").encode("ascii", "replace").decode()
    print(f"\n{'=' * 60}")
    print(f"STEP 3: Contact agent (attempt {attempt}/{MAX_ATTEMPTS})")
    print("=" * 60)
    print(f"  Listing: {title[:60]}")
    print(f"  URL: {listing_url}")
    print(f"  Lead: {lead.name} / {lead.email} / {lead.phone}")
    print(f"  Mode: preview (fill only)\n")

    result = run_contact_flow(
        listing_url,
        lead,
        mode="preview",
        headless=False,
        slow_mo_ms=150,
        use_proxy=False,
    )

    print(f"\n  CTA found:     {result.cta_found}")
    print(f"  Form found:    {result.form_found}")
    print(f"  Fields filled: {result.fields_filled}")
    print(f"  Submit found:  {result.submit_button_found}")
    if result.error:
        print(f"  Error:         {result.error}")

    if result.cta_found and result.form_found:
        print("\n  >> SUCCESS - form filled!")
        break
    else:
        print(f"\n  >> CTA not found on this listing, trying next...")

if not result or not result.cta_found:
    print(f"\nFailed to find Contact Agent on any of the top {MAX_ATTEMPTS} listings.")
