
## Strategy for Point 4: Advanced AI Capabilities

---

### Sub-feature A: Event Clustering

**The Problem:** If 5 sources all cover the same GPT-5 release, you get 5 separate digest items in the email. The upgrade clusters them into **one master summary**.

**Strategy:**

The plan is to add a **Cluster Agent** that runs between `process_digests` (Step 4) and `send_digest_email` (Step 5) in `daily_runner.py`.

```
Scrape → Process Anthropic → Process YouTube → Generate Digests → [NEW] Cluster → Send Email
```

**Technical Approach — Vector Embeddings (better than LLM-only):**

1. **New file: `app/agent/cluster_agent.py`** — Takes all `Digest` dicts, embeds their titles+summaries using OpenAI's `text-embedding-3-small`, computes cosine similarity, and groups items above a similarity threshold (e.g. `0.82`) into clusters. Falls back to simple keyword-based grouping if no API key.
2. **New file: `app/services/process_clustering.py`** — Calls the cluster agent, then for each cluster with 2+ items, calls the `DigestAgent` to synthesize a single **master summary** from the individual summaries. Stores the cluster group in a new `DigestCluster` table.
3. **New DB model: `DigestCluster`** — Stores `cluster_id`, `title`, `master_summary`, `member_ids` (comma-separated digest IDs), and `created_at`.
4. **Update `repository.py`** — Add `create_digest_cluster()` and `get_recent_clusters()` methods.
5. **Update `daily_runner.py`** — Insert a new Step 5 for clustering, push email to Step 6.
6. **Update `email_agent.py`** — When building the email, use cluster master summaries first (marked as "🔗 Trending Event"), then individual unclustered items after.


