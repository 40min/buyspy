# BuySpy - Your Personal AI Shopping Concierge 🛍️🤖

<div align="center">
  <img src="res/buyspy_sm.png" alt="BuySpy Logo" width="200">
</div>
# BuySpy - Your Personal AI Shopping Concierge 🛍️🤖

BuySpy is an AI-powered shopping assistant, built as a capstone project. It acts as a personal concierge via a Telegram chat, helping users find, research, and compare products in a personalized and localized way.

This project is built using Google's Agent Development Kit (ADK) and demonstrates a multi-agent system that can search for both new and used items, remember user preferences, analyze reviews, and provide curated recommendations.

## ✨ Features

-   **Conversational Interface:** Chat with BuySpy naturally on Telegram.
-   **Multi-Agent Architecture:** Specialized agents for research, shopping, price extraction, and general conversation.
-   **Intelligent Intent Detection:** Automatically routes queries to appropriate agents (shopping vs. general knowledge).
-   **Personalization & Memory:** Remembers user preferences and conversation context across sessions using ADK's built-in memory system.
-   **Localized Search:** Tailors product search results to your country.
-   **Enterprise Web Scraping:** Uses BrightData's Streamable HTTP MCP service for reliable SERP search and web crawling.
-   **Parallel Price Extraction:** Efficiently scrapes multiple stores simultaneously for best prices.
-   **Smart Aggregator Handling:** Detects price comparison sites and automatically navigates to actual shop pages.
-   **Comparison Summaries:** Generates easy-to-read markdown tables comparing product options with pricing and availability.

## 🛠️ Tech Stack

-   **Backend:** Python 3.11+
-   **AI/Agent Framework:** Google Agent Development Kit (ADK)
-   **LLM:** Google Gemini 2.5 Flash (via Vertex AI)
-   **Interface:** `python-telegram-bot` (using polling)
-   **Web Scraping:** BrightData Streamable HTTP MCP Service (enterprise SERP & web crawling)
-   **Memory:** ADK built-in memory system with auto-save
-   **Cloud Services:**
    -   Google Cloud Vertex AI (LLM)
    -   Google Cloud Trace & Logging (observability)
    -   BigQuery (event storage & analytics)
-   **Dependency Management:** uv
-   **Local Testing:** Streamlit Playground
-   **Infrastructure:** Terraform (for Google Cloud deployment)

## 📁 Project Structure

```
buyspy/
├── app/                 # Core application code
│   ├── agent.py         # Main app instance
│   ├── agent_engine_app.py # Agent Engine application logic
│   ├── config.py        # Configuration management
│   ├── dependencies.py  # Dependency injection
│   ├── subagents/       # Specialized agent implementations
│   │   ├── orchestrator/    # Root agent coordinating all subagents
│   │   ├── research/        # Product research agent (Google Search)
│   │   ├── shopping/        # Shopping agent (BrightData Streamable HTTP MCP)
│   │   ├── price_extractor/ # Price extraction agent (web scraping)
│   │   └── smalltalk/       # General conversation agent
│   ├── tools/           # Custom tools and MCP integrations
│   │   └── search_tools_bd.py # BrightData Streamable HTTP MCP toolset
│   ├── services/        # Service layer (Telegram, etc.)
│   └── app_utils/       # Utilities and helpers
├── .github/             # CI/CD pipeline configurations
├── deployment/          # Infrastructure and deployment scripts
├── notebooks/           # Jupyter notebooks for prototyping
├── tests/               # Unit, integration, and load tests
├── telegram_bot.py      # Telegram bot entrypoint
├── Makefile             # Common commands
└── pyproject.toml       # Project dependencies and configuration
```

## 🚀 Getting Started

### Prerequisites

