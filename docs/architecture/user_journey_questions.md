# Building the AgentHood Skeleton: The User Journey

To build the foundation of our new AI SaaS (inspiring from OpenClaw and open-swe, but without relying on heavy enterprise tools like Temporal just yet), we must define exactly how the system behaves from the user's perspective.

Here are the critical questions and answers defining the skeleton of our AgentHood when "I" (the user) interact with it.

---

### 1. How do I start a task?
**Question:** If I am on my phone on Telegram, how do I tell the system to build a Next.js app without it trying to write the code directly in the chat?
**Answer:** You message the **Receptionist Agent**. The Receptionist has a strict prompt: *Never write code.* Its only job is to extract intent. It parses your message, creates a JSON payload (`{"task": "Build Next.js app", "type": "coding"}`), inserts a row into the database (`Task Status: Queued`), and replies to you: *"I've put a coding team on this. I will let you know when they have an update."*

### 2. Where does the code actually run?
**Question:** When the Worker Agent starts, where does it type `npm install`?
**Answer:** The Orchestration layer reads the new Task from the database. It hits an API (like Daytona or a custom Docker daemon) to provision a fresh, ephemeral Ubuntu VM. It injects a tiny Python script (the "Sandbox Bridge") into the VM. The Worker Agent sends bash commands to this bridge, not to your local laptop.

### 3. How do I check on the task 30 minutes later?
**Question:** I am waiting for the app. How do I know it hasn't crashed?
**Answer:** You text the Receptionist: *"Status update?"*. The Receptionist queries the central database for your active tasks. It sees the Coding Agent's last logged milestone (`"Status: Debugging React Router"`). The Receptionist replies: *"They are currently debugging a routing issue. Want me to interrupt them?"*

### 4. What happens if the agent gets stuck in a loop?
**Question:** The agent keeps running a python script, getting a syntax error, and running it again without fixing it. How do we prevent this?
**Answer:** The Sandbox Bridge hashes the last 3 bash outputs. If `hash(output 1) == hash(output 3)`, it flags a "Loop Detected" event. The Orchestration layer forces the agent to stop executing bash. It forces the agent into a "Reflection Node" (LangGraph) where it must write an `inner_monologue` explaining why it failed and proposing a radically different approach.

### 5. How do I interact with the agent while it is working?
**Question:** I forgot to tell the agent to use Tailwind CSS. Can I tell it while it is coding?
**Answer:** Yes. You text the Receptionist: *"Tell the coding team to use Tailwind."* The Receptionist appends this message to the **Global Scratchpad**. The next time the Worker Agent finishes its current step and checks the scratchpad to plan its next move, it sees the new constraint and adjusts its plan.

### 6. What if the agent needs my password to an API?
**Question:** The agent needs an OpenAI API key to build my app. How does it get it without me hardcoding it in the prompt?
**Answer:** The Worker Agent halts and emits a `USER_INPUT_REQUIRED` event. The Receptionist gets this event and texts you: *"The dev team needs your OpenAI API key to proceed. Please reply with it."* When you reply, the Receptionist encrypts it and injects it securely into the ephemeral VM's environment variables. The Worker Agent resumes.

### 7. How does the agent know when it is finished?
**Question:** How does the agent not just keep endlessly tinkering?
**Answer:** The Worker Agent has a specific "Done" tool (e.g., `submit_pr` or `finish_task`). In its LangGraph logic, it is explicitly prompted to evaluate its work against the original Mission Brief. Once it calls `finish_task`, the Orchestration layer destroys the Ephemeral VM, saves the final code to GitHub/Cloud Storage, and the Receptionist texts you the link.

### 8. Can I have two different tasks running at once?
**Question:** Can I ask it to code an app, and also ask it to research flights to Tokyo at the same time?
**Answer:** Yes. The Receptionist simply creates two separate rows in the Task database. It spins up a Coding Worker (with a Linux VM) and a Research Worker (with a Headless Browser). They operate completely independently.

### 9. How do we keep the LLM context window from exploding?
**Question:** If the agent reads a 10,000-line log file, won't the next prompt fail because it's too big?
**Answer:** The agent never puts the raw log file in its active context. If it runs a command with huge output, the Sandbox Bridge truncates the output in the prompt (e.g., showing the first 50 and last 50 lines). If the agent needs to read the whole file, it uses a `grep` tool or an `ask_questions_about_file` tool to extract only what it needs.

### 10. What happens if the server hosting the AgentHood crashes?
**Question:** I don't want to use Temporal yet. If our Node/Python orchestrator restarts, do all the running agents die?
**Answer:** Without Temporal, we build a basic State Machine in our database (e.g., SQLite). Every time the agent transitions a node in LangGraph (e.g., from `Thinking` to `Executing`), we update the DB row: `{"current_node": "Executing", "last_bash_cmd": "npm start"}`. If the server restarts, our boot script reads the DB, sees tasks in "Executing", reconnects to the Ephemeral VMs (which are still running), and re-triggers the LangGraph loop from the last known state.

---

### The Skeleton Derived from these Questions:
1.  **The API Gateway (Fast/Stateless):** Receives Telegram/Web messages. Hosts the Receptionist.
2.  **The Database (Stateful):** Stores Users, Active Tasks, Global Scratchpads, and LangGraph checkpoints.
3.  **The Orchestrator (The Loop):** A background worker that pulls Active Tasks from the DB and runs the LangGraph step.
4.  **The Infrastructure Manager:** An API client that talks to Daytona/Docker to spin up, pause, or kill VMs on demand.
