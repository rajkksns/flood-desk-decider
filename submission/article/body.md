# Flood Desk: classifying every customer message with Strands Decider 2B before the LLM replies

By rajkksns

Flood Desk is a lead-triage agent for a small plumbing and electrical business. It reads every incoming customer message, decides what kind of request it is with Strands Decider 2B, and only then lets Amazon Bedrock write the reply. The point of putting a decision model first is control: a burst pipe should never queue behind a price enquiry, a vendor advert should get no reply at all, and a message the system is unsure about should go to a person rather than get a confident wrong answer. This is a technical write-up of how that decision is wired, what it cost, and what the numbers do and do not prove.

## The design: decide first, generate second

Most agent bugs I hit came from asking one LLM call to both judge and act. If the model decides the category and writes the reply in the same breath, the reply can quietly drift from the category, and the "confidence" it reports is not a probability I can branch on. So Flood Desk splits the two jobs. Strands Decider 2B does the judgement: it reads the raw message and returns a typed category with a calibrated probability. My own code reads that probability and chooses an action. Amazon Bedrock (Amazon Nova Pro, us.amazon.nova-pro-v1:0) writes the words, but only after the category is fixed, so the prose cannot contradict the decision.

That ordering is the whole architecture. The agent is a Strands Agent; its tools draft the reply for a given category; the decision sits in front of all of it; and the deployment target is Amazon Bedrock AgentCore Runtime in us-east-1, which is where the demo was recorded. I built it with Kiro in a spec-driven flow, so the use case, the decision questions, the eval cases, and this article stay in step.

< FIGURE 1 of 6: upload submission/article/img/demo.png here >
Alt text: The demo UI: the conversation on the left, the decider's typed answers and verdict on the right

## The decision

The decision is one typed question over seven categories, each option carrying its own definition:

```python
QUESTIONS = {
    "category": Decider.choice(
        "Which kind of request is this customer message?",
        LEAD_CATEGORIES,
    ),
}
```

The categories are emergency, new_quote, job_status, reschedule_or_cancel, complaint, general_question, and spam_or_irrelevant. The definitions carry most of the signal: "emergency" is an urgent problem needing a same-day visit such as a burst pipe or a power cut; "spam_or_irrelevant" is an advert, a vendor pitch, or a wrong number. This is the right job for a decision model rather than another LLM call, because it is a language judgement (what did this person actually mean?) that runs on every single message, so it has to be cheap, fast at the tail, and return a number the code can trust.

The routing rule is ordinary Python I own, which means the threshold and the three actions are if-statements, not model output:

```python
verdict = LeadTriage(Decider()).route(customer_message)
if verdict.action == "human": queue_for_owner(...)
else: handle_by_category(verdict.category, customer_message)
```

Inside `route`, if confidence is at or above 0.6 and the category is not spam, the agent acts alone. If the category is spam and the decider is sure, the message is dropped with no reply. If confidence is below the threshold, the message is handed to a person. That last branch is why the calibrated probability matters: the agent escalates what it is unsure about instead of guessing.

## Measured

I ran the decider against the same Bedrock model asked the same classification question, over 32 labelled cases. The decider ran in the AWS User Group Madurai hosted mode (ugmdu), model strands-decider-2b-hobson-v19; the baseline was us.amazon.nova-pro-v1:0 on Amazon Bedrock.

Decider: strands-decider-2b-hobson-v19 (ugmdu). 32 labelled cases, 32 decisions.

| | Strands Decider 2B | us.amazon.nova-pro-v1:0 |
|---|---|---|
| Accuracy | 100.0% | 100.0% |
| Latency p50 per decision | 1967 ms | 1834 ms |
| Latency p95 | 2178 ms | 5290 ms |
| Cost per 1,000 decisions | $0.0350 | $0.9051 |
| Answered alone at confidence >= 0.7 | 84% | 100% |
| Accuracy when confident | 100.0% | 100.0% |

Read these honestly. Both models got every case right, so accuracy here is a tie, and at the median the LLM was slightly faster (1.83 s against 1.97 s over the hosted API plus my network). The decider's real wins are cost and tail latency: about $0.035 against $0.905 per 1,000 decisions, roughly 26 times cheaper, and a p95 of 2.18 s against the LLM's 5.29 s, so its slowest calls were far tighter. The other difference is confidence. The decider returned a calibrated probability, so 84 percent of messages cleared the 0.7 threshold and were answered alone while the rest went to a person; the LLM reported a flat high confidence on everything, so it would never have escalated anything.

The accuracy number is weak evidence and I want to be clear about why: those 32 labels are cases I wrote and labelled myself, so they reflect my own sense of the categories, not real customer traffic, and 32 is far too few to separate two models that both scored 100 percent. Treat the accuracy row as "neither model embarrassed itself on a tiny hand-written set", not as proof of real-world correctness. The cost and p95 gaps are more robust because they come from the same 32 runs measured the same way, and they are large rather than marginal.

< FIGURE 2 of 6: upload submission/article/img/architecture.png here >
Alt text: Architecture: the user, the agent with its tools and decision, Amazon Bedrock and Strands Decider 2B

< FIGURE 3 of 6: upload submission/article/img/bench-accuracy.png here >
Alt text: Accuracy of Strands Decider 2B and the Bedrock LLM on the labelled cases

< FIGURE 4 of 6: upload submission/article/img/bench-latency.png here >
Alt text: Median latency per decision for both

< FIGURE 5 of 6: upload submission/article/img/bench-cost.png here >
Alt text: Cost per 1,000 decisions for both

< FIGURE 6 of 6: upload submission/article/img/bench-confidence.png here >
Alt text: Accuracy against the share of decisions answered without a human, as the confidence threshold moves

## Reuse it

The pattern lives in agent/decision.py, tagged #policy. It is a category map with a short definition per option, one typed choice question built from it, a threshold in code, and a LeadTriage class that wraps the decider call and the routing rule. To adapt it to your own agent, change the categories and their definitions, keep each definition short and concrete, and set the threshold in code you own. Any single-label "which bucket is this text?" decision fits: ticket routing, moderation pre-screening, intent tagging. The one rule to keep is to let the decider judge language only; pull numbers, dates, and addresses out in code and put them in the state rather than asking the model to invent them.

## What is next

The honest takeaway for anyone building on AWS: the decision model did not beat the LLM on raw median speed here, but it was far cheaper, far more stable at the tail, and gave me a confidence I could branch on, which is what makes the human-handoff safe. Next I want a larger, independently labelled eval set so the accuracy claim means something, code-side extraction of phone numbers and addresses, and a live owner queue for the escalated messages.

---

Code: https://github.com/rajkksns/flood-desk-decider . Video: https://youtu.be/--mKWqqgm2I . Tags: #strands-decider-2b #policy

Built with the AWS User Group Madurai Strands Decider hackathon kit
