# AI Reviews Summarizer for Noon App

An autonomous LangChain-powered AI agent designed to ingest public Google Play Store reviews for the Noon Buyer App, cluster them into actionable themes using Gemini, generate a concise weekly pulse document, and deliver it automatically via Google Docs and Gmail (through MCP).

## 🌟 Features

- **Automated Ingestion**: Scrapes the last 10 weeks of public reviews from the Google Play Store (`com.noon.buyerapp`).
- **Data Privacy (PII Stripping)**: Two-layer PII removal (Regex + LLM) ensures no emails, phone numbers, or usernames are leaked.
- **LLM Theme Clustering**: Uses `gemini-3.6-flash` to intelligently cluster hundreds of reviews into the top 3 core themes, backed by verbatim user quotes.
- **Actionable Insights**: Automatically proposes 3 concrete action items based on the week's top complaints/praise.
- **MCP Delivery Integration**: Bypasses raw Google API complexity by talking to an external Model Context Protocol (MCP) server over SSE to append to Google Docs and create Gmail drafts.
- **CI/CD Scheduling**: Fully automated via GitHub Actions to run every Sunday at 10 PM UAE time.

## 🏗️ Architecture

The pipeline is orchestrated by a **LangChain ReAct Agent** that sequentially triggers custom tools:
1. `fetch_reviews`
2. `process_reviews`
3. `cluster_themes`
4. `generate_pulse`
5. `publish_and_draft_pulse`

For a deeper dive into the system design, check out [architecture.md](architecture.md).

## 🚀 Setup & Installation

### 1. Prerequisites
- Python 3.11+ (Recommended 3.12)
- Gemini API Key
- Access to the deployed Google Workspace MCP Server.

### 2. Clone the Repository
```bash
git clone https://github.com/vishalpurswaniiift1719-png/AI-reviews-summarizer.git
cd AI-reviews-summarizer
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configuration
Copy the `.env.example` to `.env` and fill in your production values:
```bash
cp .env.example .env
```
Key variables needed:
- `GEMINI_API_KEY`: Your Google Gemini API Key.
- `TARGET_GOOGLE_DOC_ID`: The ID of the Google Doc to append pulses to.
- `EMAIL_RECIPIENT`: The email address where the Gmail Draft will be sent.
- `MCP_SERVER_SSE_URL`: The deployed Railway MCP Server SSE endpoint.

*Note: The `.gitignore` file ensures your local `.env` and `data/` directories are never committed.*

## 💻 Usage

To run the agent manually on your local machine:
```bash
python src/main.py
```

The agent will execute the pipeline, logging its thought process in the terminal and pushing the final output to Google Docs and Gmail.

## ⚙️ GitHub Actions Automation

This project is configured to run automatically every **Sunday at 10:00 PM (UAE Time)**. 

To enable this, you must configure the following **Repository Secrets** in GitHub (`Settings` > `Secrets and variables` > `Actions`):
- `GEMINI_API_KEY`
- `MCP_SERVER_SSE_URL`
- `TARGET_GOOGLE_DOC_ID`
- `EMAIL_RECIPIENT`

The workflow file can be found at `.github/workflows/weekly_pulse.yml`. You can also trigger the workflow manually from the GitHub Actions tab.

## 🔒 Data Security
- **No data is stored in this repository**. All `data/raw/` and `data/processed/` files generated during runtime are strictly `.gitignore`'d.
- The MCP server manages all OAuth tokens in memory—no tokens are exposed to the AI agent.
