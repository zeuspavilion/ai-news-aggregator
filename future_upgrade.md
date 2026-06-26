# AI News Aggregator - Future Upgrades Required

While the current pipeline is a solid foundation, here are several key upgrades to take this project to the next level:

## 1. Source Expansion & Generic RSS
Currently, the sources are hardcoded to specific YouTube channels and specific blogs (OpenAI/Anthropic). 
* **Upgrade:** Integrate a generic RSS Feed parser to allow the user to easily add sources like HackerNews, TechCrunch, Arxiv AI papers, and Reddit (e.g., `r/LocalLLaMA`). Adding Twitter/X API integration for trending AI tweets would also significantly increase the signal.

## 2. Web Frontend / User Interface
Relying solely on email is great for passive consumption but limits the utility of your database.
* **Upgrade:** Build a web frontend (e.g., Next.js, Streamlit, or FastAPI with a React frontend). This would allow users to log in, search through historical AI news, bookmark favorite digests, and read full summaries on a web dashboard rather than losing them in their inbox.

## 3. Multi-User Personalization
The pipeline is currently designed as a single-tenant application (one user, one set of news).
* **Upgrade:** Update the database schema to handle multiple users. Allow users to set their own "Preferences" or "Keywords" (e.g., User A only cares about *Open Source LLMs*, User B cares about *AI Image Generation*). The Curator Agent could then filter and rank the news based on individual user profiles.

## 4. Advanced AI Capabilities (Clustering & Audio)
* **Event Clustering:** If OpenAI, Anthropic, and 3 YouTube videos all talk about the *same* new model release, you currently get 5 separate digest items. Use an LLM or vector embeddings to "cluster" similar news items together into one cohesive master summary to prevent redundancy.
* **Podcast Generation:** Integrate text-to-speech (like ElevenLabs or OpenAI TTS) to convert the daily digest into a 5-minute audio podcast that the user can listen to on their commute.

## 5. Pipeline Orchestration & Robustness
* **Orchestration:** Moving from a simple Python `main.py` script to a proper data orchestration tool like **Apache Airflow**, **Prefect**, or **Dagster**. This provides better logging, automatic retries if a scraper fails, and dependency management.
* **Scraper Resilience:** Add proxy rotation and backoff/retry logic (e.g., `tenacity` library) to the scrapers to avoid being IP-blocked or rate-limited by sources like YouTube or Cloudflare-protected blogs.
