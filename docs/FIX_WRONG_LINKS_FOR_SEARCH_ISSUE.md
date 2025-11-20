# Guide: Building a Hybrid Shopping Agent with Accurate Links

## 1. Problem Definition

**The Issue:**
Current agent uses the standard `google_search` tool (Google Grounding). This tool is excellent for summarizing information (reviews, specs, facts) but it obscures direct URLs behind redirect links (`vertexaisearch...`).
When user ask for a "shop link," the LLM (especially fast models like Flash) tries to "guess" the real URL based on the store name, resulting in broken links (404s) or hallucinated products.

**The Solution:**
Implement a **Hybrid Tool Architecture**:
1.  **Google Grounding:** Used for general knowledge, research, and summaries.
2.  **DuckDuckGo (Raw Search):** Used specifically to retrieve raw, valid, copy-pasteable URLs and current prices.

Here is the implementation plan for the **Sequential "Best Solution"** with added **Region Awareness**.

# Guide: Building "BuySpy" (Sequential Search + Region Detection)

**Goal:** Create a shopping agent that first researches the best products using Google, then finds specific, clickable shop links using DuckDuckGo.
**New Requirement:** The agent must respect the user's location. If the region is unknown, the agent must ask the user before searching for prices to avoid giving US links to a user in Finland (or vice versa).

## 2. Solution Architecture
*   **Agent:** Single Agent (`root_agent`) using `gemini-2.5-flash-lite`.
*   **Tools:**
    1.  `google_search`: For "What to buy" (Reviews/Specs).
    2.  `find_shopping_links`: For "Where to buy" (Price/URL).
*   **Logic:** The Prompt will enforce a 3-step workflow: **Identify Region -> Research -> Shop Search**.

---

## 3. Implementation Steps

### Step 1: Install Dependencies
```bash
pip install duckduckgo-search
```

### Step 2: Define the Custom Tool
We will design the tool to **require** a `region` code. This helps force the model to realize it needs this information.

```python
from duckduckgo_search import DDGS
import json

def find_shopping_links(product_name: str, region: str):
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
        return f"Error searching for links: {str(e)}"
```

### Step 3: Define the Agent with Sequential Logic
Here is the complete Agent definition. Note the updated `instruction` which acts as the "State Machine" for the conversation.

```python
from google.adk.model import Agent
from google.adk.tools.google_search_tool import google_search

# ... (Import your find_shopping_links function here) ...

return Agent(
    name="root_agent",
    model="gemini-2.5-flash-lite",
    tools=[google_search, find_shopping_links],
    instruction="""You are BuySpy, an intelligent shopping assistant.

    ### YOUR WORKFLOW (Follow strictly)

    **STEP 1: CHECK REGION**
    - Before finding any prices or links, you MUST know the user's region.
    - Check the conversation history. Did the user mention a country (Finland, US, UK)?
    - **IF REGION IS UNKNOWN:** Stop and ask: "Which country are you shopping in?"
    - **IF REGION IS KNOWN:** Map it to a code (Finland -> 'fi-fi', USA -> 'us-en', UK -> 'uk-en', Germany -> 'de-de', etc.) and proceed.

    **STEP 2: RESEARCH (The "What")**
    - If the user asks generic questions (e.g., "Best headphones?"), use `google_search`.
    - Summarize the best options, pros/cons, and select specific models to recommend.

    **STEP 3: SHOPPING (The "Where")**
    - Once you have specific model names AND the region code, use the `find_shopping_links` tool.
    - Call this tool for EACH recommended product individually.
    - **CRITICAL:** Extract the 'href' (URL) exactly as provided by the tool. Do not guess URLs.

    ### RESPONSE FORMAT
    When recommending products, use this structure:

    **[Product Name]**
    *   **Why it's good:** [Summary from Step 2]
    *   **Best Price:** [Price from Step 3] at [Store Name from Step 3]
    *   **Link:** [Direct URL from Step 3]
    """
)
```

---

## 4. How the Conversation Will Flow

Here is a simulation of how this code behaves in practice:

#### Scenario A: User DOES NOT state region
**User:** "What are the best cheap noise cancelling headphones?"
**BuySpy (Step 1 triggered):** "I can help with that! To give you accurate prices and links, **which country are you shopping in?**"
**User:** "Finland."
**BuySpy (Step 2 & 3 triggered):** "Thanks! Searching for the best options in Finland..."
*(Internal: Calls `google_search` for reviews -> Finds 'Soundcore Q30' -> Calls `find_shopping_links('Soundcore Q30', 'fi-fi')` -> Returns results)*

#### Scenario B: User STATES region
**User:** "Find me the best deals on Sony headphones in **Finland**."
**BuySpy (Step 1 triggered):** *(Detects 'Finland' -> sets region='fi-fi')*
*(Proceeds immediately to research and shopping)*
**BuySpy:** "Here are the best deals on Sony headphones available in Finnish stores..."

---

## 5. Summary Checklist
1.  [ ] **Library:** `pip install duckduckgo-search` is installed.
2.  [ ] **Model:** Changed to `gemini-1.5-flash-002`.
3.  [ ] **Tools:** Passed `[google_search, find_shopping_links]`.
4.  [ ] **Prompt:** Includes the "STEP 1: CHECK REGION" instruction.
