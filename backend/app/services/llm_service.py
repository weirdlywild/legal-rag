"""LLM service using OpenAI GPT-4o with strict grounding."""

import re
from typing import Any

import tiktoken
from openai import OpenAI

from ..config import get_settings, Settings


class LLMService:
    """Service for generating answers using GPT-4o with grounding."""

    SYSTEM_PROMPT = """You are a legal document assistant. Answer questions ONLY using the provided document excerpts.

RULES:
- Use ONLY information from the sources provided
- Cite every claim with [Source N]
- Use bullet points for multiple items
- If sources don't answer the question, say so
- End with: "Confidence: high/medium/low"

This is for research only, not legal advice."""

    def __init__(self, settings: Settings | None = None):
        """Initialize the LLM service."""
        self.settings = settings or get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string."""
        return len(self.tokenizer.encode(text))

    def is_healthy(self) -> bool:
        """Check if OpenAI API is accessible."""
        try:
            # Make a minimal API call to check connectivity
            self.client.models.retrieve(self.settings.openai_model)
            return True
        except Exception:
            return False

    def _build_context(self, chunks: list[dict[str, Any]]) -> str:
        """Build compact context string from retrieved chunks."""
        context_parts = []

        for i, chunk in enumerate(chunks):
            source_num = i + 1
            doc_title = chunk.get("document_title", "Unknown")
            page_num = chunk.get("page_number", "?")
            text = chunk.get("text", "")

            context_parts.append(
                f"[Source {source_num}] {doc_title}, p.{page_num}:\n{text}"
            )

        return "\n\n".join(context_parts)

    def _parse_confidence(self, response_text: str) -> str:
        """Parse confidence level from response."""
        text_lower = response_text.lower()

        # Look for explicit confidence statement
        confidence_match = re.search(r'confidence:\s*(high|medium|low)', text_lower)
        if confidence_match:
            return confidence_match.group(1)

        # Infer from content
        if "cannot find sufficient" in text_lower or "insufficient" in text_lower:
            return "low"

        if "clearly" in text_lower or "explicitly" in text_lower:
            return "high"

        return "medium"

    def generate_answer(
        self,
        question: str,
        context_chunks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Generate an answer using GPT-4o with strict grounding.

        Args:
            question: User's question
            context_chunks: Retrieved document chunks

        Returns:
            Dict with answer, confidence, and usage stats
        """
        if not context_chunks:
            return {
                "answer": "I cannot find sufficient information in the provided documents to answer this question. No relevant document sections were found.",
                "confidence": "low",
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_usd": 0.0,
            }

        context = self._build_context(context_chunks)

        user_prompt = f"""Question: {question}

Sources:
{context}

Answer the question using only the sources above. Cite with [Source N]. End with "Confidence: high/medium/low" """

        # Count input tokens
        input_text = self.SYSTEM_PROMPT + user_prompt
        input_tokens = self.count_tokens(input_text)

        # Call GPT-4o
        response = self.client.chat.completions.create(
            model=self.settings.openai_model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.settings.openai_temperature,
            max_tokens=self.settings.openai_max_tokens,
        )

        answer = response.choices[0].message.content or ""
        output_tokens = self.count_tokens(answer)

        # Calculate cost
        cost = (
            (input_tokens / 1000 * self.settings.gpt4o_input_cost_per_1k) +
            (output_tokens / 1000 * self.settings.gpt4o_output_cost_per_1k)
        )

        # Parse confidence
        confidence = self._parse_confidence(answer)

        return {
            "answer": answer,
            "confidence": confidence,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost,
        }


# Singleton instance
_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    """Get or create LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
