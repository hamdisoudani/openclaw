# AgentHood Feature Blueprint (OpenClaw + open-swe)

This document catalogues every major feature extracted from reading both `open-swe` and `OpenClaw` from A to Z. For each feature, we detail the current implementation and how we will improve it in our new, high-performance Go/Python/Docker stack.

## 1. The Gateway / Webhook Server
**Current Implementation (OpenClaw & open-swe):**
*   *open-swe:* Uses a Python FastApi/Flask (`agent/webapp.py`) server to receive GitHub/Linear webhooks. It pushes state directly to LangGraph using Python client libraries.
*   *OpenClaw:* Uses a massive Node.js Express server (`src/gateway/server.impl.ts`) to handle WebSockets, SSE, and HTTP endpoints for Telegram, WhatsApp, Discord, etc.
**The Better Technique (AgentHood):**
*   **Go Fiber/Gin Server.** We will replace both with a single, highly concurrent Go server. It will act *only* as a reverse proxy and webhook receiver. When it receives a Slack/Telegram message, it validates the payload, transforms it into a standard JSON event, and pushes it to PostgreSQL. It does 0 AI reasoning.

## 2. Tool Execution & Cloud Sandboxes
**Current Implementation (OpenClaw & open-swe):**
*   *open-swe:* Uses `LangSmithBackend` or `E2B` (`agent/integrations/langsmith.py`). The Python agent sends bash commands via API over the internet to a cloud VM.
*   *OpenClaw:* Uses `src/agents/sandbox/fs-bridge.ts` and `docker-manager.ts` to spin up local Docker containers on the user's laptop.
**The Better Technique (AgentHood):**
*   **Daytona SDK via Python Worker.** We will not run code on the user's machine. The Python Worker Daemon will use a Sandbox SDK (like Daytona or E2B) to provision isolated, ephemeral VMs in the cloud. We will wrap tools like `read_file`, `write_file`, and `run_bash` to execute exclusively over this SDK.

## 3. GitHub / Source Control Integration
**Current Implementation (OpenClaw & open-swe):**
*   *open-swe:* Highly specialized tools (`agent/tools/commit_and_open_pr.py`, `github_comment.py`, `github_review.py`). The agent knows exactly how to clone, read diffs, and interact with the GitHub API.
*   *OpenClaw:* Relies mostly on raw bash (`git diff`) executed locally by the agent.
**The Better Technique (AgentHood):**
*   **First-Class Native Tools.** We will adopt `open-swe`'s approach. We will build dedicated Python MCP Tools for GitHub (`create_pr`, `review_pr`, `read_issue`). This prevents the agent from making syntax errors while using raw `git` commands in the terminal and standardizes the output.

## 4. Multi-Channel Messaging (Slack, Telegram, WhatsApp)
**Current Implementation (OpenClaw & open-swe):**
*   *open-swe:* Hardcoded specifically for Linear issues and some Slack thread replies (`agent/tools/slack_thread_reply.py`).
*   *OpenClaw:* A masterpiece of multi-channel routing (`src/channels/telegram`, `src/channels/whatsapp`, etc.). It normalizes messages into a unified `ChatEnvelope`.
**The Better Technique (AgentHood):**
*   **The Omni-Channel Go Router.** We will extract OpenClaw's channel normalization logic and rewrite it in Go. The Python Worker Agent will never know if the user is on Telegram or WhatsApp. It will simply use a tool `reply_to_user("Task complete")`. The Go Gateway will read this from the DB and route it back to the correct specific WebSocket/Webhook for that user.

## 5. Context & Memory Management
**Current Implementation (OpenClaw & open-swe):**
*   *open-swe:* Relies on LangGraph Checkpointers (`langgraph_client.store`) to save the exact thread state to a DB.
*   *OpenClaw:* Uses `src/config/sessions/` to write massive JSON transcript files to the local disk.
**The Better Technique (AgentHood):**
*   **PostgreSQL Checkpointing + The "Goldfish" Reducer.** We will use Postgres to store the LangGraph state (like `open-swe`). However, we will improve it by adding a "Reducer Node" in LangGraph. Before saving the state, if the context exceeds 10,000 tokens, a fast LLM summarizes the last 5 turns into a "Scratchpad" string, drastically reducing DB size and LLM costs.

## 6. Interruptions & Mid-Task Instructions
**Current Implementation (OpenClaw & open-swe):**
*   *open-swe:* Uses the `check_message_queue_before_model` Middleware. Webhooks write to the DB. The agent reads the DB right before calling the LLM and injects the new message.
*   *OpenClaw:* Uses `src/agents/subagent-announce-queue.ts` in-memory.
**The Better Technique (AgentHood):**
*   **The Mailbox Middleware.** We will perfectly replicate the `open-swe` Middleware pattern. The Go Receptionist writes interrupts to Postgres. The Python Worker runs `@before_model` middleware to check Postgres. This allows the user to say *"Stop using Python, use Node instead"* without breaking the agent's execution loop.

## 7. Auth & Secrets Management
**Current Implementation (OpenClaw & open-swe):**
*   *open-swe:* Uses `agent/utils/auth.py` to resolve GitHub tokens specifically.
*   *OpenClaw:* Uses `src/secrets/runtime.ts` to manage API keys securely.
**The Better Technique (AgentHood):**
*   **Encrypted DB Vault + JIT Injection.** The Go server will store encrypted API keys (OpenAI, GitHub, Linear) in Postgres. When a Python Worker claims a task, the Go server decrypts the keys needed *just for that task* and injects them into the Ephemeral VM's environment variables. The Python worker never logs the raw keys.

## Conclusion
By stripping the heavy NodeJS routing from OpenClaw and merging it with the LangGraph/Cloud Sandbox architecture of open-swe, we create a system that is:
1. **Faster:** Go handles 10,000 webhooks a second.
2. **Smarter:** LangGraph prevents LLM hallucinations via strict state loops.
3. **Safer:** Daytona/E2B cloud sandboxes protect the host infrastructure.
