import logging
import sys
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.agent.cluster_agent import ClusterAgent
from app.agent.digest_agent import DigestAgent, DigestOutput
from app.database.repository import Repository

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def generate_master_summary(member_digests: List[Dict[str, Any]], digest_agent: DigestAgent) -> DigestOutput:
    """
    Consolidates multiple digests into a single master title and summary.
    """
    # Create combined input content for the digest agent
    combined_content = ""
    for idx, d in enumerate(member_digests, 1):
        combined_content += f"Article {idx}:\nTitle: {d.get('title', '')}\nSummary: {d.get('summary', '')}\n\n"
        
    combined_content += (
        "Please analyze the articles above, which cover the same event, "
        "and produce a single, unified master title and summary that "
        "captures all key developments from these multiple sources."
    )
    
    # We call generate_digest on the DigestAgent
    digest_output = digest_agent.generate_digest(
        title="Clustered AI Event Update",
        content=combined_content,
        article_type="clustered news event"
    )
    
    if not digest_output:
        # Local fallback if generation failed completely
        first_title = member_digests[0].get("title", "AI Event Update")
        summaries = " | ".join([d.get("summary", "") for d in member_digests])
        digest_output = DigestOutput(
            title=f"Trending: {first_title}",
            summary=f"Unified update from multiple sources. {summaries[:300]}..."
        )
        
    return digest_output


def process_clustering(hours: int = 24) -> dict:
    cluster_agent = ClusterAgent()
    digest_agent = DigestAgent()
    repo = Repository()
    
    digests = repo.get_recent_digests(hours=hours)
    total_digests = len(digests)
    
    logger.info(f"Retrieved {total_digests} recent digests from the last {hours} hours for clustering")
    if total_digests < 2:
        logger.info("Not enough digests to perform clustering.")
        return {"total_clusters": 0, "clustered_digests": 0}
        
    # Get cluster groupings (lists of digest IDs)
    cluster_groups = cluster_agent.cluster_digests(digests)
    
    clusters_created = 0
    clustered_digests_count = 0
    
    for group in cluster_groups:
        if len(group) < 2:
            continue
            
        # We have a cluster! Let's get the digest objects
        member_digests = [d for d in digests if d["id"] in group]
        member_ids = sorted([d["id"] for d in member_digests])
        
        # Generate idempotent cluster ID based on the sorted member IDs
        member_ids_str = "".join(member_ids)
        cluster_hash = hashlib.md5(member_ids_str.encode()).hexdigest()
        cluster_id = f"cluster:{cluster_hash}"
        
        logger.info(f"Creating/updating cluster {cluster_id} with {len(member_digests)} members: {[d['title'] for d in member_digests]}")
        
        try:
            # Generate the consolidated master summary and title
            master_digest = generate_master_summary(member_digests, digest_agent)
            
            # Save the cluster to database
            repo.create_digest_cluster(
                id=cluster_id,
                title=master_digest.title,
                master_summary=master_digest.summary,
                member_ids=member_ids,
                created_at=member_digests[0].get("created_at") # align with the newest member
            )
            
            clusters_created += 1
            clustered_digests_count += len(member_digests)
        except Exception as e:
            logger.error(f"Error processing cluster {cluster_id}: {e}")
            
    logger.info(f"Clustering complete: Created {clusters_created} clusters covering {clustered_digests_count} out of {total_digests} digests.")
    return {
        "total_clusters": clusters_created,
        "clustered_digests": clustered_digests_count
    }


if __name__ == "__main__":
    result = process_clustering(hours=24)
    print(f"Clusters created/updated: {result['total_clusters']}")
    print(f"Digests clustered: {result['clustered_digests']}")
