import json

from ddgs import DDGS


def find_shopping_links(product_name: str, region: str):
    """
    Finds shop links. Prioritizes price comparison sites for better accuracy.
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
