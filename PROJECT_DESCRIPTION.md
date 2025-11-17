# Project Description: BuySpy - Your Personal & Localized AI Shopping Concierge

<div align="center">
  <img src="res/buyspy_sm.png" alt="BuySpy Logo" width="200">
</div>
# Project Description: BuySpy - Your Personal & Localized AI Shopping Concierge

## 1. Problem Statement

Online shopping is overwhelming and impersonal. Consumers spend hours sifting through countless product pages, comparing specifications, and struggling to distinguish genuine feedback from sponsored content or fake reviews. This leads to decision fatigue and a lack of trust. Furthermore, existing shopping assistants are generic and disconnected from the user's local context. They fail to understand personal preferences, cannot search popular local marketplaces for second-hand goods, and offer a one-size-fits-all experience that ignores regional nuances, resulting in irrelevant recommendations and a frustrating process.

## 2. Proposed Solution

I will be building **BuySpy**, an AI-powered shopping concierge agent that delivers a deeply personalized and localized shopping experience. BuySpy acts as your personal shopper via a simple chat interface (Telegram), doing the heavy lifting of product research, review analysis, and vendor vetting.

It not only learns and remembers your style but also leverages a team of specialized agents to search global e-commerce sites, local marketplaces like Finland's Tori.fi, and analyze community feedback. By synthesizing this information, BuySpy provides comprehensive, trustworthy, and relevant options, transforming online shopping from a stressful task into a seamless and personalized conversation.

## 3. Core Functionality & Technical Architecture

BuySpy is architected as a modular, multi-agent system where a central orchestrator delegates tasks to a team of specialized agents. This design allows for clear separation of concerns and showcases advanced agentic patterns.

The system is orchestrated by the **`OrchestratorAgent`**, the primary user-facing component. It manages the conversational flow, understands user intent, and maintains both short-term session state and **long-term memory** of user preferences (e.g., name, clothing size, favorite brands) via a custom **Memory Bank** tool connected to a Google Cloud Firestore database.

When a user makes a request, the `OrchestratorAgent` devises a plan and invokes one or more specialist agents:

*   **`LocationAgent`:** To provide localized results, this agent's sole purpose is to determine the user's shopping region, ensuring subsequent searches are relevant.
*   **`TranslationAgent`:** To break down language barriers, this agent uses a **custom tool** wrapping the Google Cloud Translation API. It can translate a user's query into the local language required for a specific marketplace search.
*   **`WebSearchAgent`:** This agent is the primary tool for researching new products. Equipped with the **built-in Google Search tool**, it scours the web for product listings and specifications.
*   **`ToriSearchAgent`:** This agent is the key to unlocking the local market. It is equipped with a powerful **custom tool**—a web scraper designed specifically for Tori.fi, Finland's premier second-hand marketplace. It finds relevant local listings, a task impossible for generic shopping assistants.
*   **`ReviewAgent`:** To build user trust, this agent is responsible for vetting both products and sellers. It uses a hybrid approach:
    *   For **product quality**, it employs the **Google Search tool** with specialized prompts to find and synthesize review summaries, pros, and cons from articles and forums.
    *   For **vendor trustworthiness**, it uses a **custom tool** that integrates with the **Google Places API** to fetch structured data like star ratings and review counts for specific shops.

This architecture allows for complex, dynamic workflows. For a query like "Find me a good quality used camera from a reputable shop in Helsinki," the `OrchestratorAgent` could run the `ToriSearchAgent` and the `ReviewAgent` in **parallel**, presenting a curated list of options that are both available and well-regarded.

## 4. Key Features in MVP

*   **Conversational Interface:** Natural language interaction via a Telegram bot.
*   **Personalization & Long-Term Memory:** Remembers user details like name, size, and brand preferences across sessions.
*   **Localized Search:** Identifies user's region to tailor searches.
*   **Dual Market Search:** Finds both new items (via Google Search) and used items (via a custom Tori.fi tool).
*   **Review Analysis & Shop Vetting:** Summarizes product pros and cons from web articles and fetches concrete ratings for local shops using the Google Places API.
*   **Comparison Summaries:** Presents structured comparisons of products in easy-to-read markdown tables.

## 5. Future Enhancements (Post-MVP)

*   **Proactive Monitoring Agent:** A long-running agent to track items for price drops, flash sales, or restocks, demonstrating Long-Running Operations (LROs).
*   **Advanced Gift Recommendations:** A specialized agent that reasons about gift ideas based on a recipient's profile and budget.
*   **Style/Mood Board Inspiration:** Allow users to send an image of an outfit to find visually similar items, leveraging multimodal models.