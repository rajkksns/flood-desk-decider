Title (max 255 characters):
Flood Desk: a lead-triage agent that classifies each message with Strands Decider 2B before Amazon Bedrock replies, about 26x cheaper per decision

Description (max 512 characters):
A technical write-up of Flood Desk, a Strands Agent for a plumbing and electrical business. Strands Decider 2B classifies each customer message into one of seven categories with calibrated confidence (#policy) before Amazon Bedrock writes the reply; unsure messages go to a person. On 32 self-written labels both models scored 100% (weak evidence), but the decider cost $0.035 vs $0.905 per 1,000 decisions, about 26x cheaper, with a tighter p95 (2.18 s vs 5.29 s). Deployed on AgentCore Runtime.

Tags:
strands-decider-2b, policy, amazon-bedrock, strands-agents, agentcore

Cover image: submission/article/cover.png