-   **uv**: Python package manager - [Install](https://docs.astral.sh/uv/getting-started/installation/)
-   **Google Cloud SDK**: For authenticating to GCP services - [Install](https://cloud.google.com/sdk/docs/install)
-   **make**: Build automation tool (pre-installed on most Unix-based systems)
-   **Terraform**: For infrastructure deployment - [Install](https://developer.hashicorp.com/terraform/downloads)
-   **Docker & Docker Compose** (optional, for containerized deployment): [Install Docker](https://docs.docker.com/get-docker/)
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
    -   Cloud Trace API
    -   Cloud Logging API
    -   BigQuery API (for event storage)

4.  **Configure Environment Variables:**
    Create a `.env` file in the root directory by copying the example file:
    ```bash
    cp .env.example .env
    ```
    Now, fill in the values in your `.env` file:
    ```env
    # Google Cloud (for Vertex AI, Trace, Logging)
    GCP_PROJECT_ID="your-gcp-project-id"
    GCP_REGION="your-gcp-region" # e.g., europe-west1

    # Telegram
    TELEGRAM_BOT_TOKEN="your-telegram-bot-token"

    # BrightData (for web scraping)
    BRIGHTDATA_API_TOKEN="your-brightdata-api-token"
    BRIGHTDATA_API_TIMEOUT=300
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

## ⚙️ Available Commands

| Command              | Description                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `make install`       | Install all required dependencies using uv                                                  |
| `make playground`    | Launch Streamlit interface for testing agent locally and remotely |
| `make deploy`        | Deploy agent to Agent Engine |
| `make register-gemini-enterprise` | Register deployed agent to Gemini Enterprise |
| `make test`          | Run unit and integration tests                                                              |
| `make lint`          | Run code quality checks (codespell, ruff, mypy)                                             |
| `make setup-dev-env` | Set up development environment resources using Terraform                         |
| `docker-compose up --build` | Build and run the bot in Docker containers |
| `docker-compose down` | Stop the Docker containers |

For full command options and usage, refer to the [Makefile](Makefile).

## 🧪 Testing

### Overview
This project includes a comprehensive testing setup with unit tests, integration tests, and automated code quality checks to ensure code reliability, maintainability, and adherence to best practices.

### Running Tests
Run tests using the following commands:

- **All tests:** `make test`
- **Unit tests only:** `uv run pytest tests/unit/ -v`
- **Integration tests only:** `uv run pytest tests/integration/ -v`
- **Specific test files:** `uv run pytest tests/unit/test_config.py -v`

### Code Quality
Ensure code quality with automated linting and type checking:

- **All linters:** `make lint`
- **Ruff (linting and formatting):** `uv run ruff check .`
- **MyPy (type checking):** `uv run mypy .`
- **Codespell (spell checking):** `uv run codespell`

### Pre-commit Hooks
Pre-commit hooks are configured to automatically run code quality checks before each commit:

- **Installed hooks:** ruff, mypy, codespell, pytest
- **Install hooks:** `uv run pre-commit install`
- **Run hooks manually:** `uv run pre-commit run --all-files`
- **Skip hooks (emergencies only):** `git commit --no-verify`

### Test Coverage
The test suite covers key components:

- **Config module:** Settings validation and environment variable handling
- **Dependencies module:** Dependency injection and service initialization
- **Telegram service:** Message handling, error handling, and API interactions
- **Integration tests:** End-to-end flows including agent communication and external API calls

## 📊 Test Status

*Test status badges will be added here once CI/CD integration is complete.*

## 🏗️ Architecture

BuySpy uses a **multi-agent architecture** where specialized agents handle different aspects of the shopping experience:

### Agent Hierarchy

```
┌─────────────────────────────────────────┐
│         root_agent (Orchestrator)       │
│  - Intent detection                     │
│  - Country detection                    │
│  - Response formatting                  │
│  - Memory management                    │
└─────────────────┬───────────────────────┘
                  │
        ┌─────────┴─────────┬──────────────┬──────────────┐
        │                   │              │              │
┌───────▼────────┐  ┌──────▼──────┐ ┌────▼─────┐ ┌─────▼──────┐
│ smalltalk_agent│  │research_agent│ │shopping_ │ │            │
│                │  │              │ │  agent   │ │            │
│ General chat & │  │ Product      │ │          │ │            │
│ knowledge      │  │ research via │ │ Price    │ │            │
│ (Google Search)│  │ Google Search│ │ finding  │ │            │
└────────────────┘  └──────────────┘ │(BrightData│ │            │
                                     │   MCP)   │ │            │
                                     └────┬─────┘ │            │
                                          │       │            │
                                   ┌──────▼───────▼──────┐     │
                                   │ price_extractor_agent│     │
                                   │                      │     │
                                   │ Web scraping &       │     │
                                   │ price extraction     │     │
                                   │(BrightData HTTP MCP) │     │
                                   └──────────────────────┘     │
```

### Key Features

-   **Intent Detection:** Orchestrator automatically routes queries to appropriate agents
-   **Parallel Execution:** Shopping agent calls multiple price extractors simultaneously
-   **Smart Scraping:** Price extractor detects aggregator sites and navigates to actual shops
-   **Memory System:** ADK's built-in memory with auto-save after each turn
-   **Error Resilience:** Retry logic and graceful degradation when tools fail

## 🔄 Development Process

This project follows a structured development approach:

1. **Prototype:** Build and test agents using the intro notebooks in `notebooks/` for guidance.
2. **Integrate:** Customize agent logic in `app/subagents/` to implement new features.
3. **Test:** Use the Streamlit playground with `make playground` for rapid iteration. The playground auto-reloads on code changes.
4. **Deploy:** Set up CI/CD pipelines with `make setup-dev-env` or `uvx agent-starter-pack setup-cicd`.
5. **Monitor:** Track performance using Cloud Logging, Tracing, and the Looker Studio dashboard.

## 🚀 Deployment Options

### Docker Deployment (Local)

The application can be easily deployed locally using Docker and Docker Compose.

#### Prerequisites for Docker Deployment

- **Docker & Docker Compose**: [Install Docker](https://docs.docker.com/get-docker/)
- **Environment Configuration**: Create your `.env` file as described in the Installation section

#### Quick Start with Docker

1. **Clone and setup the project:**
    ```bash
    git clone https://github.com/<your-username>/buyspy.git
    cd buyspy
    cp .env.example .env
    # Edit .env with your configuration
    ```

2. **Build and run with Docker Compose:**
    ```bash
    docker-compose up --build
    ```

The bot will start automatically and begin polling for Telegram messages.

#### Docker Commands

| Command | Description |
|---------|-------------|
| `docker-compose up --build` | Build and start the bot |
| `docker-compose up -d` | Run in background |
| `docker-compose down` | Stop the bot |
| `docker-compose logs -f buyspy-bot` | View logs |
| `docker-compose restart buyspy-bot` | Restart the bot |

### Google Cloud Deployment

For streamlined deployment to Google Cloud Platform:

#### One-Command Deployment
For a streamlined one-command deployment of the entire CI/CD pipeline and infrastructure using Terraform:
```bash
uvx agent-starter-pack setup-cicd
```
Currently supports GitHub with both Google Cloud Build and GitHub Actions as CI/CD runners.

#### Manual Deployment

**Dev Environment:**
```bash
gcloud config set project <your-dev-project-id>
make deploy
```

**Production Deployment:**
The repository includes a comprehensive Terraform configuration for production deployment. See [deployment/README.md](deployment/README.md) for detailed instructions on how to deploy the infrastructure and application.

## 📊 Monitoring and Observability

The application uses OpenTelemetry for comprehensive observability with all events being sent to:
- **Google Cloud Trace and Logging** for real-time monitoring
- **BigQuery** for long-term storage and analysis

You can use [this Looker Studio dashboard](https://lookerstudio.google.com/reporting/46b35167-b38b-4e44-bd37-701ef4307418/page/tEnnC) template for visualizing events being logged in BigQuery. See the "Setup Instructions" tab to get started.
