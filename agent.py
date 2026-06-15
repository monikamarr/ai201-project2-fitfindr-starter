"""
agent.py

The FitFindr planning loop.
"""

import re

from tools import search_listings, suggest_outfit, create_fit_card


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    return {
        "query": query,
        "parsed": {},
        "search_results": [],
        "selected_item": None,
        "wardrobe": wardrobe,
        "outfit_suggestion": None,
        "fit_card": None,
        "error": None,
    }


# ── query parsing ─────────────────────────────────────────────────────────────

def _parse_query(query: str) -> dict:
    """
    Extract description, size, and max_price from a natural-language query.
    """
    lower_query = query.lower()

    max_price = None
    price_match = re.search(
        r"(?:under|below|less than)\s*\$?(\d+(?:\.\d+)?)",
        lower_query,
    )
    if price_match:
        max_price = float(price_match.group(1))

    size = None
    size_match = re.search(r"size\s+([a-zA-Z0-9/]+)", lower_query)
    if size_match:
        size = size_match.group(1).upper()

    description = query

    description = re.sub(
        r"(?:under|below|less than)\s*\$?\d+(?:\.\d+)?",
        "",
        description,
        flags=re.IGNORECASE,
    )

    description = re.sub(
        r"size\s+[a-zA-Z0-9/]+",
        "",
        description,
        flags=re.IGNORECASE,
    )

    description = description.replace("I'm looking for", "")
    description = description.replace("im looking for", "")
    description = description.replace("looking for", "")
    description = description.replace("I want", "")
    description = description.replace("i want", "")

    description = description.strip(" .,!")

    return {
        "description": description,
        "size": size,
        "max_price": max_price,
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    session = _new_session(query, wardrobe)

    parsed = _parse_query(query)
    session["parsed"] = parsed

    results = search_listings(
        description=parsed["description"],
        size=parsed["size"],
        max_price=parsed["max_price"],
    )

    session["search_results"] = results

    if not results:
        session["error"] = (
            "I couldn't find any matching listings. Try a broader description, "
            "a higher budget, or a different size."
        )
        return session

    selected_item = results[0]
    session["selected_item"] = selected_item

    outfit = suggest_outfit(selected_item, wardrobe)
    session["outfit_suggestion"] = outfit

    if not outfit or not outfit.strip():
        session["error"] = (
            "I found a listing, but couldn't generate an outfit suggestion."
        )
        return session

    fit_card = create_fit_card(outfit, selected_item)
    session["fit_card"] = fit_card

    if not fit_card or not fit_card.strip():
        session["error"] = (
            "I generated an outfit suggestion, but couldn't create a fit card."
        )
        return session

    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )

    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")