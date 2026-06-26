# Render Deployment Setup & OOP Refactoring

This plan outlines the changes required to refactor the scraping architecture using Object-Oriented Programming (OOP) design patterns, make the pipeline fully production-ready, and configure a seamless deployment to Render using Render Blueprints.

---

## User Review Required

> [!IMPORTANT]
> - **PyTorch CPU-only Optimization:** To prevent Render builds from timing out and exceeding free tier resource limits, the `requirements.txt` build command will download the CPU-only version of PyTorch (`torch --index-url https://download.pytorch.org/whl/cpu`).
> - **Environment Variables:** The Render Cron Job service will require your secrets (such as `OPENAI_API_KEY`, `SMTP_USER`, `SMTP_PASSWORD`, and `RECEIVER_EMAIL`) to be configured in the Render Dashboard or during Blueprint deployment.

---

## Proposed Changes

### Scraping Architecture (OOP Design Patterns)

We will introduce a `BaseScraper` abstract class to implement the Strategy Pattern for news scrapers, decoupling the execution runner from specific scraper implementations.

#### [NEW] [base.py](file:///c:/Users/Ronit/Downloads/ai-news-aggregator/ai-news-aggregator-master/app/scrapers/base.py)
- Create an abstract base class `BaseScraper` defining the common scraper contract:
  ```python
  from abc import ABC, abstractmethod
  from typing import List, Any

  class BaseScraper(ABC):
      @abstractmethod
      def get_articles(self, hours: int = 24) -> List[Any]:
          """Scrape and return articles published within the last 'hours'."""
          pass
  ```

#### [MODIFY] [youtube.py](file:///c:/Users/Ronit/Downloads/ai-news-aggregator/ai-news-aggregator-master/app/scrapers/youtube.py)
- Make `YouTubeScraper` inherit from `BaseScraper`.
- Add `channel_id` to the `ChannelVideo` Pydantic model so that each scraped video carries its channel identifier.
- Implement the `get_articles(self, hours: int = 24)` method, which aggregates videos across all channels configured in `YOUTUBE_CHANNELS`.

#### [MODIFY] [openai.py](file:///c:/Users/Ronit/Downloads/ai-news-aggregator/ai-news-aggregator-master/app/scrapers/openai.py)
- Make `OpenAIScraper` inherit from `BaseScraper`.
- Ensure it implements the abstract `get_articles(hours)` method.

#### [MODIFY] [anthropic.py](file:///c:/Users/Ronit/Downloads/ai-news-aggregator/ai-news-aggregator-master/app/scrapers/anthropic.py)
- Make `AnthropicScraper` inherit from `BaseScraper`.
- Ensure it implements the abstract `get_articles(hours)` method.

#### [MODIFY] [runner.py](file:///c:/Users/Ronit/Downloads/ai-news-aggregator/ai-news-aggregator-master/app/runner.py)
- Refactor `run_scrapers` to use polymorphism by instantiating and calling `get_articles(hours)` on each scraper, simplifying code readability and extensibility.

---

### Production Readiness & DB Initializer

#### [MODIFY] [daily_runner.py](file:///c:/Users/Ronit/Downloads/ai-news-aggregator/ai-news-aggregator-master/app/daily_runner.py)
- Import `engine` and `Base` from `app.database.connection` and `app.database.models`.
- Add a safety check at the very beginning of the pipeline run to automatically execute database schema migrations:
  ```python
  from app.database.models import Base
  from app.database.connection import engine
  ...
  # At the start of run_daily_pipeline:
  Base.metadata.create_all(engine)
  ```
  This guarantees that table schemas (including the recent `DigestCluster` tables) are created automatically on database connection start, avoiding manual configuration steps on Render.

---

### Render Infrastructure Config (Infrastructure-as-Code)

#### [NEW] [render.yaml](file:///c:/Users/Ronit/Downloads/ai-news-aggregator/ai-news-aggregator-master/render.yaml)
- Create a Render Blueprint definition containing:
  1. A **PostgreSQL database instance** (`ai-news-aggregator-db`).
  2. A **Cron Job service** (`ai-news-aggregator-job`) set to run `main.py` daily.
  3. Connection mapping linking the database URL environment variable (`DATABASE_URL`) to the Cron Job automatically.
  4. Placeholders for all required configurations (`OPENAI_API_KEY`, SMTP details, receiver emails).

#### [NEW] [requirements.txt](file:///c:/Users/Ronit/Downloads/ai-news-aggregator/ai-news-aggregator-master/requirements.txt)
- Export and compile project dependencies from `pyproject.toml` into a standard format.
- Set a custom build prefix to pull CPU-only versions of PyTorch to ensure builds remain clean and stay within resource limits.

---

## Verification Plan

### Automated Tests
- Run `uv run python -m unittest` or check execution of individual modules to verify imports and base class functionality:
  ```powershell
  python -m app.scrapers.youtube
  python -m app.scrapers.openai
  python -m app.scrapers.anthropic
  python -m app.runner
  ```

### Manual Verification
1. Run `python main.py` locally to verify that:
   - Database tables are initialized dynamically.
   - Scraping, clustering, and email sending work correctly.
2. Deploy the blueprint configuration on Render and confirm:
   - The PostgreSQL instance spins up and initializes properly.
   - The Cron Job environment builds successfully and triggers a test execution.
