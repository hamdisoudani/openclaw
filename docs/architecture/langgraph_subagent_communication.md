# Deep Dive: Subagent Message Interception (The open-swe Pattern)

When building an autonomous agent that runs for hours (like `open-swe` or our proposed AgentHood), a critical problem arises: **If the agent is deep inside a `while (true)` reasoning loop, how do you talk to it?**

If the agent is currently compiling code, and the user sends a message saying, *"Wait, use Tailwind CSS instead,"* how does the agent receive that message *without* needing to stop and restart the entire job?

In `open-swe`, this is solved brilliantly using **LangGraph's Store and Middleware**.

## The Two Halves of the Pattern

### 1. The Webhook (The Sender)
When a user sends a new message (e.g., a GitHub comment or a Slack message) while the agent is already working, the webhook server receives it.

Instead of trying to "interrupt" the active Python thread (which is dangerous and complicated), the webhook server simply **queues the message in the database.**

In `open-swe` (`agent/webapp.py`), this looks like:
```python
# Find the LangGraph thread ID associated with this issue
thread_id = get_thread_id()

# Use the LangGraph Store API to append the message to the "pending_messages" queue
langgraph_client.store.put_item(
    namespace=("queue", thread_id),
    key="pending_messages",
    value={"messages": [...]}
)
```
The webhook server instantly responds `200 OK`. It is not blocked by the working agent.

### 2. The Middleware (The Receiver)
The agent is currently spinning in its LangGraph loop: `Think -> Act -> Observe -> Repeat`.

Before the agent makes its *next* call to the LLM (the `Think` phase), it hits a piece of **Middleware**. In `open-swe`, this is defined in `agent/middleware/check_message_queue.py` using the `@before_model` decorator.

```python
@before_model(state_schema=LinearNotifyState)
async def check_message_queue_before_model(state, runtime):
    # 1. Check the database for pending messages
    queued_item = await store.aget(("queue", thread_id), "pending_messages")

    if not queued_item:
        return None # No new messages, continue normally.

    # 2. Extract the messages and immediately delete them from the queue
    queued_messages = queued_item.value.get("messages", [])
    await store.adelete(("queue", thread_id), "pending_messages")

    # 3. INJECT the messages into the LangGraph state as if the user just typed them
    new_message = {
        "role": "user",
        "content": "Wait, use Tailwind CSS instead"
    }

    # 4. Return the new message to LangGraph, which appends it to the context window
    return {"messages": [new_message]}
```

## Why This Architecture is State-of-the-Art

This pattern completely eliminates the need for complex, concurrent inter-process communication (IPC), WebSockets, or a "Go Receptionist" holding the connection open.

1.  **It is 100% Asynchronous:** The user can send 50 messages while the agent is downloading an NPM package. All 50 messages queue up in the database.
2.  **It is Safe (No Race Conditions):** We don't interrupt the agent while it is executing a bash command. We wait until the bash command finishes, and *right before* it asks the LLM what to do next, we slide the new messages into its context window.
3.  **It is Natural for the LLM:** To the LLM, it just looks like the user typed a follow-up message:
    *   *System:* Bash command failed.
    *   *User:* Wait, use Tailwind CSS instead.
    *   *Agent:* Ah, I will update my plan to fix the error using Tailwind!

## Summary for AgentHood
We do not need a Go Receptionist to solve the "interrupt" problem. We simply need our Database (or Redis) to act as a **Mailbox**.

Any external event (User WhatsApp message, GitHub PR comment, Cron Job) simply drops a letter in the Mailbox. The LangGraph Worker Agent checks its Mailbox at the beginning of every turn. If there's a letter, it reads it, updates its plan, and continues working.
