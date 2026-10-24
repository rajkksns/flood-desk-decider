0. This is Flood Desk. Amazon Bedrock writes the replies. Strands Decider reads each customer message first and decides what kind of request it is, before anything else happens.

1. Flood Desk reads every customer message for a plumbing and electrical business and decides what kind of request it is. What it does: Sorts each customer message into a category with Strands Decider 2B. Acts on clear messages and hands unsure ones to a person. Drops adverts and wrong numbers without replying. Runs on Amazon Bedrock AgentCore Runtime.

2. The agent you are about to see is running on Amazon Bedrock AgentCore Runtime.

3. A customer has water spreading under the sink and wants someone straight away. The decider scored confidence 0.86, so the verdict was act, in 1.3 seconds.

4. A customer asks for a price on a new job. The decider scored confidence 0.96, so the verdict was act, in 1.3 seconds.

5. This message is vague, so the decider may not be sure what kind of request it is. The decider scored confidence 0.81, so the verdict was act, in 1.2 seconds.

6. On 32 labelled decisions, with the decider on the AWS User Group Madurai hosted API, Strands Decider was 100% accurate at a median of 1967 milliseconds, against 100% and 1834 milliseconds for the Bedrock LLM asked the same questions.

7. One decision per message, a confidence the code can branch on, and a person for anything the decider is unsure about. Amazon Bedrock writes the replies.