import json

from ddgs import DDGS


def find_shopping_links(product_name: str, region: str) -> str:
    """
    Searches for current product prices and purchase links in a specific region.

    Use this tool when the user asks to "buy", "find price", or "shop" for an item.
    It returns a list of search results containing URLs and snippets.

    Args:
        product_name: The specific name of the product (e.g., "Sony WF-C510").
        region: The ISO region code to localize results.
                Supported codes: "fi-fi" (Finland), "us-en" (USA), "de-de" (Germany),
                "uk-en" (UK), "fr-fr" (France).
                If the user's location is unknown, default to "us-en".

    Returns:
        str: A JSON string containing a list of search results with titles, links, and snippets.
    """
    # Inject local keywords. For Finland, "hinta" (price) and "halvin" (cheapest)
    search_modifiers = {
        "fi-fi": "hinta suomi osta",  # "price finland buy"
        "us-en": "price usa buy",
        "de-de": "preis deutschland kaufen",
        "uk-en": "price uk buy",
        "fr-fr": "prix france acheter",
    }
    # 2. Get the modifier, default to English if region unknown
    suffix = search_modifiers.get(region.lower(), "price buy")

    # 3. Construct a "Strong" query
    # Old Query: "Sony WF-C510" -> Returns global news/junk
    # New Query: "Sony WF-C510 hinta suomi osta" -> Forces Finnish shops
    final_query = f"{product_name} {suffix}"

    try:
        # Fetch slightly more results to give the agent options
        # We still pass the region param, but the text query does the heavy lifting
        results = DDGS().text(final_query, region=region, max_results=5)
        return json.dumps(results)
    except Exception as e:
        return f"Error finding links: {e!s}"
