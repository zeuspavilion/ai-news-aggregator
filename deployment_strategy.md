# GitHub Actions & Neon/Supabase Deployment Setup

This plan outlines the steps to deploy the daily news aggregator using **GitHub Actions** (as a free daily Cron/orchestrator) and **Neon/Supabase** (as a free PostgreSQL database), avoiding the need for credit cards or paid services.

---

## User Review Required

> [!IMPORTANT]
> - **GitHub Repository Secrets:** You will need to add your `.env` variables (e.g., `DATABASE_URL`, `OPENAI_API_KEY`, `SMTP_USER`, `SMTP_PASSWORD`, and `RECEIVER_EMAIL`) as **GitHub Repository Secrets** so they can be securely injected into the workflow.
> - **Database Provisioning:** You will need to create a free account on [Neon.tech](https://neon.tech) or [Supabase.com](https://supabase.com), spin up a free PostgreSQL database, and copy its connection string for your `DATABASE_URL` secret.

---

## Proposed Changes

### GitHub Actions Workflow

#### [NEW] [daily_aggregator.yml](file:///c:/Users/Ronit/Downloads/ai-news-aggregator/ai-news-aggregator-master/.github/workflows/daily_aggregator.yml)
- Create a GitHub Actions workflow to run the pipeline daily at a scheduled time, with support for manual triggering:
  ```yaml
  name: Daily AI News Aggregator

  on:
    schedule:
      - cron: '0 9 * * *'  # Runs daily at 9:00 AM UTC
    workflow_dispatch:     # Allows manual triggering from the GitHub Actions UI

  jobs:
    run-pipeline:
      runs-on: ubuntu-latest
      steps:
        - name: Checkout repository
          uses: actions/checkout@v4

        - name: Install uv
          uses: astral-sh/setup-uv@v5
          with:
            enable-cache: true

        - name: Setup Python
          uses: actions/setup-python@v5
          with:
            python-version-file: "pyproject.toml"

        - name: Install dependencies
          run: |
            uv pip install --system torch --index-url https://download.pytorch.org/whl/cpu
            uv sync --system

        - name: Run Aggregator Pipeline
          env:
            DATABASE_URL: ${{ secrets.DATABASE_URL }}
            OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
            SMTP_HOST: smtp.gmail.com
            SMTP_PORT: 587
            SMTP_USER: ${{ secrets.SMTP_USER }}
            SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
            RECEIVER_EMAIL: ${{ secrets.RECEIVER_EMAIL }}
          run: python main.py
  ```

---

### Cleanups

#### [DELETE] [render.yaml](file:///c:/Users/Ronit/Downloads/ai-news-aggregator/ai-news-aggregator-master/render.yaml)
- Delete the Render configuration file since we are migrating away from Render.

---

## Verification Plan

### Automated Tests
- None required for this configuration change, but we will test yaml formatting.

### Manual Verification
1. Create the workflow file locally.
2. Commit and push it to your GitHub repository.
3. In your GitHub repository settings, add the required Secrets:
   - `DATABASE_URL`
   - `OPENAI_API_KEY`
   - `SMTP_USER`
   - `SMTP_PASSWORD`
   - `RECEIVER_EMAIL`
4. Go to the **Actions** tab on GitHub, select **Daily AI News Aggregator**, click **Run workflow**, and verify that the scraper runs successfully and sends the daily digest email.
