# 🤖 AI News Aggregator

An automated, production-grade AI pipeline designed to scrape, summarize, cluster, and deliver the latest AI news directly to your inbox. 

This system consolidates updates from diverse sources (such as AI research blogs and YouTube transcripts), filters out noise using advanced LLM curation, groups similar stories together using vector embeddings, and delivers a clean HTML digest newsletter via email.

---

## 🌟 Key Features

*   **Multi-Source Scraping:** Automated parsers for OpenAI/Anthropic blogs and curated YouTube channels using `beautifulsoup4` and `youtube-transcript-api`.
*   **Vector Event Clustering:** Groups similar stories covering the same topic (e.g., a major model release) into a single unified event using OpenAI's `text-embedding-3-small` and Cosine Similarity, avoiding newsletter redundancy.
*   **AI Curation & Summarization:** Synthesizes master summaries using OpenAI GPT models, delivering key takeaways with high technical depth.
*   **Robust Database Layer:** Uses SQLAlchemy (supporting PostgreSQL and SQLite) to cache processed articles and digests, preventing duplicate processing.
*   **Flexible Deployments:** Supports running as a simple Python CLI, containerized with Docker Compose, or scheduled daily in a production-ready Kubernetes cluster.

---

## 🛠️ System Architecture

The pipeline runs sequentially:
```
[Scrape Blogs/YouTube] ──> [Process & Extract Text] ──> [Generate AI Digests] ──> [Cluster Events] ──> [SMTP Email Curation]
```

---

## 📁 Repository Structure

```
├── app/                        # Application Codebase
│   ├── agent/                  # OpenAI Prompt Agents (Curation, Digest, Clustering)
│   ├── database/               # SQL Connection, Models, and Repository Queries
│   ├── profiles/               # User interest preferences (for personalized ranking)
│   ├── scrapers/               # Blog and YouTube RSS scrapers
│   └── services/               # Curation pipelines, text parsing, and email services
├── kubernetes/                 # Production Kubernetes Orchestration
│   ├── configmap.yaml          # K8s ConfigMap for non-sensitive variables
│   ├── secrets.yaml            # K8s Secrets for credentials/passwords
│   ├── postgres-deployment.yaml# PostgreSQL Deployment, PVC, and Service
│   ├── cronjob.yaml            # Daily scheduled Scraper Job
│   └── README.md               # K8s execution guide
├── Dockerfile                  # Containerization image build configuration
├── main.py                     # CLI entrypoint for running the pipeline
└── requirements.txt            # System dependency lock list
```

---

## ⚙️ Environment Configuration

Create a `.env` file in the root directory for local runs, or configure these values in Kubernetes (`kubernetes/secrets.yaml` and `kubernetes/configmap.yaml`):

| Variable Name | Description | Example Value |
| :--- | :--- | :--- |
| `OPENAI_API_KEY` | Your OpenAI API key for digests and clustering | `sk-proj-...` |
| `MY_EMAIL` | The Gmail address used to log in and send the email | `sender@gmail.com` |
| `APP_PASSWORD` | A 16-letter Gmail App Password (no spaces) | `vdwlrtbrcsqqenqa` |
| `POSTGRES_USER` | Database username | `postgres` |
| `POSTGRES_PASSWORD`| Database password | `postgres` |
| `POSTGRES_HOST` | Database host address | `localhost` or `postgres-service` |
| `POSTGRES_PORT` | Database port number | `5432` |
| `POSTGRES_DB` | Name of the database | `ai_news_aggregator` |

> [!TIP]
> **Getting a Gmail App Password:**
> 1. Go to your Google Account Settings -> Security.
> 2. Enable **2-Step Verification** (required by Google to use App Passwords).
> 3. Search for **App Passwords** in the search bar.
> 4. Choose a custom name (e.g. "AI News Aggregator") and copy the generated 16-character code. **Remove all spaces** when pasting it into your configuration.

---

## 🚀 How to Run the Project

You can run the aggregator in three different ways:

### Option 1: Run Locally (Python CLI)

Perfect for quick local testing. Uses SQLite by default.

1. **Install dependencies:**
   Ensure you have Python 3.12+ installed. Install the requirements using `pip`:
   ```bash
   pip install -r requirements.txt
   ```
2. **Setup Environment:**
   Create your `.env` file using the configuration reference above.
3. **Execute:**
   ```bash
   python main.py
   ```
   *(Optionally pass a custom lookback window in hours as an argument, e.g. `python main.py 72` to search the last 3 days).*

---

### Option 2: Run with Docker Compose

Runs PostgreSQL in a container while you execute the scraper from your host machine.

1. **Start the database container:**
   ```bash
   docker compose -f docker/docker-compose.yml up -d
   ```
2. **Execute the pipeline:**
   Make sure `POSTGRES_HOST=localhost` and `POSTGRES_PORT=5433` (or the mapped port) are configured in your `.env` file, then run:
   ```bash
   python main.py
   ```

---

### Option 3: Kubernetes Orchestration (Production Ready)

Orchestrates the entire system locally using a single-node cluster (Docker Desktop Kubernetes or Minikube).

1. **Set up Kubernetes:**
   Make sure Kubernetes is enabled in your Docker Desktop Settings (Settings -> Kubernetes -> Enable Kubernetes).
2. **Configure Secrets:**
   Open `kubernetes/secrets.yaml` and paste your actual API keys and plain-text passwords directly under the `stringData:` block.
3. **Build the Container Image:**
   Build the image inside your Docker daemon:
   ```bash
   docker build -t news-aggregator-scraper:v2 .
   ```
4. **Deploy Manifests:**
   Apply the ConfigMaps, Secrets, PostgreSQL Database, and CronJob schedulers:
   ```bash
   kubectl apply -f kubernetes/configmap.yaml
   kubectl apply -f kubernetes/secrets.yaml
   kubectl apply -f kubernetes/postgres-deployment.yaml
   kubectl apply -f kubernetes/cronjob.yaml
   ```
5. **Test Trigger Immediately:**
   Trigger a manual test job and follow the logs to confirm success:
   ```bash
   kubectl create job --from=cronjob/news-aggregator-scraper news-aggregator-run-today
   kubectl logs -f -l job-name=news-aggregator-run-today
   ```
   *(For full Kubernetes setup steps and troubleshooting, see the [Kubernetes Guide](kubernetes/README.md)).*
