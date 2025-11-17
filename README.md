# BuySpy - Your Personal AI Shopping Concierge 🛍️🤖

<div align="center">
  <img src="res/buyspy_sm.png" alt="BuySpy Logo" width="200">
</div>
# BuySpy - Your Personal AI Shopping Concierge 🛍️🤖

BuySpy is an AI-powered shopping assistant, built as a capstone project. It acts as a personal concierge via a Telegram chat, helping users find, research, and compare products in a personalized and localized way.

This project is built using Google's Agent Development Kit (ADK) and demonstrates a multi-agent system that can search for both new and used items, remember user preferences, analyze reviews, and provide curated recommendations.

## ✨ Features

-   **Conversational Interface:** Chat with BuySpy naturally on Telegram.
-   **Personalization:** Remembers your name, size, and favorite brands.
-   **Localized Search:** Tailors results to your country.
-   **New & Used Items:** Searches Google for new items and local marketplaces (like Tori.fi) for used ones.
-   **Review Vetting:** Summarizes product reviews and checks vendor ratings using the Google Places API to build trust.
-   **Comparison Summaries:** Generates easy-to-read tables comparing product options.

## 🛠️ Tech Stack

-   **Backend:** Python 3.11+, FastAPI
-   **AI/Agent Framework:** Google Agent Development Kit (ADK)
-   **LLM:** Google Gemini (via Vertex AI)
-   **Interface:** `python-telegram-bot` (using polling)
-   **Cloud Services:**
    -   Google Cloud Firestore (for long-term memory)
    -   Google Cloud Translation API
    -   Google Places API
-   **Dependency Management:** uv
-   **Local Testing:** Streamlit Playground

## 🚀 Getting Started

### Prerequisites

-   **uv**: Python package manager - [Install](https://docs.astral.sh/uv/getting-started/installation/)
-   **Google Cloud SDK**: For authenticating to GCP services - [Install](https://cloud.google.com/sdk/docs/install)
-   **make**: Build automation tool (pre-installed on most Unix-based systems)
-   A Telegram Bot Token from BotFather.
-   A Google Cloud Project with billing enabled.

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/<your-username>/buyspy.git
    cd buyspy
    ```

2.  **Authenticate with Google Cloud:**
    Log in with the gcloud CLI and set up Application Default Credentials. This allows the application to securely access Google Cloud APIs.
    ```bash
    gcloud auth login
    gcloud auth application-default login
    ```

3.  **Enable GCP APIs:**
    In your Google Cloud project, make sure you have enabled the following APIs:
    -   Vertex AI API
    -   Cloud Translation API
    -   Places API

4.  **Configure Environment Variables:**
    Create a `.env` file in the root directory by copying the example file:
    ```bash
    cp .env.example .env
    ```
    Now, fill in the values in your `.env` file:
    ```env
    # Google Cloud (for services like Firestore, Translate, Vertex AI)
    GCP_PROJECT_ID="your-gcp-project-id"
    GCP_REGION="your-gcp-region" # e.g., europe-west1

    # Telegram
    TELEGRAM_BOT_TOKEN="your-telegram-bot-token"
    ```

5.  **Install dependencies:**
    This command uses `uv` to install all necessary packages listed in `pyproject.toml`.
    ```bash
    make install
    ```

### Local Development

This project uses two main components for local development: the ADK agent server (tested via a Streamlit playground) and a separate Telegram polling script.

1.  **Run the Agent Playground:**
    In one terminal, launch the Streamlit interface to interact with and test your agent directly. The server will auto-reload on code changes in the `app/` directory.
    ```bash
    make playground
    ```

2.  **Run the Telegram Bot:**
    In a second terminal, run the Telegram polling script. This script will fetch messages from Telegram, send them to your local agent server, and return the agent's response to the user.
    ```bash
    uv run python scripts/run_telegram_bot.py
    ```
    You can now interact with your agent by messaging your bot on Telegram.

## 🐳 Deployment (Local Server with Docker)

The primary deployment target is a local server using Docker.

1.  **Build the Docker Image:**
    ```bash
    docker build -t buyspy-agent .
    ```

2.  **Run with Docker Compose:**
    A `docker-compose.yml` file is provided to run the FastAPI agent server and the Telegram polling script as two separate, connected services.
    ```bash
    docker-compose up
    ```

*(Note: The starter kit also provides extensive tooling for deploying to Google Cloud using Terraform and CI/CD. For more details, refer to the original starter pack documentation.)*