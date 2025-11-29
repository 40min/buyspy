# Project Description: BuySpy - Your Personal & Localized AI Shopping Concierge

<div align="center">
  <img src="res/buyspy_sm.png" alt="BuySpy Logo" width="200">
</div>
# Project Description: BuySpy - Your Personal & Localized AI Shopping Concierge

## 1. Problem Statement

Online shopping is overwhelming and impersonal. Consumers spend hours sifting through countless product pages, comparing specifications, and struggling to find the best prices across multiple retailers. This leads to decision fatigue and wasted time. Furthermore, existing shopping assistants are generic and disconnected from the user's local context. They fail to understand personal preferences, cannot efficiently compare prices across stores, and offer a one-size-fits-all experience that ignores regional nuances, resulting in irrelevant recommendations and a frustrating process.

## 2. Proposed Solution

**BuySpy** is an AI-powered shopping concierge agent that delivers a personalized and localized shopping experience. BuySpy acts as your personal shopper via a simple chat interface (Telegram), doing the heavy lifting of product research, price comparison, and intelligent routing between shopping and general conversation.

It leverages a team of specialized agents working in parallel to search for products, extract prices from multiple retailers, and provide comprehensive comparisons. Using enterprise-grade web scraping through BrightData's Streamable HTTP MCP service, BuySpy efficiently navigates e-commerce sites and price comparison platforms to find the best available deals. The system remembers user preferences and conversation context, transforming online shopping from a stressful task into a seamless and personalized conversation.

## 3. Core Functionality & Technical Architecture

BuySpy is architected as a modular, multi-agent system where a central orchestrator delegates tasks to a team of specialized agents. This design allows for clear separation of concerns and showcases advanced agentic patterns including parallel execution and intelligent routing.

### Agent Architecture

The system is orchestrated by the **`root_agent`** (Orchestrator), the primary user-facing component. It manages the conversational flow, detects user intent (shopping vs. general conversation), handles country detection, and maintains conversation context through ADK's built-in memory system with auto-save functionality.

When a user makes a request, the `root_agent` analyzes intent and invokes one or more specialist agents:

#### Specialist Agents

*   **`smalltalk_agent`:** Handles general knowledge questions, casual conversations, and non-shopping queries. Uses Google Search for current information and has a witty, engaging personality. Examples: "What's the capital of Finland?", "Tell me about quantum physics", "Recommend a good book".

*   **`research_agent`:** Performs product research to find top recommendations for a given category and country. Uses Google Search with specialized prompts to identify 1-5 recommended models with reasoning (e.g., "Best Value", "Best Battery Life"). Returns structured JSON with model names and reasons.

*   **`shopping_agent`:** The main price-finding agent that coordinates the shopping workflow:
    1. Uses BrightData's Streamable HTTP MCP service for SERP search to find product listings
    2. Filters and deduplicates URLs by domain
    3. Prioritizes URLs into tiers (official stores, local retailers, international sites)
    4. Delegates to multiple `price_extractor_agent` instances **in parallel**
    5. Collects and ranks results by price and availability

*   **`price_extractor_agent`:** Specialized web scraping agent that:
    1. Scrapes individual product pages using BrightData's Streamable HTTP MCP service
    2. Detects if page is a price comparison site (aggregator) or direct shop
    3. If aggregator: finds best price, extracts shop URL, and rescrapes the actual shop
    4. Extracts price, currency, store name, availability status
    5. Returns structured JSON or null if extraction fails

### Key Technical Features

*   **BrightData Streamable HTTP MCP Integration:** Enterprise-grade SERP search and web crawling via Model Context Protocol (MCP) over Streamable HTTP, providing reliable scraping with automatic redirect handling without requiring Node.js dependencies.

*   **Parallel Execution:** The shopping agent calls multiple price extractor agents simultaneously (one per URL), significantly improving response time.

*   **Smart Aggregator Detection:** Price extractor automatically detects price comparison sites and navigates to actual shop pages, handling redirect URLs transparently.

*   **Memory System:** Uses ADK's built-in memory with `load_memory` tool and auto-save callback, maintaining conversation context and user preferences across sessions.

*   **Intent-Based Routing:** Orchestrator intelligently routes between shopping workflow and general conversation based on query analysis.

This architecture allows for complex, dynamic workflows. For a query like "Best headphones in Finland," the orchestrator would:
1. Detect shopping intent and country
2. Call `research_agent` to get recommendations
3. Present options and ask user which to price check
4. Call `shopping_agent` which spawns multiple `price_extractor_agent` instances in parallel
5. Compile and format results with prices, stores, and availability

## 4. Key Features (Current Implementation)

*   **Conversational Interface:** Natural language interaction via a Telegram bot with Markdown V2 formatting.
*   **Multi-Agent System:** Five specialized agents working together (orchestrator, research, shopping, price extractor, smalltalk).
*   **Intelligent Intent Detection:** Automatically routes between shopping queries and general conversation.
*   **Memory & Context:** Remembers conversation context and user preferences using ADK's built-in memory system.
*   **Localized Search:** Identifies user's country to tailor product searches and results.
*   **Product Research:** Finds top recommended products for any category using Google Search.
*   **Parallel Price Extraction:** Efficiently scrapes multiple stores simultaneously for best prices.
*   **Smart Aggregator Handling:** Automatically detects price comparison sites and navigates to actual shop pages.
*   **Enterprise Web Scraping:** Uses BrightData's Streamable HTTP MCP service for reliable SERP search and web crawling.
*   **Comparison Summaries:** Presents structured comparisons with prices, stores, availability, and store tier ratings.
*   **General Knowledge:** Handles non-shopping queries with a witty, engaging personality.

## 5. Future Enhancements

### High Priority
*   **Local Marketplace Integration (Tori.fi):** Add support for searching Finland's premier second-hand marketplace with custom scraping tools.
*   **Review Analysis & Vendor Vetting:** Integrate Google Places API to fetch shop ratings and review counts for trust building.
*   **Translation Service:** Add automatic translation for queries in non-English markets.

### Medium Priority
*   **Custom Firestore Memory:** Migrate from ADK's built-in memory to custom Firestore implementation for more control over user profiles and interaction history.
*   **Location Detection Agent:** Dedicated agent for determining user's shopping region automatically.
*   **Enhanced Error Handling:** More robust retry logic and fallback mechanisms for external API failures.

### Long-term Vision
*   **Proactive Monitoring Agent:** Long-running agent to track items for price drops, flash sales, or restocks (demonstrating LROs).
*   **Advanced Gift Recommendations:** Specialized agent that reasons about gift ideas based on recipient's profile and budget.
*   **Style/Mood Board Inspiration:** Allow users to send images to find visually similar items, leveraging multimodal models.
*   **Multi-marketplace Support:** Expand to other European marketplaces (Blocket, Marktplaats, Leboncoin).
