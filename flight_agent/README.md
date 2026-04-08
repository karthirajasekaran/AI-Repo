# A quest in the clouds

### Q. What is this quest?
It is a fun way to assess your **AI Engineering** skills. It is also a representative sample of the work we do at Rearc.

We've built a basic orchestrator with Langgraph. Your job is to build a **Passenger Advocate Agent** that can help travelers understand their rights when things go wrong at the airport.

### Q. So what skills should I have?
- **Python proficiency:** You can write effective, modular code.
- **LLM API Usage:** Experience with OpenAI, Anthropic, or AWS Bedrock APIs.
- **Orchestration:** Understanding of state management and agentic workflows (e.g., LangGraph, State Machines, or custom control flows).
- **Tool Use:** Ability to define structured interfaces for LLMs to interact with data.
- **RAG concepts:** Retrieval, context injection, and semantic search.

### Q. What do I have to do?
We have provided two data sources:
1.  `hive_metastore.default.ontime_cleaned`: A dataset of flight records, delays, and cancellations.
2.  `policies.md`: The official "Consumer Guide to Air Travel," including specific commitments from airlines regarding cancellations and delays.

**The Challenge:**
Build a Python application where an LLM Agent acts as a Travel Advocate. The Agent must answer user questions by determining *which* data source to use, *how* to query it, and *how* to synthesize the final answer.

### Q. How do I know I have solved it?
Your Agent should be able to answer the following types of questions correctly:

1.  **User:** *"What was the status of flight UA123 on 2023-01-01?"*
2.  **User:** *"Since it was cancelled, is United required to provide me with a hotel?"*
3.  **User:** *"My flight was delayed 3 hours. Do I get a meal voucher?"*

### Q. What do I have to submit?
1.  **Your Code (in Databricks):** Please develop **directly** inside the provided Databricks notebook and make sure it can be run from within the platform.
2.  **Your Thought Process (`PROCESS.md`):** We value your engineering judgment as much as your code. Create a markdown file (or a clear section in the notebook) covering:
    *   **Architecture:** Why did you structure the agent this way?
    *   **Trade-offs:** What shortcuts did you take for this demo, and how would you handle them in a real production environment (e.g., security, scale, cost)?
    *   **Retrospective:** What was the hardest part to get right?

### **Bonus:**
If you're having fun and don't want to stop, demonstrate how you would give a stakeholder confidence that your Agent is reliable, consistent, and safe to deploy.

### **Misc:**
**Q: Can I use AI to assist me?**
We (obviously) love AI, and you absolutely *may* use it as a reference tool. **However:**
1.  You must understand every line of code you submit. We *will* ask you to explain your logic in the interview.
2.  We encourage you to be open about usage! Tell us: *"I used Claude to generate the Pydantic schema, but I had to manually fix the error handling logic."*

**Q: How do I install new Python packages in this environment?**
Create and run a cell with a `%pip` command. For example, to install `langchain`: `%pip install langchain`

**Q: Do I have to use specific software tools?**
Aside from the requirement to **work inside the Databricks notebook**, you can use whichever Python packages or architectural approaches you like.

**Q: How do I turn my work in?**
We can see your completed notebook directly from inside the Databricks environment. Just let your contact at Rearc know once you are done.
