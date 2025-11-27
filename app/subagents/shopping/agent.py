from google.adk.agents import Agent
from google.adk.apps.app import App
from google.adk.models.google_llm import Gemini
from google.adk.plugins import ReflectAndRetryToolPlugin
from google.adk.tools import AgentTool
from google.genai.types import GenerateContentConfig

from app.subagents.config import default_retry_config
from app.subagents.price_extractor.agent import price_extractor_agent
from app.tools.search_tools_bd import brightdata_toolset


def _create_shopping_agent(price_extractor_agent: Agent) -> Agent:
    """Uses BrightData SERP search and web crawler to find and verify product prices."""
    return Agent(
        name="shopping_agent",
        # model="gemini-2.5-flash-lite",
        model=Gemini(model="gemini-2.5-flash", retry_options=default_retry_config),
        tools=[brightdata_toolset, AgentTool(price_extractor_agent)],
        generate_content_config=GenerateContentConfig(
            temperature=0.1,
        ),
        instruction="""You are a Price Search Engine using BrightData.

**TASK:** Find the 5 best available prices for "[Product Name] in [Country Name]"
**Input:** [Product Name] price in [Country Name]

## WORKFLOW

### 1. SERP Search
- Query: "[Product Name] price [Country Name]"
- Engine: "google"
- For non-English countries (Finland→Finnish, Germany→German, etc.), translate generic terms but keep brand names and model numbers unchanged
  - Example: "Sony WH-CH520 wireless headphones" → "Sony WH-CH520 langattomat kuulokkeet"

### 2. Filter & Deduplicate URLs
From SERP results:
- **Remove:** Search engines (google.com, bing.com, yandex.ru), social media, forums, blogs, news sites
- **Deduplicate:** Keep only ONE link per shop domain (e.g., if 3 amazon.de links, keep the most relevant product page)
- **Extract domain:** "https://www.verkkokauppa.com/fi/product/123" → domain is "verkkokauppa.com"

### 3. Prioritize URLs
From filtered URLs (target: 3-7 unique shops), assign priority tiers:
- **Tier 1:** Official stores, major local retailers, country price comparison sites
- **Tier 2:** International retailers with country sites (amazon.de, amazon.fi)
- **Tier 3:** Generic international sites (amazon.com, ebay.com)

Sort URLs: Tier (1>2>3) → Domain (alphabetically) → Path (alphabetically)

### 4. Delegate to price_extractor tool (IN PARALLEL)
For EACH of the first 3-7 sorted URLs, call `price_extractor` with:
- URL to scrape
- Tier assignment for that URL
- Product name (for verification)

Run all calls IN PARALLEL (don't wait for one to finish before starting the next).

Each `price_extractor_agent` will scrape the URL and return extracted JSON or null.

### 5. Collect Results
Wait for all parallel extractions to complete. Collect all non-null results.
**CRITICAL:** Some agents may fail, return "Error", return "Resource Exhausted", or return null.
- **IGNORE** any result that is not valid JSON.
- **IGNORE** any result containing error messages.
- **IGNORE** any result that is `null`.
- **DO NOT** stop or complain if some agents fail. As long as you have at least 1 valid result, proceed.

### 6. Select Top 5
From collected results:
1. Filter: Keep only "In Stock" or "Limited Availability"
2. Sort by price (lowest first, numerical comparison)
3. For price ties: Prefer Tier 1 > country domains (.fi, .de) > earlier in list
4. Take first 5

### 7. Output JSON
```json
{
  "product": "Product Name",
  "country": "Country Name",
  "results": [
    {
      "rank": 1,
      "price": "99.99 EUR",
      "store": "Store Name",
      "url": "https://...",
      "status": "In Stock"
    }
  ],
  "total_found": 7
}
```

If fewer than 5: Include "note": "Only X results available"
If none: Include "error": "No available products found"

**RULES:**
- Always sort URLs deterministically before delegating
- Call price_extractor_agent for EACH URL in parallel
- Never handle raw HTML yourself - that's the extractor's job
- Handle selection and ranking after collecting all results
- Return ONLY valid JSON, no extra text""",
    )


# Create shopping agent using imported price_extractor_agent
shopping_agent = _create_shopping_agent(price_extractor_agent)


# Main app uses shopping agent which delegates scraping+extraction to multiple parallel extractor calls
app = App(
    root_agent=shopping_agent,
    name="shopping",
    plugins=[
        ReflectAndRetryToolPlugin(max_retries=10),
    ],
)
