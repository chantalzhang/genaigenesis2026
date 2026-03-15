"""
Tool: Inspect a Zillow listing detail page for contact form structure,
API endpoints, and GraphQL mutations.

Usage:
    python -m inspect_tools.inspect_contact_form <url_or_local_html>

Examples:
    python -m inspect_tools.inspect_contact_form https://www.zillow.com/apartments/cranford-nj/fairways-at-cranford/Cknr46/
    python -m inspect_tools.inspect_contact_form data/output/some_listing.html
"""
import json
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup


def inspect_forms(html: str):
    """Find all form elements and their action/method."""
    soup = BeautifulSoup(html, "html.parser")
    forms = soup.select("form")
    print(f"\n=== FORMS ({len(forms)}) ===")
    for i, form in enumerate(forms):
        action = form.get("action", "(none)")
        method = form.get("method", "(none)")
        form_id = form.get("id", "")
        form_class = form.get("class", [])
        inputs = form.select("input, textarea, select")
        print(f"\n  Form #{i}: id={form_id!r} class={form_class}")
        print(f"    action={action!r} method={method!r}")
        print(f"    fields ({len(inputs)}):")
        for inp in inputs:
            name = inp.get("name", "")
            typ = inp.get("type", inp.name)
            placeholder = inp.get("placeholder", "")
            print(f"      {inp.name} name={name!r} type={typ!r} placeholder={placeholder!r}")


def inspect_api_endpoints(html: str):
    """Search for API endpoint patterns in the page source."""
    print("\n=== API ENDPOINT PATTERNS ===")
    patterns = [
        (r"https?://[^\"'\s]+/api/[^\"'\s]+contact[^\"'\s]*", "contact API"),
        (r"https?://[^\"'\s]+/api/[^\"'\s]+lead[^\"'\s]*", "lead API"),
        (r"https?://[^\"'\s]+/api/[^\"'\s]+inquiry[^\"'\s]*", "inquiry API"),
        (r'fetch\s*\(\s*["\']([^"\']+)["\']', "fetch() calls"),
        (r'"submitUrl"\s*:\s*"([^"]+)"', "submitUrl"),
        (r'"graphQLURL"\s*:\s*"([^"]+)"', "graphQLURL"),
    ]
    for pattern, label in patterns:
        matches = list(set(re.findall(pattern, html)))
        if matches:
            print(f"\n  [{label}] ({len(matches)} unique)")
            for m in matches[:10]:
                print(f"    {m[:200]}")


def inspect_contact_data(html: str):
    """Look for contact/lead/form config in Next.js data."""
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.select('script[type="application/json"]'):
        try:
            d = json.loads(script.string or "")
            if not isinstance(d, dict) or "props" not in d:
                continue
            print("\n=== NEXT.JS DATA - CONTACT RELATED ===")
            _search_dict(d, ["contact", "lead", "inquiry", "omp", "formSubmit", "agentEmail", "listingAgent"], "root")
            break
        except json.JSONDecodeError:
            pass


def _search_dict(obj, keywords, path, depth=0):
    if depth > 6:
        return
    if isinstance(obj, dict):
        for key in obj:
            key_lower = key.lower()
            if any(kw in key_lower for kw in keywords):
                val = obj[key]
                val_str = json.dumps(val, indent=2) if isinstance(val, (dict, list)) else str(val)
                if len(val_str) < 3000:
                    print(f"\n  FOUND '{key}' at {path}.{key}")
                    print(f"  {val_str[:2000]}")
                else:
                    print(f"\n  FOUND '{key}' at {path}.{key} (large, {len(val_str)} chars)")
                    if isinstance(val, dict):
                        print(f"  keys: {list(val.keys())[:20]}")
            if isinstance(obj[key], (dict, list)):
                _search_dict(obj[key], keywords, f"{path}.{key}", depth + 1)
    elif isinstance(obj, list):
        for i, item in enumerate(obj[:5]):
            _search_dict(item, keywords, f"{path}[{i}]", depth + 1)


def inspect_js_bundles(html: str):
    """List JS bundle URLs and flag contact-relevant ones."""
    soup = BeautifulSoup(html, "html.parser")
    print("\n=== JS BUNDLES ===")
    for s in soup.select("script[src]"):
        src = s.get("src", "")
        if src:
            relevant = any(kw in src.lower() for kw in ("contact", "lead", "omp", "inquiry", "form"))
            marker = " <-- RELEVANT" if relevant else ""
            print(f"  {src}{marker}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    target = sys.argv[1]
    path = Path(target)

    if path.exists():
        print(f"Reading local file: {path}")
        html = path.read_text(encoding="utf-8")
    else:
        print(f"Fetching URL: {target}")
        from data.zillow.playwright_fetch import fetch_html
        html = fetch_html(target, headless=True)
        if not html:
            print("Failed to fetch page.")
            sys.exit(1)

    inspect_forms(html)
    inspect_api_endpoints(html)
    inspect_contact_data(html)
    inspect_js_bundles(html)


if __name__ == "__main__":
    main()
