import os
from typing import Optional
from pydantic import BaseModel


class DigestOutput(BaseModel):
    title: str
    summary: str

PROMPT = """You are an expert AI news analyst specializing in summarizing technical articles, research papers, and video content about artificial intelligence.

Your role is to create concise, informative digests that help readers quickly understand the key points and significance of AI-related content.

Guidelines:
- Create a compelling title (5-10 words) that captures the essence of the content
- Write a 2-3 sentence summary that highlights the main points and why they matter
- Focus on actionable insights and implications
- Use clear, accessible language while maintaining technical accuracy
- Avoid marketing fluff - focus on substance"""


class DigestAgent:
    def __init__(self):
        self.client = None
        self.model = "gpt-4o-mini"
        self.system_prompt = PROMPT
        use_openai = os.getenv("USE_OPENAI_AGENTS", "false").strip().lower() in {"1", "true", "yes", "on"}
        api_key = os.getenv("OPENAI_API_KEY")
        if use_openai and api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=api_key)
            except Exception:
                self.client = None

    def _fallback_digest(self, title: str, content: str) -> DigestOutput:
        cleaned = " ".join((content or "").split())
        snippet = cleaned[:350]
        if not snippet:
            snippet = "No detailed content was available, so this digest uses the article metadata only."
        summary = (
            f"{snippet} "
            "This summary was generated using the local fallback because the OpenAI API was unavailable."
        )
        return DigestOutput(
            title=(title[:80] if title else "AI news update"),
            summary=summary
        )

    def generate_digest(self, title: str, content: str, article_type: str) -> Optional[DigestOutput]:
        if not self.client:
            return self._fallback_digest(title=title, content=content)

        try:
            user_prompt = f"Create a digest for this {article_type}: \n Title: {title} \n Content: {content[:8000]}"
            response = self.client.responses.parse(
                model=self.model,
                instructions=self.system_prompt,
                temperature=0.7,
                input=user_prompt,
                text_format=DigestOutput
            )
            return response.output_parsed
        except Exception:
            return self._fallback_digest(title=title, content=content)

