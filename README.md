# BuySpy - Your Personal AI Shopping Concierge 🛍️🤖

BuySpy is an AI-powered shopping assistant, built as a capstone project. It acts as a personal concierge via a Telegram chat, helping users find, research, and compare products in a personalized and localized way.

This project demonstrates a multi-agent system using Google's Agent Development Kit (ADK) and Google Cloud services. The agent can search for both new and used items, remember user preferences, and provide curated recommendations.

## ✨ Features

-   **Conversational Interface:** Chat with BuySpy naturally on Telegram.
-   **Personalization:** Remembers your name, size, and favorite brands.
-   **Localized Search:** Tailors results to your country.
-   **New & Used Items:** Searches Google for new items and local marketplaces (like Tori.fi) for used ones.
-   **Comparison Summaries:** Generates easy-to-read tables comparing product options.

## 🛠️ Tech Stack

-   **Backend:** Python 3.11+, FastAPI
-   **AI/Agent Framework:** Google Agent Development Kit (ADK)
-   **LLM:** Google Gemini (via Vertex AI)
-   **Cloud Services:**
    -   Google Cloud Run (for deployment)
    -   Google Cloud Firestore (for long-term memory)
    -   Google Cloud Translation API
-   **Interface:** Telegram Bot API
-   **Dependency Management:** uv

## 🚀 Getting Started

### Prerequisites

-   Python 3.11+ and Poetry
-   A Google Cloud Platform (GCP) project with billing enabled.
-   A Telegram Bot Token from BotFather.
-   `gcloud` CLI installed and authenticated.

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/40min/buyspy.git
    cd buyspy
    ```

2.  **Install dependencies:**
    ```bash
    make install
    ```

3.  **Configure Environment Variables:**
    Create a `.env` file in the root directory by copying the example file:
    ```bash
    cp .env.example .env
    ```
    Now, fill in the values in your `.env` file:
    ```env
    # Google Cloud
    GCP_PROJECT_ID="your-gcp-project-id"
    GCP_REGION="your-gcp-region" # e.g., europe-west1

    # Telegram
    TELEGRAM_BOT_TOKEN="your-telegram-bot-token"

    # ADK & Gemini
    # Ensure your GCP account has access to Vertex AI
    ```

4.  **Run the application locally:**
    todo: add

5.  **Connect Telegram Bot (for local development):**
    todo: rewrite with using pulling

### Deployment

    todo: write it