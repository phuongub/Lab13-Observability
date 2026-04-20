from __future__ import annotations

import time
from dataclasses import dataclass

from . import metrics
from .mock_llm import FakeLLM
from .mock_rag import retrieve
from .pii import hash_user_id, summarize_text
from .tracing import (
    end_span,
    langfuse_context,
    langfuse_span,
    observe,
    start_span,
    trace_log,
    update_current_span,
)


@dataclass
class AgentResult:
    answer: str
    latency_ms: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    quality_score: float


class LabAgent:
    def __init__(self, model: str = "claude-sonnet-4-5") -> None:
        self.model = model
        self.llm = FakeLLM(model=model)

    @observe()
    def run(self, user_id: str, feature: str, session_id: str, message: str) -> AgentResult:
        started = time.perf_counter()
        user_id_hash = hash_user_id(user_id)

        agent_span_id = start_span(
            service="chat_service",
            event="agent_run",
            parent_span_id=None,
            feature=feature,
            session_id=session_id,
            user_id_hash=user_id_hash,
        )

        trace_log(
            event="agent_started",
            service="chat_service",
            span_id=agent_span_id,
            parent_span_id=None,
            feature=feature,
            session_id=session_id,
            user_id_hash=user_id_hash,
        )

        # Structured retrieval with Langfuse span
        with langfuse_span(
            name="retrieval",
            input={"query": message},
            metadata={"feature": feature, "session_id": session_id},
            session_id=session_id,
            user_id=user_id_hash,
            tags=["retrieval", feature],
        ) as retrieval_span:
            docs = retrieve(message)
            if retrieval_span:
                retrieval_span.update(
                    output={"doc_count": len(docs), "docs": docs},
                    metadata={"retrieved_doc_count": len(docs)},
                )

        trace_log(
            event="retrieval_finished",
            service="chat_service",
            span_id=agent_span_id,
            parent_span_id=None,
            feature=feature,
            session_id=session_id,
            user_id_hash=user_id_hash,
            doc_count=len(docs),
            payload={"query_preview": summarize_text(message)},
        )

        prompt = f"Feature={feature}\nDocs={docs}\nQuestion={message}"

        # Structured LLM call with Langfuse span
        with langfuse_span(
            name="llm_generation",
            input={"prompt": prompt, "model": self.model},
            metadata={"model": self.model, "feature": feature},
            session_id=session_id,
            user_id=user_id_hash,
            tags=["llm", self.model, feature],
        ) as llm_span:
            response = self.llm.generate(prompt)
            if llm_span:
                llm_span.update(
                    output={"text": response.text},
                    metadata={
                        "tokens_in": response.usage.input_tokens,
                        "tokens_out": response.usage.output_tokens,
                        "model": self.model,
                    },
                )

        trace_log(
            event="llm_finished",
            service="model_inference",
            span_id=agent_span_id,
            parent_span_id=None,
            feature=feature,
            session_id=session_id,
            user_id_hash=user_id_hash,
            model=self.model,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
        )

        quality_score = self._heuristic_quality(message, response.text, docs)
        latency_ms = int((time.perf_counter() - started) * 1000)
        cost_usd = self._estimate_cost(response.usage.input_tokens, response.usage.output_tokens)

        trace_log(
            event="agent_finished",
            service="chat_service",
            span_id=agent_span_id,
            parent_span_id=None,
            feature=feature,
            session_id=session_id,
            user_id_hash=user_id_hash,
            model=self.model,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            quality_score=quality_score,
            payload={"answer_preview": summarize_text(response.text)},
        )

        end_span(
            service="chat_service",
            event="agent_done",
            span_id=agent_span_id,
            parent_span_id=None,
            feature=feature,
            session_id=session_id,
            model=self.model,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            quality_score=quality_score,
        )

        # Update trace with metadata following best practices
        langfuse_context.update_current_trace(
            user_id=user_id_hash,
            session_id=session_id,
            tags=["lab", feature, self.model],
            metadata={
                "quality_score": quality_score,
                "feature": feature,
                "model": self.model,
            },
        )
        
        # Update current observation with structured output
        update_current_span(
            output={"answer": response.text},
            metadata={
                "doc_count": len(docs),
                "query_preview": summarize_text(message),
                "answer_preview": summarize_text(response.text),
                "quality_score": quality_score,
            },
            input={
                "message": message,
                "feature": feature,
                "doc_count": len(docs),
            },
            cost_usd=cost_usd,
            latency_ms=latency_ms,
        )
        langfuse_context.update_current_observation(
            usage_details={"input": response.usage.input_tokens, "output": response.usage.output_tokens},
        )

        metrics.record_request(
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            quality_score=quality_score,
        )

        return AgentResult(
            answer=response.text,
            latency_ms=latency_ms,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            cost_usd=cost_usd,
            quality_score=quality_score,
        )

    def _estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        input_cost = (tokens_in / 1_000_000) * 3
        output_cost = (tokens_out / 1_000_000) * 15
        return round(input_cost + output_cost, 6)

    def _heuristic_quality(self, question: str, answer: str, docs: list[str]) -> float:
        score = 0.5
        if docs:
            score += 0.2
        if len(answer) > 40:
            score += 0.1
        if question.lower().split()[0:1] and any(token in answer.lower() for token in question.lower().split()[:3]):
            score += 0.1
        if "[REDACTED" in answer:
            score -= 0.2
        return round(max(0.0, min(1.0, score)), 2)