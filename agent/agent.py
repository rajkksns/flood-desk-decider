"""Flood Desk: lead triage for a local plumbing and electrical business.

Strands Decider 2B sorts each customer message into one category (agent/decision.py) before any
reply is written. A confidence threshold decides whether the agent acts alone or hands the message
to a person. Amazon Bedrock, called through a Strands Agent, writes the reply after the category is
set. Numbers, dates and addresses are meant for code to extract, not the LLM or the decider.

    from agent.agent import HackathonAgent
    out = HackathonAgent().chat("water everywhere under the sink, can someone come now??")
    out["reply"], out["decisions"]
"""

from __future__ import annotations

import time
from typing import Any

from strands import Agent

from decider_kit import Decider
from decider_kit.llm import agent_model, default_model_id, image_blocks, strip_thinking

from .decision import LeadTriage
from .tools import TOOLS

NAME = "Flood Desk: lead triage for a plumbing and electrical business"

SYSTEM_PROMPT = """You reply to customers of a small plumbing and electrical business.
Be brief, polite and plain. Never invent prices, dates, arrival times or engineer names.
Never promise a visit time unless the customer's message already names one.
If you need an address or a phone number to book a visit, ask for it."""

# What the reply should do, once the decider has set the category.
CATEGORY_GUIDE = {
    "emergency": "The customer has an urgent problem. Ask for their address and a phone number, and say "
                 "someone will call back straight away to arrange a same-day visit.",
    "new_quote": "The customer wants a price. Say you will prepare an estimate, and ask for the job details you need.",
    "job_status": "The customer asks about an existing booking. Say you will check, and that someone will confirm the time.",
    "reschedule_or_cancel": "The customer wants to move or cancel a visit. Say you have noted the request "
                            "and will confirm the change.",
    "complaint": "The customer is unhappy. Apologise briefly and say a manager will call them. "
                 "Do not argue, and do not offer refunds.",
    "general_question": "The customer asks a general question. Answer only what you are sure of, "
                        "and say so if you do not know.",
}
HANDOFF_GUIDE = ("A person on the team must decide this one. Say that a member of the team will reply shortly. "
                 "Do not promise anything specific.")


class HackathonAgent:
    """One Strands agent per session. The decision runs first; the LLM only writes the reply."""

    def __init__(self, decider: Decider | None = None, model_id: str | None = None, eager: bool | None = None):
        self.decider = decider or Decider()
        self.eager = bool(eager)  # kept for the shared interface; Flood Desk does not need an eager demo
        self.model_id = model_id or default_model_id()  # LLM_PROVIDER in .env: bedrock, local, ugmdu
        self.triage = LeadTriage(self.decider)
        self.sessions: dict[str, Agent] = {}

    def _session(self, session_id: str) -> Agent:
        if session_id not in self.sessions:
            self.sessions[session_id] = Agent(model=agent_model(self.model_id), system_prompt=SYSTEM_PROMPT,
                                              tools=TOOLS, callback_handler=None)
        return self.sessions[session_id]

    def chat(self, message: str, session_id: str = "default", images: list[Any] | None = None) -> dict[str, Any]:
        """`images` (optional) go to the LLM only; the decision reads the text of the message."""
        agent = self._session(session_id)
        t0 = time.perf_counter()
        verdict = self.triage.route(message)
        decision = {**self.triage.log[-1], "verdict": verdict.action}

        if verdict.action == "drop":
            reply = "This looks like an advert or a wrong number, so no reply was sent."
        else:
            guide = HANDOFF_GUIDE if verdict.action == "human" else CATEGORY_GUIDE.get(verdict.category, HANDOFF_GUIDE)
            prompt = (f"[Category decided by Strands Decider 2B: {verdict.category}. "
                      f"Guidance for your reply: {guide}]\n\nCustomer message:\n{message}")
            content = [*image_blocks(images), {"text": prompt}] if images else prompt
            reply = strip_thinking(str(agent(content)))  # Nova's <thinking>, Qwen's <think>

        return {"reply": reply, "decisions": [decision], "model_id": self.model_id,
                "latency_ms": round((time.perf_counter() - t0) * 1000), "agent": NAME, "eager": self.eager}


if __name__ == "__main__":
    import json
    import sys

    a = HackathonAgent()
    for msg in sys.argv[1:] or ["water everywhere under the sink, can someone come now??",
                                "Can you quote me for replacing the ceiling fans in my lounge?"]:
        print(json.dumps(a.chat(msg), indent=1))
