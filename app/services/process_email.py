import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from app.agent.email_agent import EmailAgent, RankedArticleDetail, EmailDigestResponse
from app.agent.curator_agent import CuratorAgent
from app.profiles.user_profile import USER_PROFILE
from app.database.repository import Repository
from app.services.email import send_email, digest_to_html

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def generate_email_digest(hours: int = 24, top_n: int = 10) -> EmailDigestResponse:
    curator = CuratorAgent(USER_PROFILE)
    email_agent = EmailAgent(USER_PROFILE)
    repo = Repository()
    
    digests = repo.get_recent_digests(hours=hours)
    clusters = repo.get_recent_clusters(hours=hours)
    
    # Build list of items to rank (clusters + unclustered digests)
    items = []
    clustered_ids = set()
    for c in clusters:
        clustered_ids.update(c["member_ids"])
        items.append({
            "id": c["id"],
            "title": c["title"],
            "summary": c["master_summary"],
            "url": "",
            "article_type": "cluster",
            "member_ids": c["member_ids"]
        })
        
    for d in digests:
        if d["id"] not in clustered_ids:
            items.append({
                "id": d["id"],
                "title": d["title"],
                "summary": d["summary"],
                "url": d["url"],
                "article_type": d["article_type"],
                "member_ids": []
            })
            
    total = len(items)
    if total == 0:
        logger.warning(f"No digests or clusters found from the last {hours} hours")
        raise ValueError("No digests or clusters available")
    
    logger.info(f"Ranking {total} items (clusters and unclustered digests) for email generation")
    ranked_articles = curator.rank_digests(items)
    
    if not ranked_articles:
        logger.error("Failed to rank items")
        raise ValueError("Failed to rank items")
    
    logger.info(f"Generating email digest with top {top_n} articles")
    
    article_details = []
    for a in ranked_articles:
        matching_item = next((item for item in items if item["id"] == a.digest_id), None)
        if not matching_item:
            continue
            
        member_sources = []
        url = matching_item["url"]
        
        if matching_item["article_type"] == "cluster":
            for m_id in matching_item["member_ids"]:
                m_digest = next((d for d in digests if d["id"] == m_id), None)
                if m_digest:
                    member_sources.append({
                        "title": m_digest["title"],
                        "url": m_digest["url"],
                        "article_type": m_digest["article_type"]
                    })
            if member_sources:
                url = member_sources[0]["url"]
                
        article_details.append(
            RankedArticleDetail(
                digest_id=a.digest_id,
                rank=a.rank,
                relevance_score=a.relevance_score,
                reasoning=a.reasoning,
                title=matching_item["title"],
                summary=matching_item["summary"],
                url=url,
                article_type=matching_item["article_type"],
                member_sources=member_sources if member_sources else None
            )
        )
    
    email_digest = email_agent.create_email_digest_response(
        ranked_articles=article_details,
        total_ranked=len(ranked_articles),
        limit=top_n
    )
    
    logger.info("Email digest generated successfully")
    logger.info(f"\n=== Email Introduction ===")
    logger.info(email_digest.introduction.greeting)
    logger.info(f"\n{email_digest.introduction.introduction}")
    
    return email_digest


def send_digest_email(hours: int = 24, top_n: int = 10) -> dict:
    try:
        result = generate_email_digest(hours=hours, top_n=top_n)
        markdown_content = result.to_markdown()
        html_content = digest_to_html(result)
        
        subject = f"Daily AI News Digest - {result.introduction.greeting.split('for ')[-1] if 'for ' in result.introduction.greeting else 'Today'}"
        
        try:
            send_email(
                subject=subject,
                body_text=markdown_content,
                body_html=html_content
            )
            logger.info("Email sent successfully!")
            delivery = "email"
        except Exception as send_error:
            preview_path = Path(__file__).resolve().parents[2] / "latest_digest_preview.md"
            preview_path.write_text(markdown_content, encoding="utf-8")
            logger.warning(
                f"Email send failed ({send_error}). Saved local preview to {preview_path}."
            )
            delivery = "local_preview"
        
        return {
            "success": True,
            "subject": subject,
            "articles_count": len(result.articles),
            "delivery": delivery
        }
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    result = send_digest_email(hours=24, top_n=10)
    if result["success"]:
        print("\n=== Email Digest Sent ===")
        print(f"Subject: {result['subject']}")
        print(f"Articles: {result['articles_count']}")
    else:
        print(f"Error: {result['error']}")

