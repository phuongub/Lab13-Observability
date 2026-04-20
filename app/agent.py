from __future__ import annotations

import time
from dataclasses import dataclass

from .mock_llm import FakeLLM
from .mock_rag import retrieve
from .pii import hash_user_id
from .tracing import get_langfuse_client


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

    def run(self, user_id: str, feature: str, session_id: str, message: str) -> AgentResult:
        started = time.perf_counter()
        user_id_hash = hash_user_id(user_id)
        langfuse = get_langfuse_client()

        if not langfuse:
            context = retrieve(message)
            response = self.llm.generate(f"{context}\n\nUser: {message}")
            latency_ms = int((time.perf_counter() - started) * 1000)
            cost_usd = (response.usage.input_tokens * 0.00015 + response.usage.output_tokens * 0.0006) / 1000
            quality_score = 0.85

            return AgentResult(
                answer=response.text,
                latency_ms=latency_ms,
                tokens_in=response.usage.input_tokens,
                tokens_out=response.usage.output_tokens,
                cost_usd=cost_usd,
                quality_score=quality_score,
            )

        with langfuse.start_as_current_observation(
            as_type="span",
            name="agent_run",
            input={"message": message, "feature": feature},
            metadata={"user_id_hash": user_id_hash, "session_id": session_id},
        ) as agent_span:
            with langfuse.start_as_current_observation(
                as_type="span",
                name="retrieve_context",
                input={"query": message},
            ) as retrieve_span:
                context = retrieve(message)
                retrieve_span.update(output={"context": context})

            with langfuse.start_as_current_observation(
                as_type="generation",
                name="llm_generate",
                model=self.model,
                input={"prompt": f"{context}\n\nUser: {message}"},
            ) as gen_span:
                response = self.llm.generate(f"{context}\n\nUser: {message}")
                gen_span.update(
                    output={"text": response.text},
                    usage_details={
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                    },
                )

            latency_ms = int((time.perf_counter() - started) * 1000)
            cost_usd = (response.usage.input_tokens * 0.00015 + response.usage.output_tokens * 0.0006) / 1000
            quality_score = 0.85

            agent_span.update(
                output={
                    "answer": response.text,
                    "latency_ms": latency_ms,
                    "tokens_in": response.usage.input_tokens,
                    "tokens_out": response.usage.output_tokens,
                    "cost_usd": cost_usd,
                    "quality_score": quality_score,
                }
            )

            return AgentResult(
                answer=response.text,
                latency_ms=latency_ms,
                tokens_in=response.usage.input_tokens,
                tokens_out=response.usage.output_tokens,
                cost_usd=cost_usd,
                quality_score=quality_score,
            )