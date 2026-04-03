# LangGraph vs. Temporal: The Dual-Engine Architecture

When building a 3-day, long-running agent like Devin, a common confusion arises: **"Do I use LangGraph or Temporal to manage state?"**

The answer is: **You use both.** They solve two completely different problems. One is the "Brain," and the other is the "Life Support System."

## 1. LangGraph: The Agentic Brain (The "What")
**LangGraph** is a framework for structuring LLM reasoning. It allows you to define cyclical graphs: *Think -> Act -> Observe -> Repeat.*

*   **What it does:** It tells the agent *how* to solve a software engineering problem.
*   **The State it Manages:** "The compiler failed. The `package.json` needs updating. My next step is to call the `run_bash` tool with `npm install`."
*   **The Problem:** LangGraph runs in memory (or backed by a basic DB checkpointer). If the physical server running your Python/Node.js code crashes on Day 2, the LangGraph process dies. The API request times out. The agent is dead.

## 2. Temporal: The Life Support System (The "How")
**Temporal.io** is a Durable Execution Engine. It doesn't know anything about LLMs, prompts, or Python syntax errors. It only cares about *Tasks*.

*   **What it does:** It ensures that a function, once started, *will* finish, even if the datacenter catches on fire.
*   **The State it Manages:** "Worker 04 was executing `ToolCall(run_bash, npm install)`. The server crashed. I will spin up Worker 05, skip the LLM generation phase because we already have the answer from yesterday, and resume exactly at `run_bash`."
*   **The Problem:** Temporal is incredibly rigid. It is terrible at unstructured, fuzzy reasoning loops. It needs deterministic, explicit steps.

## 3. How They Combine in Production

If you build a SaaS Agent (the "AgentHood"), you wrap LangGraph *inside* Temporal.

1.  **The Trigger:** A user sends a WhatsApp message: *"Build a Next.js app."*
2.  **The Temporal Workflow Starts:** The OpenClaw Gateway kicks off a Temporal Workflow named `Build_NextJS_App`.
3.  **The LangGraph Node:** The Temporal Workflow calls an Activity. This Activity executes one "turn" of the LangGraph state machine.
4.  **The Checkpoint:** LangGraph decides: *"I need to run `npx create-next-app`."*
5.  **The Durable Hand-off:** The Python process tells Temporal: *"I am pausing. Wake me up when `npx create-next-app` finishes in the MicroVM."*
6.  *(Disaster Strikes: The SaaS server crashes, or a new deployment is pushed).*
7.  **The Resurrection:** Temporal notices the server crashed. It spins up a new pod. It skips Step 1, 2, 3, and 4 because they are already saved in the database. It reconnects to the MicroVM, waits for `create-next-app` to finish, and wakes up LangGraph.

### The Analogy: The Architect and the General Contractor
*   **LangGraph is the Architect:** They look at the blueprints, decide what room needs to be built next, and realize they made a mistake and need to redraw the stairs.
*   **Temporal is the General Contractor:** They don't know how to draw blueprints. But they make sure the workers show up every day, they buy the concrete, and if a worker gets sick, they hire a new one so the building *always* gets finished.

### Summary
*   Use **LangGraph** to stop the LLM from hallucinating and to force it into a structured *Think/Act/Observe* loop.
*   Use **Temporal** to stop the *Agent Process* from crashing, timing out, or losing its place during a 72-hour task.
