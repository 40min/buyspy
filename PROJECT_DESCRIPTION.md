# Project Description: BuySpy - Your Personal & Localized AI Shopping Concierge

## 1. Problem Statement

Online shopping is overwhelming and impersonal. Consumers spend hours sifting through countless product pages, trying to decipher fake reviews, and comparing specifications, leading to decision fatigue and wasted time. Furthermore, existing shopping assistants are generic and disconnected from the user's local context. They fail to understand personal preferences, cannot search popular local marketplaces for second-hand goods, and offer a one-size-fits-all experience that ignores regional nuances. This results in irrelevant recommendations and a frustrating, disjointed process.

## 2. Proposed Solution

I will be building **BuySpy**, an AI-powered shopping concierge agent that delivers a deeply personalized and localized shopping experience. BuySpy acts as your personal shopper via a simple chat interface (Telegram), doing the heavy lifting of product research, review analysis, and price comparison.

It not only learns and remembers your style and preferences but also leverages a team of specialized agents to search both global e-commerce sites and local marketplaces like Finland's Tori.fi, providing a truly comprehensive and relevant set of options. BuySpy transforms online shopping from a stressful task into a seamless and personalized conversation.

## 3. Core Functionality

BuySpy is architected as a modular, multi-agent system where a central orchestrator delegates tasks to a team of specialized agents. This design allows for clear separation of concerns and showcases advanced agentic patterns.

The system is orchestrated by the **`OrchestratorAgent`**, the primary user-facing component. It manages the conversational flow, understands user intent, and maintains both short-term session state and **long-term memory** of user preferences (e.g., name, clothing size, favorite brands) via a custom **Memory Bank** tool connected to a Google Cloud Firestore database.

When a user makes a request, the `OrchestratorAgent` devises a plan and invokes one or more specialist agents:

*   **`LocationAgent`:** To provide localized results, this agent's sole purpose is to determine the user's shopping region, ensuring subsequent searches are relevant.
*   **`TranslationAgent`:** To break down language barriers, this agent uses a **custom tool** wrapping the Google Cloud Translation API. It can translate a user's query into the local language required for a specific marketplace search.
*   **`WebSearchAgent`:** This agent is the primary tool for researching new products. Equipped with the **built-in Google Search tool**, it scours the web for product listings, specifications, and reviews. It uses the LLM's powerful synthesis capabilities to extract key pros and cons from search results.
*   **`ToriSearchAgent`:** This agent is the key to unlocking the local market. It is equipped with a powerful **custom tool**—a web scraper designed specifically for Tori.fi, Finland's premier second-hand marketplace. It finds relevant local listings, a task impossible for generic shopping assistants.

This architecture allows for complex, dynamic workflows. For a query like "Find me a new or used Fjällräven Kånken backpack in Finland," the `OrchestratorAgent` could run the `WebSearchAgent` and the `ToriSearchAgent` in **parallel**, gathering both new and second-hand options simultaneously before presenting a unified, curated list to the user.

## 4. Key Features in MVP

*   **Conversational Interface:** Natural language interaction via a Telegram bot.
*   **Personalization & Long-Term Memory:** Remembers user details like name, size, and brand preferences across sessions.
*   **Localized Search:** Identifies user's region to tailor searches.
*   **Dual Market Search:** Finds both new items (via Google Search) and used items (via a custom Tori.fi tool).
*   **Comparison Summaries:** Presents structured comparisons of products in easy-to-read markdown tables.

## 5. Future Enhancements (Post-MVP)

*   **Proactive Monitoring Agent:** A long-running agent to track items for price drops, flash sales, or restocks, demonstrating Long-Running Operations (LROs).
*   **Advanced Gift Recommendations:** A specialized agent that reasons about gift ideas based on a recipient's profile and budget.
*   **Style/Mood Board Inspiration:** Allow users to send an image of an outfit to find visually similar items, leveraging multimodal models.