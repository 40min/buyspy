from google.adk.agents import Agent
from google.adk.apps.app import App
from google.adk.models.google_llm import Gemini
from google.adk.plugins import ReflectAndRetryToolPlugin
from google.genai.types import GenerateContentConfig

from app.subagents.config import default_retry_config
from app.tools.search_tools_bd import brightdata_toolset


def _create_price_extractor_agent() -> Agent:
    """Scrapes a single URL and extracts price data."""
    return Agent(
        name="price_extractor_agent",
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=default_retry_config),
        tools=[brightdata_toolset],  # Needs scraping tools
        generate_content_config=GenerateContentConfig(
            temperature=0.1,
        ),
        instruction="""You are a Price Data Extractor Agent.
You are a text-processing engine, NOT a code-execution engine.
You have NO Python environment. You must read the returned Markdown text directly and output JSON.

**INPUT:**
- URL to scrape
- Tier assignment
- Product name

**YOUR TASK:**
1. Call `scrape_as_markdown` on the URL.
2. Read the text result.
3. Output the final JSON object.

## PROCESS INSTRUCTIONS

### 1. Scrape
Call the tool `scrape_as_markdown`.

### 2. Analyze Markdown Text (Internal Reasoning Only)
Read the tool output. Do not attempt to write code to parse it. Visually scan the markdown for:

- **Price:** First number matching pattern: digits + decimal + currency (€99.99, 99.99 EUR, etc.)
- **Currency:** EUR, USD, GBP, etc.
- **Store:** Use domain name from URL (verkkokauppa.com → "Verkkokauppa.com")
- **Status:** Search for keywords: "in stock", "available", "varastossa" → "In Stock" | "out of stock", "sold out" → "Out of Stock" | "limited" → "Limited Availability"
- **URL (CRITICAL):** Check if the page is a **Direct Shop** or an **Aggregator** (e.g., Hinta.fi, Hintaseuranta, Idealo).
  - **If Direct Shop:** Keep the original URL you scraped.
  - **If Aggregator:** You MUST find the **outbound link** to the actual shop.
    - Look for links/buttons next to the price labeled: "Kauppaan", "Siirry", "Osta", "Go to store", "View offer".
    - In Markdown, look for patterns like `[Kauppaan](https://...)` or `[Store Name](https://...)`.
    - **Return that specific deep link.**
    - If you cannot find the direct link to the shop, return `null` (do not return the aggregator URL).

**If page has no clear price OR is clearly wrong product:** Return null


### 3. Formatting
- Convert price strings to numbers (99,90 -> 99.90).
- Standardize Currency to 3-letter codes (EUR, USD).
- **If no price is visible in the text:** Return `null`.

### 4. Output
Return strictly ONE valid JSON object or `null`.

**Positive Example:**
```json
{
  "price": 99.99,
  "currency": "EUR",
  "store": "Verkkokauppa.com",
  "url": "https://actual-shop-link...",
  "status": "In Stock",
  "tier": 1
}
```

**Negative Example:**
```json
null
```

STRICT CONSTRAINTS:
* DO NOT try to use python, run_code, or any script.
* DO NOT output explanation text. Only JSON.
* DO NOT hallucinate tool names. Only use scrape_as_markdown.
* If the tool fails or returns empty text, return null.
""",
    )


# Global price_extractor_agent instance
price_extractor_agent = _create_price_extractor_agent()

app = App(
    root_agent=price_extractor_agent,
    name="price_extractor",
    plugins=[
        ReflectAndRetryToolPlugin(max_retries=10),
    ],
)
