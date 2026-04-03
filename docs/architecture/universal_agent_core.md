# The Universal Agent Core (Beyond Coding)

While `open-swe` and `OpenClaw` were primarily designed around software engineering and specialized messaging, our new **AgentHood** is a **Universal Assistant**. It is not hardcoded for Git, GitHub, or React. It is a general-purpose reasoning engine.

We are *not* replicating OpenClaw's feature set. We are extracting the **Core Mechanics of Orchestration** and building a system where tools are completely pluggable.

## 1. The Agnostic State Machine (The Core)
The core of the system doesn't know if it is booking a flight, writing code, or analyzing a legal contract. It only knows the `Think -> Act -> Observe` loop.

*   **The Brain:** The LangGraph logic is identical regardless of the task. It looks at the `System Prompt`, reads the `Scratchpad`, and outputs a `ToolCall`.
*   **The Error Handler:** The `ToolErrorMiddleware` catches *any* error from *any* tool and feeds it back to the agent: *"Tool X failed with error Y. Try again."*

## 2. Pluggable Tools (Model Context Protocol)
We will not hardcode tools into the agent. Instead, we will use the **Model Context Protocol (MCP)** or a similar dynamic registry.

*   **The Tool Registry:** When the Go Receptionist creates a new Task in Postgres, it assigns a `Skillset` to the Python Worker (e.g., `[browser, flight_search, calendar]`).
*   **Dynamic Injection:** When the Python Worker wakes up, it queries the Tool Registry and injects *only* those specific tools into its LangGraph state machine for that run.
*   **Universality:** Tomorrow, if we want the agent to control a smart home, we don't change the agent's core logic. We just write a new `SmartHomeTool` and assign it to the worker.

## 3. The Universal Sandbox
The Ephemeral VM (Daytona/Docker) is not just for compiling code. It is a universal execution environment.

*   **Data Science:** The agent can spin up a VM, pip install `pandas` and `matplotlib`, download a massive CSV, generate a chart, and send the image back.
*   **Web Automation:** The agent can spin up a VM with a headless Chrome browser (Playwright/Puppeteer) to log into a website, scrape data, and destroy the VM to wipe the cookies.
*   **Media Processing:** The agent can spin up a VM with `ffmpeg` to transcode a video the user uploaded via Telegram.

## 4. The Receptionist's True Role (Intent Classification)
The Go Receptionist's most crucial job is **Classification**.

1.  **User:** "Hey, summarize this 100-page PDF and email the summary to John."
2.  **Receptionist (Go):** Uses a fast, cheap LLM just to route the intent.
    *   *Classification:* Document Analysis + Email.
    *   *Required Tools:* `[pdf_reader, gmail_sender]`.
    *   *Required Environment:* No VM needed (pure API calls).
3.  **The Dispatch:** The Receptionist writes the task to Postgres. A Python Worker claims it, injects the `pdf_reader` and `gmail_sender` tools, and completes the task in seconds.

## Conclusion
By stripping away the hardcoded software-engineering logic of `open-swe` and the rigid channel-bindings of `OpenClaw`, we are left with a pure, scalable **Orchestration Engine**.

The AgentHood is a blank slate. Its power comes from the fact that it can reliably run *any* sequence of tools for hours without crashing or losing context.
