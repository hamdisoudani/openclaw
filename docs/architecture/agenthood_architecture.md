# The "AgentHood": A General-Purpose SaaS AI OS

The architecture of this AI system extends far beyond software engineering (like `open-swe`). It is an **"AgentHood"**—a dynamic, general-purpose agency that lives in the cloud, capable of handling personal tasks, deep research, and complex coding simultaneously.

## 1. The Receptionist (The Omni-Supervisor)
The user interacts entirely with **The Receptionist**. This agent is incredibly fast, context-aware, and highly personable.

*   **The Single Point of Contact:** Whether the user sends a WhatsApp voice note, a Telegram message, or clicks a button on the Web UI, The Receptionist answers instantly.
*   **The Triage Engine:** The Receptionist's primary job is *not* to solve complex problems. Its job is to:
    1.  Acknowledge the user's request.
    2.  Classify the domain (Coding, Web Research, Calendar/Email, Data Entry).
    3.  Spin up the appropriate specialized "Worker Agent".
    4.  Put the task in the background.

## 2. The Worker Guilds (Domain Experts)
The Receptionist dispatches tasks to different "Guilds" depending on the requirement:

*   **The Coding Guild:** Operates as described previously. Spins up Ephemeral VMs (like Daytona), uses LangGraph state machines to write code, test it, and open PRs.
*   **The Deep Research Guild:** Uses "browser" and "web_fetch" tools. If the user asks, *"Research the top 10 CRM tools for a small logistics company and make a comparison table,"* this Worker can browse the web for hours, read dozens of pages, and compile a comprehensive report without timing out the user's chat session.
*   **The Executive Assistant Guild:** Has OAuth access to the user's Gmail, Google Calendar, and Notion. It can read unread emails, draft replies, and schedule meetings.

## 3. Global State Awareness (The "Dashboard")
The essential magic of the AgentHood is that **The Receptionist always knows what is running in the background.**

*   **The Task Registry (Database):** Every time a Worker is spawned, a record is created in a central database (e.g., PostgreSQL or SQLite):
    *   `Task ID: 8912`
    *   `Worker: Research-04`
    *   `Status: Reading G2 Reviews...`
    *   `Progress: 40%`
*   **Real-Time Polling:** When the user texts The Receptionist: *"What are you working on right now?"*
    *   The Receptionist instantly queries the Task Registry.
    *   *Response:* "Right now, the Research team is halfway through the CRM comparison table, and the Coding team just opened a Pull Request for the new login page. I'm also waiting for your approval on a draft email to John."
*   **Background Interruptions:** If the user says, *"Cancel the CRM research, I changed my mind,"* The Receptionist sends a `SIGTERM` or an `INTERRUPT` event via the Event Bus directly to the active Research Worker, instantly halting the background job and destroying its temporary VM/browser session.

## 4. The User Experience (Seamless Multitasking)
The AgentHood allows the user to treat the AI like a massive human agency.

1.  **User:** "Hey, build a Python script to scrape this website, also book me a flight to NYC next Tuesday, and summarize the PDF I just sent."
2.  **Receptionist:** "You got it. I've sent the PDF summary request to the Reader, the Python script to the Dev Team, and I'm looking up flights now."
3.  *(5 seconds later)* **Receptionist:** "Here is the summary of the PDF..."
4.  *(2 minutes later)* **Receptionist:** "I found 3 flights to NYC. Which do you prefer?"
5.  *(1 hour later)* **Receptionist:** "The Dev Team finished the Python scraper. I've attached the `scraper.py` file."

## Summary
The AgentHood architecture shifts the AI paradigm from a "smart chatbot" to a **Massively Parallel Agency**.
By separating the fast, conversational **Receptionist** from the slow, heavy-lifting **Workers**, and using a **Task Registry** for global state awareness, the system can handle coding, research, and personal assistance flawlessly, concurrently, and for days at a time.
