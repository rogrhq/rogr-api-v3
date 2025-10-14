"""
Level 4: Cross-Encoder Entailment System

Provides semantic similarity and entailment detection using pre-trained models.
Designed to replace dictionary-based paraphrase matching with unlimited vocabulary.
"""

from sentence_transformers import SentenceTransformer, CrossEncoder
import numpy as np
from functools import lru_cache
import hashlib

class SemanticEmbeddings:
    """
    Smart embeddings system with bi-encoder (fast) and cross-encoder (precise).

    Architecture:
    - Bi-encoder: Fast semantic similarity for paraphrase matching
    - Cross-encoder: Precise entailment detection for stance determination
    """

    def __init__(self):
        print("Loading semantic models...")

        # Bi-encoder: Fast similarity (50ms)
        # Used for: Paraphrase matching, quick filtering
        self.bi_encoder = SentenceTransformer('all-MiniLM-L6-v2')

        # Cross-encoder: Precise entailment (100-150ms)
        # Used for: Stance detection (support/challenge/contextual)
        self.cross_encoder = CrossEncoder('cross-encoder/nli-deberta-v3-base')

        # Embedding cache to avoid recomputation
        self.embedding_cache = {}

        print("✓ Semantic models loaded")

    def get_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Fast semantic similarity using bi-encoder.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score 0.0-1.0

        Examples:
            "rose" vs "increased" → ~0.75
            "travels" vs "speed" → ~0.65
            "faster" vs "higher" → ~0.70
        """
        # Get cached embeddings
        emb1 = self._get_embedding(text1)
        emb2 = self._get_embedding(text2)

        # Cosine similarity
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))

        return float(similarity)

    def get_entailment_stance(self, claim: str, evidence: str) -> dict:
        """
        Precise entailment detection using cross-encoder.

        Args:
            claim: The claim text
            evidence: The evidence text

        Returns:
            {
                "stance": "support" | "challenge" | "contextual_support" | "unrelated",
                "confidence": 0.0-1.0,
                "entailment_score": 0.0-1.0,
                "reasoning": str
            }

        Examples:
            Claim: "Water boils at 100°C"
            Evidence: "Boiling point is 100 degrees Celsius"
            → {"stance": "support", "confidence": 0.94, ...}

            Claim: "Water boils at 100°C"
            Evidence: "Water boils at lower temp at altitude"
            → {"stance": "contextual_support", "confidence": 0.72, ...}

            Claim: "Budget increased 8%"
            Evidence: "Budget decreased 8%"
            → {"stance": "challenge", "confidence": 0.91, ...}
        """
        # Get entailment scores [contradiction, neutral, entailment]
        raw_scores = self.cross_encoder.predict([(claim, evidence)])[0]

        # Apply softmax to normalize logits to probabilities (0-1)
        exp_scores = np.exp(raw_scores - np.max(raw_scores))  # Subtract max for numerical stability
        scores = exp_scores / np.sum(exp_scores)

        contradiction_score = scores[0]
        neutral_score = scores[1]
        entailment_score = scores[2]

        # Determine stance based on scores
        max_score = max(contradiction_score, neutral_score, entailment_score)

        if entailment_score == max_score:
            if entailment_score > 0.7:
                stance = "support"
                reasoning = "Evidence directly supports the claim"
            else:
                # Lower confidence entailment might be contextual
                stance = "contextual_support"
                reasoning = "Evidence supports with qualifications or different context"

        elif contradiction_score == max_score:
            if contradiction_score > 0.6:
                stance = "challenge"
                reasoning = "Evidence contradicts the claim"
            else:
                stance = "contextual_support"
                reasoning = "Evidence provides context that qualifies the claim"

        else:  # neutral is max
            if neutral_score > 0.5:
                stance = "unrelated"
                reasoning = "Evidence does not directly address the claim"
            else:
                stance = "contextual_support"
                reasoning = "Evidence is tangentially related to the claim"

        return {
            "stance": stance,
            "confidence": float(max_score),
            "entailment_score": float(entailment_score),
            "contradiction_score": float(contradiction_score),
            "neutral_score": float(neutral_score),
            "reasoning": reasoning
        }

    def get_contextual_similarity(self, phrase1: str, phrase2: str, context: str = None) -> float:
        """
        Context-aware similarity (Level 2 intelligence).

        If context provided, embeds phrases with context for disambiguation.

        Examples:
            "rose", "increased", context="temperature" → 0.89
            "rose", "increased", context="elevation" → 0.45
        """
        if context:
            phrase1_with_context = f"{context}: {phrase1}"
            phrase2_with_context = f"{context}: {phrase2}"
        else:
            phrase1_with_context = phrase1
            phrase2_with_context = phrase2

        return self.get_semantic_similarity(phrase1_with_context, phrase2_with_context)

    def _get_embedding(self, text: str) -> np.ndarray:
        """Get cached embedding for text."""
        # Create cache key
        cache_key = hashlib.md5(text.encode()).hexdigest()

        if cache_key not in self.embedding_cache:
            # Compute and cache
            self.embedding_cache[cache_key] = self.bi_encoder.encode(text, convert_to_numpy=True)

        return self.embedding_cache[cache_key]

    def clear_cache(self):
        """Clear embedding cache (for testing or memory management)."""
        self.embedding_cache.clear()


# Global singleton instance (loaded once at startup)
_embeddings_instance = None

def get_embeddings() -> SemanticEmbeddings:
    """Get or create the global embeddings instance."""
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = SemanticEmbeddings()
    return _embeddings_instance


# Public API functions (for easy integration)

def get_semantic_similarity(text1: str, text2: str) -> float:
    """
    Public API: Get semantic similarity between two texts.

    This is a drop-in replacement for dictionary-based paraphrase matching.
    """
    return get_embeddings().get_semantic_similarity(text1, text2)


def get_entailment_stance(claim: str, evidence: str) -> dict:
    """
    Public API: Get entailment-based stance detection.

    This can replace complex frame-based stance logic in P20.
    """
    return get_embeddings().get_entailment_stance(claim, evidence)


def get_contextual_similarity(phrase1: str, phrase2: str, context: str = None) -> float:
    """
    Public API: Get context-aware similarity.
    """
    return get_embeddings().get_contextual_similarity(phrase1, phrase2, context)
