"""
End-to-end test: transcript → LLM → search criteria → Zillow scrape → rank & validate.
Requires .env with GPT_OSS_BASE_URL, GPT_OSS_MODEL, SCRAPER_API_KEY.

Run:  python -m pytest tests/test_scrape_and_validate.py -v -s
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRANSCRIPT_PATH = ROOT / "trans.txt"


def test_full_pipeline():
    from app.agents.build_search_criteria import extract_search_criteria
    from data.zillow.scraper import search

    # Step 1: extract criteria from transcript
    transcript = TRANSCRIPT_PATH.read_text(encoding="utf-8")
    criteria = extract_search_criteria(transcript)

    print("\n=== SEARCH CRITERIA ===")
    print(json.dumps(criteria, indent=2))

    # Step 2: broad scrape + rank
    data = search(criteria)
    results = data["results"]

    print(f"\n=== {results['message']} ===")

    matches = results["matches"]
    nearest = results["nearest"]

    # Step 3: print matches
    if matches:
        print(f"\n--- EXACT MATCHES ({len(matches)}) ---")
        for r in matches:
            print(f"  [{r['_score']}] {r['title']}")
            print(f"       price={r['price']!r}  beds={r['beds']!r}")

    # Step 4: print nearest
    if nearest:
        print(f"\n--- CLOSEST ({len(nearest)}) ---")
        for r in nearest:
            print(f"  [{r['_score']}] {r['title']}")
            print(f"       price={r['price']!r}  beds={r['beds']!r}")
            for v in r["_violations"]:
                print(f"       !! {v}")

    # Step 5: summary
    total = len(matches) + len(nearest)
    print(f"\n=== SUMMARY ===")
    print(f"  Total scraped:  {total}")
    print(f"  Exact matches:  {len(matches)}")
    print(f"  Closest:        {len(nearest)}")
    print(f"  Search URL:     {data['search_url']}")

    assert total > 0, "No listings returned — scraper may have been blocked"

    # We always get results now — either matches or nearest
    assert matches or nearest, "Expected at least some listings in matches or nearest"

    if not matches:
        top = nearest[0]
        print(f"\n  Best near-match: {top['title']} (score {top['_score']})")
        print(f"  Issues: {', '.join(top['_violations'])}")
