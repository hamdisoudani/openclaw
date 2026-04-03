# Roadmap: Building the Temporal-Backed AgentHood

Our goal is to evolve OpenClaw into a SaaS AgentHood capable of running tasks for 1 to 3 hours consecutively without memory leaks, context collapse, or dropped WebSocket connections.

To achieve this, we will transition from OpenClaw's current in-memory `subagent-spawn` logic to a **Durable Execution Engine (Temporal.io)** combined with **LangGraph** for reasoning and **Daytona** for ephemeral execution.

Here is the step-by-step implementation roadmap.

## Phase 1: The Temporal Foundation
**Goal:** Introduce Temporal into the OpenClaw codebase as the new orchestrator for background tasks.
*   **Step 1:** Set up a local Temporal cluster (via Docker Compose) in the `docker-compose.yml` file.
*   **Step 2:** Create a new directory `src/temporal/` to house our Workflows and Activities.
*   **Step 3:** Implement a basic `AgentWorkflow`. This workflow will simply accept a task string ("Research X"), wait 5 minutes (using `temporal.sleep`), and return a hardcoded result.
*   **Step 4:** Modify OpenClaw's `src/agents/subagent-spawn.ts`. Instead of calling `callSubagentGateway({ method: "agent", ... })`, the Gateway will now kick off the `AgentWorkflow` via the Temporal Client and immediately return an `accepted` status to the user.

*Outcome of Phase 1:* OpenClaw can kick off a background task that survives a server restart, even if the task takes 3 hours.

## Phase 2: LangGraph Integration (The Brain)
**Goal:** Replace the hardcoded Temporal Activity with a real LangGraph state machine.
*   **Step 1:** Define the LangGraph State (`AgentState`) in `src/temporal/activities/`. This state will track the `messages`, the `current_step`, and `errors`.
*   **Step 2:** Port the `open-swe` agent logic into a Temporal Activity. The Temporal Workflow will call `run_langgraph_step(currentState)`.
*   **Step 3:** Implement the "Goldfish" context pattern. When `run_langgraph_step` is called, it summarizes the last 10 messages into the `AgentState` so the LLM context window doesn't explode during a 3-hour run.
*   **Step 4:** The Activity queries the LLM (Claude/GPT-4) and returns the chosen `ToolCall` back to the Temporal Workflow.

*Outcome of Phase 2:* The agent can think and decide on actions, and its reasoning state is durably saved to the Temporal database after every single thought.

## Phase 3: Daytona VM Integration (The Hands)
**Goal:** Give the agent a safe, disposable place to run code.
*   **Step 1:** Build a new OpenClaw Tool: `DaytonaTool`.
*   **Step 2:** When LangGraph outputs a `ToolCall(run_bash, npm install)`, the Temporal Workflow intercepts it and calls a new Activity: `execute_in_daytona(command)`.
*   **Step 3:** `execute_in_daytona` uses the Daytona API to spin up a workspace (or connect to an existing one for this task ID), runs the command over SSH/WebSocket, captures the stdout, and returns it.
*   **Step 4:** The Temporal Workflow receives the stdout, updates the `AgentState`, and loops back to Phase 2 (calling `run_langgraph_step`).

*Outcome of Phase 3:* The agent can write and execute code in an isolated cloud VM without risking the host server.

## Phase 4: The Receptionist & State Awareness
**Goal:** Allow the user to interact with the system while jobs are running.
*   **Step 1:** Create the "Task Registry" database table (SQLite/PostgreSQL) to store the mapping between `OpenClaw Session ID`, `Temporal Workflow ID`, and `Current Status`.
*   **Step 2:** Update the Temporal Workflow to emit events (e.g., `UpdateTaskStatus(status="Compiling Next.js...")`) to the Task Registry.
*   **Step 3:** Implement a new tool for the Main Agent (The Receptionist) called `check_background_tasks`. When the user asks, "How is the coding going?", the Receptionist queries the Task Registry and replies with the live status from Temporal.
*   **Step 4:** Implement an `interrupt_task` tool so the user can cancel a 3-hour job mid-way through via Temporal's cancellation API.

*Outcome of Phase 4:* A fully functional "AgentHood" where the Receptionist tracks long-running Temporal workflows and keeps the user updated.

## Phase 5: Multi-Agent Collaboration (Optional / Future)
**Goal:** Allow multiple agents to work on the same codebase.
*   **Step 1:** Implement the `PR_OPENED` event listener in Temporal.
*   **Step 2:** When the Coder agent finishes a branch, Temporal kicks off a *new* Workflow: `QATesterWorkflow`.
*   **Step 3:** The QA Tester pulls the code into a fresh Daytona VM, runs tests, and leaves GitHub PR comments.

---
By following these 4 core phases, we safely migrate OpenClaw from an in-memory chat loop to an enterprise-grade, fault-tolerant SaaS AI platform.
