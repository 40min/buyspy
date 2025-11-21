import json

from duckduckgo_search import DDGS


def find_shopping_links(product_name: str, region: str) -> str:
    """
    Finds direct shop links and current prices for a specific product in a specific region.

    Args:
        product_name: The specific model name to search for (e.g. "Sony WH-CH720N").
        region: The region code to search in (e.g., "fi-fi" for Finland, "us-en" for USA, "de-de" for Germany).
    """
    # Construct a query like "Sony WH-CH720N price"
    query = f"{product_name} price"

    print(f"DEBUG: Searching for '{query}' in region '{region}'")

    try:
        # Perform the search
        results = DDGS().text(query, region=region, max_results=3)
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error searching for links: {e!s}"
