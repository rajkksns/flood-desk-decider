"""REUSABLE DECISION PATTERN: lead triage for a service business  (#policy)

What it does
    Sorts each incoming customer message into one category with Strands Decider 2B, before the
    agent writes any reply. A confidence threshold decides whether the agent acts alone or hands
    the message to a person. An advert or wrong number the decider is sure about is dropped.

Typed questions and options
    category (choice): what kind of request the customer is making, each option with a definition.

Wiring (where it sits in the agent's path)
    verdict = LeadTriage(Decider()).route(customer_message)
    if verdict.action == "human": queue_for_owner(...)
    else: handle_by_category(verdict.category, customer_message)
    In agent/agent.py this runs first, and the LLM (Amazon Bedrock) writes the reply after it.

How to reuse it
    Change LEAD_CATEGORIES to your own categories and their definitions. Keep each definition
    short and concrete. Change THRESHOLD in code you own. Numbers, dates and addresses should be
    extracted by code, not by the decider; this version does not extract them yet.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from decider_kit import Decider, Decision

PATTERN_TAG = "#policy"

LEAD_CATEGORIES = {
    "emergency": "urgent problem needing a same-day visit, such as a burst pipe, flooding, or a power cut",
    "new_quote": "asks for a price or estimate for a new job",
    "job_status": "asks about an existing booking or when the work will happen",
    "reschedule_or_cancel": "wants to move or cancel an appointment",
    "complaint": "is unhappy with work already done or with a bill",
    "general_question": "asks about services, opening hours, or whether the business covers their area",
    "spam_or_irrelevant": "is an advert, a vendor pitch, or a wrong number",
}

QUESTIONS = {
    "category": Decider.choice(
        "Which kind of request is this customer message?",
        LEAD_CATEGORIES,
    ),
}

THRESHOLD = 0.6  # below this confidence the message goes to a person


@dataclass
class Verdict:
    action: str        # "act", "human" or "drop"
    category: str
    confidence: float
    answers: dict[str, Decision] | None = None

    def __repr__(self) -> str:  # keep the message text out of logs
        return f"Verdict(action={self.action!r}, category={self.category!r}, confidence={self.confidence:.2f})"


class LeadTriage:
    """Wraps the decider call and the routing rule. Thresholds live here, in code you own."""

    def __init__(self, decider: Decider, threshold: float = THRESHOLD):
        self.decider = decider
        self.threshold = threshold
        self.log: list[dict[str, Any]] = []

    def route(self, customer_message: str) -> Verdict:
        answers = self.decider.ask(f"Customer message:\n{customer_message}", QUESTIONS)
        d = answers["category"]
        conf = d.confidence
        action = "act" if conf >= self.threshold and d.label != "spam_or_irrelevant" else "human"
        if d.label == "spam_or_irrelevant" and conf >= self.threshold:
            action = "drop"
        self.log.append({"pattern": PATTERN_TAG, "category": d.label, "confidence": round(conf, 3),
                         "action": action, "decider_ms": round(self.decider.last_latency_ms or 0)})
        return Verdict(action=action, category=d.label or "?", confidence=conf, answers=answers)
