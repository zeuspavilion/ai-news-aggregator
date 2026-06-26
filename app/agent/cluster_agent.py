import os
import math
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class ClusterAgent:
    def __init__(self):
        self.client = None
        self.model = "text-embedding-3-small"
        
        # Load settings
        self.use_openai = os.getenv("USE_OPENAI_AGENTS", "false").strip().lower() in {"1", "true", "yes", "on"}
        self.api_key = os.getenv("OPENAI_API_KEY")
        
        # Load thresholds
        try:
            self.similarity_threshold = float(os.getenv("CLUSTER_SIMILARITY_THRESHOLD", "0.82"))
        except ValueError:
            self.similarity_threshold = 0.82
            
        try:
            self.jaccard_threshold = float(os.getenv("FALLBACK_JACCARD_THRESHOLD", "0.15"))
        except ValueError:
            self.jaccard_threshold = 0.15

        if self.use_openai and self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client for clustering: {e}")
                self.client = None

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        dot_product = sum(x * y for x, y in zip(v1, v2))
        magnitude1 = math.sqrt(sum(x * x for x in v1))
        magnitude2 = math.sqrt(sum(y * y for y in v2))
        if not magnitude1 or not magnitude2:
            return 0.0
        return dot_product / (magnitude1 * magnitude2)

    def _stem(self, word: str) -> str:
        # simple rule-based stemmer to consolidate word variants
        if word.endswith("ing"):
            return word[:-3]
        if word.endswith("ed"):
            return word[:-2]
        if word.endswith("es"):
            return word[:-2]
        if word.endswith("s") and not word.endswith("ss"):
            return word[:-1]
        return word

    def _get_tokens(self, text: str) -> set:
        if not text:
            return set()
        # lowercase alphanumeric tokenization, keeping hyphens
        words = "".join([c if (c.isalnum() or c == "-") else " " for c in text.lower()]).split()
        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with",
            "is", "are", "was", "were", "of", "about", "that", "this", "these", "those",
            "it", "its", "they", "them", "from", "by", "as", "at", "by", "for", "from",
            "how", "what", "why", "who", "which", "where", "when", "be", "been", "have",
            "has", "had", "do", "does", "did", "will", "would", "should", "can", "could"
        }
        raw_tokens = {w for w in words if len(w) >= 3 and w not in stopwords}
        return {self._stem(token) for token in raw_tokens}

    def _jaccard_similarity(self, s1: set, s2: set) -> float:
        if not s1 or not s2:
            return 0.0
        return len(s1 & s2) / len(s1 | s2)

    def _get_jaccard_score(self, d1: dict, d2: dict) -> float:
        t1_tokens = self._get_tokens(d1.get("title", ""))
        t2_tokens = self._get_tokens(d2.get("title", ""))
        s1_tokens = self._get_tokens(d1.get("summary", ""))
        s2_tokens = self._get_tokens(d2.get("summary", ""))
        
        title_sim = self._jaccard_similarity(t1_tokens, t2_tokens)
        summary_sim = self._jaccard_similarity(s1_tokens, s2_tokens)
        
        # Titles are much more descriptive of same-event topics
        return 0.7 * title_sim + 0.3 * summary_sim

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not self.client:
            raise ValueError("OpenAI client not initialized")
        
        # Call OpenAI embeddings API
        response = self.client.embeddings.create(
            input=texts,
            model=self.model
        )
        return [item.embedding for item in response.data]

    def cluster_digests(self, digests: List[dict]) -> List[List[str]]:
        """
        Groups digests into clusters. Returns a list of clusters, 
        where each cluster is a list of digest IDs.
        """
        if not digests:
            return []

        # Try vector clustering if OpenAI is enabled
        if self.client:
            try:
                logger.info("Attempting OpenAI vector-based clustering...")
                # Create texts to embed (Title + Summary)
                texts = [f"{d.get('title', '')}\n{d.get('summary', '')}" for d in digests]
                embeddings = self.get_embeddings(texts)
                
                return self._vector_cluster(digests, embeddings)
            except Exception as e:
                logger.warning(f"Vector clustering failed ({e}). Falling back to local text-based clustering.")
        
        # Fallback to local text-based clustering
        logger.info("Using local Jaccard text-based clustering fallback...")
        return self._local_cluster_fallback(digests)

    def _vector_cluster(self, digests: List[dict], embeddings: List[List[float]]) -> List[List[str]]:
        clusters = []  # list of lists of digest dicts
        
        for idx, digest in enumerate(digests):
            embedding = embeddings[idx]
            matched_cluster_idx = -1
            
            for c_idx, cluster in enumerate(clusters):
                # Calculate max similarity with any member of this cluster
                similarities = []
                for member in cluster:
                    member_idx = digests.index(member)
                    sim = self._cosine_similarity(embedding, embeddings[member_idx])
                    similarities.append(sim)
                
                if similarities and max(similarities) >= self.similarity_threshold:
                    matched_cluster_idx = c_idx
                    break
                    
            if matched_cluster_idx != -1:
                clusters[matched_cluster_idx].append(digest)
            else:
                clusters.append([digest])
                
        # Return list of list of IDs
        return [[d["id"] for d in cluster] for cluster in clusters]

    def _local_cluster_fallback(self, digests: List[dict]) -> List[List[str]]:
        clusters = []  # list of lists of digest dicts
        
        for digest in digests:
            matched_cluster_idx = -1
            
            for c_idx, cluster in enumerate(clusters):
                # Calculate max Jaccard similarity with any member of this cluster
                similarities = [self._get_jaccard_score(digest, member) for member in cluster]
                
                if similarities and max(similarities) >= self.jaccard_threshold:
                    matched_cluster_idx = c_idx
                    break
                    
            if matched_cluster_idx != -1:
                clusters[matched_cluster_idx].append(digest)
            else:
                clusters.append([digest])
                
        return [[d["id"] for d in cluster] for cluster in clusters]
