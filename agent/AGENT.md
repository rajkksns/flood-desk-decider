# Use case

Flood Desk: lead triage for a small local plumbing and electrical business.

- **Pitch:** Flood Desk reads every customer message and decides what kind of request it is, so an emergency is never queued behind a price enquiry.
- **Who it is for:** a small plumbing and electrical business that gets enquiries by message at all hours, and the customers who need a fast, correct reply.
- **Features:**
  - sorts each customer message into one of seven categories with Strands Decider 2B;
  - acts alone on clear messages and hands unsure ones to a person;
  - drops adverts and wrong numbers without replying;
  - the reply is written by Amazon Bedrock after the category is set, so it cannot contradict the decision.
- **The decision handed to Strands Decider 2B:** which kind of request is this customer message? (`#policy`)
- **Why a decision model:** every incoming message needs a category before anything else happens. The decision must be fast, cheap, and return a confidence the code can branch on.
- **Amazon Bedrock:** writes the reply for the category it is given (Amazon Nova Pro by default).
- **Not yet built:** extracting numbers, dates and addresses in code; a live owner queue.
