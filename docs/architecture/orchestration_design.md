# Solving the Orchestration Challenge: Supervisor & Subagent Communication

The true challenge of a SaaS AI Operating System isn't spinning up VMs; it's **Orchestration**. How does a Supervisor manage 10 subagents working asynchronously for 3 days without context collapse, getting stuck in loops, or constantly bothering the user?

This document outlines the technical design for a state-of-the-art orchestration layer, replacing simple linear chat logs with an Event-Driven State Machine.

## 1. The Core Architecture: The Event Bus
Instead of parent/child API calls (which block and timeout), all agents communicate via an **Event Bus** (e.g., Redis Pub/Sub, Kafka, or an internal SQLite event queue like in OpenClaw).

*   **Asynchronous by Default:** When the Supervisor assigns a task (e.g., `{"type": "TASK_ASSIGNED", "agent": "frontend-01", "task": "Build React Navigation"}`), it does *not* wait for an HTTP response. It goes to sleep.
*   **Heartbeats:** Every active subagent must emit a `HEARTBEAT` event every 30 seconds.
    *   *If a heartbeat dies:* The VM crashed. The Supervisor provisions a new VM and restores the agent's last known state.
*   **Milestone Broadcasts:** When `frontend-01` finishes a component, it emits a `MILESTONE_REACHED` event. The Supervisor wakes up, reads the event, and updates its internal DAG (Directed Acyclic Graph) of the project.

## 2. Preventing Context Collapse (The "Scratchpad" vs "Chat Log")
If an agent works for 3 days, appending every bash command and error log to its context window will cause it to forget its original goal and hallucinate (Context Collapse).

*   **The Global Scratchpad:** The Supervisor maintains a central JSON document (The Scratchpad) for the project. It contains:
    1.  The Overall Goal.
    2.  The Current Plan (Step 1, Step 2, Step 3).
    3.  A summary of what has been completed.
*   **Subagent Amnesia (The "Goldfish" Pattern):** A subagent's actual context window is kept incredibly short. It only sees:
    1.  The Global Scratchpad.
    2.  Its specific current sub-task (e.g., *"Fix the type error on line 42"*).
    3.  The last 5 bash commands/outputs.
*   **State Condensation:** If a subagent tries to fix a bug 10 times, the orchestration layer intercepts the 11th turn. It takes the previous 10 turns, passes them to a cheap, fast LLM (like Claude 3 Haiku or GPT-4o-mini) to summarize: *"The agent tried to update React Router 3 times, but encountered dependency conflicts. It is currently stalled."* This summary replaces the 10 raw turns in the context window.

## 3. Monitoring and Interruptions (Stuck Loops)
The Supervisor acts as the system's "Prefrontal Cortex," monitoring for loops and anomalies.

*   **The Loop Detector:** The orchestration layer hashes the semantic meaning of the subagent's last 5 actions. If `hash(action_n) == hash(action_n-2)`, the agent is stuck in a loop (e.g., running `npm install`, getting an error, running `npm install` again).
*   **The "Tap on the Shoulder":** When a loop is detected, the Supervisor emits an `INTERRUPT` event. The subagent is forced to stop.
    *   The Supervisor injects a system prompt: *"You have been trying the same approach and failing. Stop what you are doing. Formulate a completely different approach, or declare you are blocked."*
*   **Escalation:** If the subagent declares it is blocked, the Supervisor can reassign the task to a "Senior Architect" agent or send a structured message to the human user via WhatsApp: *"Frontend-01 is blocked on a Webpack configuration error. Here is the summary. Should I let it keep trying, or do you want to intervene?"*

## 4. Multi-Agent Collaboration (The "PR Review" Model)
How do 10 agents work together without stepping on each other's toes? They don't edit the same files at the same time. They use Git.

1.  **Isolation:** `frontend-01` works on branch `feature/nav`. `backend-01` works on `feature/api`.
2.  **The Handoff:** When `backend-01` finishes the API, it opens a Pull Request (via an MCP Tool). It emits a `PR_OPENED` event.
3.  **The Reviewer:** The Supervisor sees the event and wakes up `qa-tester-01`. The QA tester pulls the branch, runs the tests in a fresh Ephemeral VM, and uses a Vision model to look at the rendered frontend.
4.  **Feedback:** If the tests fail, `qa-tester-01` leaves a comment on the PR. `backend-01` sees the comment, wakes up, and pushes a fix.

This mimics human software engineering teams. It provides a highly structured, auditable, and asynchronous way for multiple agents to collaborate without requiring complex, fragile "agent-to-agent direct messaging" protocols.

## Summary
By combining an **Event Bus**, **Context Condensation**, **Loop Detection**, and a **Git-based Collaboration Model**, the Supervisor can orchestrate a massive swarm of agents for weeks at a time. The human user simply receives high-level status updates on their phone, completely insulated from the chaos of the actual execution.
