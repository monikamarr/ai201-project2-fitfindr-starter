"""
tools.py

The three required FitFindr tools.
"""

import os
import re

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


def _clean_terms(text: str) -> set[str]:
    """Turn a search string into useful lowercase keywords."""
    stop_words = {
        "a", "an", "the", "i", "im", "i'm", "want", "looking", "for",
        "under", "below", "less", "than", "size", "and", "or", "with",
        "to", "of", "in", "on", "what", "whats", "what's", "out", "there",
        "how", "would", "style", "it", "me", "my"
    }

    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {word for word in words if word not in stop_words}


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search listings by description, optional size, and optional max price.
    Returns matching listings sorted by relevance.
    """
    listings = load_listings()
    query_terms = _clean_terms(description)

    scored_results = []

    for item in listings:
        if max_price is not None and item.get("price", 0) > max_price:
            continue

        if size:
            item_size = str(item.get("size", "")).lower()
            requested_size = size.lower()

            if requested_size not in item_size:
                continue

        searchable_text = " ".join([
            str(item.get("title", "")),
            str(item.get("description", "")),
            str(item.get("category", "")),
            str(item.get("condition", "")),
            str(item.get("brand", "")),
            str(item.get("platform", "")),
            " ".join(item.get("style_tags", [])),
            " ".join(item.get("colors", [])),
        ]).lower()

        score = sum(1 for term in query_terms if term in searchable_text)

        if score > 0:
            scored_results.append((score, item))

    scored_results.sort(
        key=lambda pair: (pair[0], -pair[1].get("price", 999999)),
        reverse=True,
    )

    return [item for score, item in scored_results]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and wardrobe, suggest 1–2 complete outfits.
    """
    if not new_item:
        return "I need a selected item before I can suggest an outfit."

    client = _get_groq_client()
    wardrobe_items = wardrobe.get("items", []) if wardrobe else []

    if wardrobe_items:
        wardrobe_text = "\n".join(str(item) for item in wardrobe_items)

        prompt = f"""
You are FitFindr, a helpful fashion styling assistant.

The user is considering buying this thrifted item:
{new_item}

Here are items already in the user's wardrobe:
{wardrobe_text}

Suggest 1–2 complete outfits using the thrifted item and specific pieces from the wardrobe.
Make the styling advice practical, specific, and easy to understand.
Mention why the outfit works.
Keep your response concise.
"""
    else:
        prompt = f"""
You are FitFindr, a helpful fashion styling assistant.

The user is considering buying this thrifted item:
{new_item}

The user's wardrobe is empty or unavailable.

Suggest 1–2 general outfit ideas for styling this item.
Mention what types of bottoms, shoes, layers, or accessories would pair well with it.
Make the styling advice practical and specific.
Keep your response concise.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a concise, stylish fashion assistant.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.
    """
    if not outfit or not outfit.strip():
        return "I need an outfit suggestion before I can create a fit card."

    if not new_item:
        return "I need a selected item before I can create a fit card."

    client = _get_groq_client()

    item_name = new_item.get("title", "this thrifted item")
    price = new_item.get("price", "N/A")
    platform = new_item.get("platform", "a secondhand platform")

    prompt = f"""
You are writing a short social-media outfit caption.

Thrifted item:
- Name: {item_name}
- Price: ${price}
- Platform: {platform}
- Full item details: {new_item}

Outfit suggestion:
{outfit}

Write a 2–4 sentence caption.

Requirements:
- Sound casual and authentic, like a real OOTD post.
- Mention the item name once.
- Mention the price once.
- Mention the platform once.
- Capture the outfit vibe in specific terms.
- Do not sound like a product description.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You write stylish, casual outfit captions.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.95,
    )

    return response.choices[0].message.content.strip()