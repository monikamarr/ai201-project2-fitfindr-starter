import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_empty_wardrobe, get_example_wardrobe

def test_search_listings_returns_results():
    results = search_listings(
        description="vintage graphic tee",
        size=None,
        max_price=30,
    )

    assert isinstance(results, list)
    assert len(results) > 0
    assert isinstance(results[0], dict)


def test_search_listings_filters_by_price():
    results = search_listings(
        description="tee",
        size=None,
        max_price=20,
    )

    assert isinstance(results, list)
    assert all(item["price"] <= 20 for item in results)


def test_search_listings_filters_by_size():
    results = search_listings(
        description="graphic tee",
        size="M",
        max_price=None,
    )

    assert isinstance(results, list)
    assert all("m" in item["size"].lower() for item in results)


def test_search_listings_no_results():
    results = search_listings(
        description="designer ballgown",
        size="XXS",
        max_price=5,
    )

    assert results == []


def test_suggest_outfit_missing_item():
    result = suggest_outfit(
        new_item={},
        wardrobe=get_example_wardrobe(),
    )

    assert isinstance(result, str)
    assert "selected item" in result.lower()


def test_create_fit_card_missing_outfit():
    sample_item = {
        "title": "Vintage Graphic Tee",
        "price": 24.0,
        "platform": "Depop",
    }

    result = create_fit_card(
        outfit="",
        new_item=sample_item,
    )

    assert isinstance(result, str)
    assert "outfit suggestion" in result.lower()


@pytest.mark.llm
def test_suggest_outfit_empty_wardrobe_llm():
    results = search_listings(
        description="vintage graphic tee",
        size=None,
        max_price=30,
    )

    assert len(results) > 0

    result = suggest_outfit(
        new_item=results[0],
        wardrobe=get_empty_wardrobe(),
    )

    assert isinstance(result, str)
    assert len(result.strip()) > 0


@pytest.mark.llm
def test_create_fit_card_llm():
    sample_item = {
        "title": "Vintage Graphic Tee",
        "price": 24.0,
        "platform": "Depop",
    }

    outfit = "Pair the tee with baggy jeans and chunky sneakers for a casual streetwear look."

    result = create_fit_card(
        outfit=outfit,
        new_item=sample_item,
    )

    assert isinstance(result, str)
    assert len(result.strip()) > 0