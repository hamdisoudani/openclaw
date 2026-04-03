# Message Bus Evaluation: Postgres vs. Redis vs. NATS vs. Kafka

To orchestrate a massive swarm of autonomous agents, the "Message Bus" is the most critical piece of infrastructure. If the bus fails, the Go Supervisor cannot talk to the Python Workers.

In our previous technical design, we proposed **PostgreSQL** (via the "Mailbox Pattern" or `SKIP LOCKED`). However, when building a state-of-the-art system, we must ask the hard questions: **Why Postgres instead of Redis, NATS, or Kafka?**

## 1. PostgreSQL (The Mailbox Pattern)
*   **How it works:** Agents use `SELECT ... FOR UPDATE SKIP LOCKED` to pull tasks from a table.
*   **Pros:**
    *   Zero extra infrastructure. You already need Postgres for vector embeddings and user data.
    *   Perfect durability. If an agent crashes, the task is still in the DB.
    *   Easy to query (e.g., "Show me all running tasks").
*   **Cons:**
    *   **Polling overhead.** Workers have to constantly poll the DB every 1 second. With 10,000 agents, this kills the database CPU.
    *   Postgres is not built to be a high-throughput pub/sub system.

## 2. Redis (Pub/Sub & Streams)
*   **How it works:** Supervisor publishes events (`TASK_ASSIGNED`) to a Redis Stream. Workers listen via Consumer Groups.
*   **Pros:**
    *   Extremely low latency (sub-millisecond).
    *   Consumer Groups automatically handle worker crashes (unacknowledged messages can be reclaimed).
    *   No polling required; workers block and wait for new messages instantly.
*   **Cons:**
    *   Redis is primarily an in-memory datastore. While it has persistence (AOF/RDB), it is not as bulletproof as Postgres for long-term state.
    *   Requires managing a separate piece of infrastructure.

## 3. NATS (JetStream)
*   **How it works:** A highly specialized, ultra-lightweight Go-based messaging system.
*   **Pros:**
    *   **The absolute best tool for the job.** It is built specifically for microservices to talk to each other.
    *   JetStream provides perfect durability (like Kafka) but with the operational simplicity of Redis.
    *   True "Push" model. The Go Supervisor sends an event, NATS immediately pushes it to a waiting Python worker.
*   **Cons:**
    *   Slight learning curve if the team is not familiar with NATS JetStream concepts.

## 4. Kafka
*   **How it works:** An enterprise-grade, distributed event streaming platform.
*   **Pros:** Infinite scalability. If you have 10 million agents generating 1 billion logs a day, Kafka will not blink.
*   **Cons:** **Overkill.** Kafka requires ZooKeeper (or KRaft), massive JVM memory footprints, and heavy operational overhead. It is terrible for a lightweight "SaaS in a Docker Compose" setup.

---

## Conclusion & The Winning Choice

If we look at OpenClaw's current source code, it uses simple in-memory queues and JSON file writing (`src/commands/status.scan.json-core.ts`, `src/agents/subagent-announce-queue.ts`). This works for a local CLI, but **fails in a distributed SaaS environment**.

To build a true, scalable AgentHood, we must transition to a dedicated broker.

### The Hybrid Approach (Postgres + Redis/NATS)
The most robust, state-of-the-art architecture uses **two** systems:
1.  **Postgres** is the *Source of Truth*. It stores the ultimate state of the task (`IN_PROGRESS`, `COMPLETED`), the LangGraph checkpoints, and the global scratchpad.
2.  **Redis (or NATS)** is the *Nervous System*. When the Go Supervisor wants an agent to start, it inserts the row into Postgres, AND publishes an event to Redis (`NEW_TASK: uuid-1`).

**Why this is perfect:**
The Python workers connect to Redis and *block* (sleep). They consume 0 CPU. The millisecond the Go Supervisor publishes to Redis, the Python worker wakes up, reads the `uuid-1` from Redis, queries Postgres for the full prompt, and starts the LangGraph loop.

We get the **durability of Postgres** without the **CPU-killing polling**, thanks to the **zero-latency of Redis/NATS**.
