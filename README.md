# AI News Aggregator

An automated, AI-powered pipeline designed to scrape, summarize, and deliver the latest AI news and updates directly to your inbox. This system consolidates content from diverse sources (such as YouTube transcripts and AI research blogs), utilizes advanced LLM curation to filter signal from noise, and formats the output into a clean, readable daily digest.

---

## Key Features

- **Multi-Source Scraping:** Automated scrapers for OpenAI/Anthropic blogs and specialized YouTube channels using `youtube-transcript-api` and `beautifulsoup4`.
- **Intelligent Summarization:** Curates and summarizes articles and transcripts utilizing OpenAI's models to extract key takeaways.
- **PostgreSQL Database Integration:** Tracks processed articles and digests using SQLAlchemy to avoid duplicate processing.
- **Daily Email Digests:** Formats digested news into clean HTML/Markdown and delivers them automatically via SMTP.

---

## System Architecture

The pipeline processes data sequentially:

```
Scrape Sources ──> Process Content ──> Generate Digests ──> Event Clustering (New) ──> Send Email
```

---

## Recent Upgrades

### Event Clustering & Master Summaries (Advanced AI Capabilities)
Previously, if multiple sources covered the same trending event (e.g., a major model release), the system generated redundant digest items. 

We have introduced a **Cluster Agent** to group related news into a single, cohesive master summary:

1. **Vector Embeddings Clustering:** In `app/agent/cluster_agent.py`, news titles and summaries are converted to vector representations using OpenAI's `text-embedding-3-small` and grouped using cosine similarity (threshold: `0.82`).
2. **Master Summarization:** For any cluster containing multiple related news items, the `DigestAgent` synthesizes a single unified **Master Summary** to eliminate redundancy.
3. **Database Caching:** A new `DigestCluster` table stores cluster groupings and synthesized master summaries.
4. **Email Integration:** The daily digest email displays clustered events under a "🔗 Trending Event" section before showing individual, unclustered updates.

---

## Project Structure

- `app/` - Core application logic:
  - `agent/` - LLM agents for curation, clustering, and summarization.
  - `services/` - Scrapers, clustering orchestrator, and email builders.
  - `models/` - SQLAlchemy models (e.g., `DigestCluster`, `Article`).
- `main.py` - Single-entry run script for the daily aggregator job.
- `docker/` - Docker deployment configuration files.

---

## Installation & Setup

1. **Clone the Repository:**
   ```bash
   git clone <YOUR_GITHUB_REPO_URL>
   cd ai-news-aggregator-master
   ```

2. **Configure Environment Variables:**
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your-openai-api-key
   DATABASE_URL=postgresql://username:password@localhost:5432/ai_news_db
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   RECEIVER_EMAIL=recipient-email@gmail.com
   ```

3. **Install Dependencies:**
   Using `uv` (recommended):
   ```bash
   uv sync
   ```

4. **Run the Pipeline:**
   ```bash
   python main.py
   ```
