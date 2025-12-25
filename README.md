# GPA (Group Project Agent) 🎓

> **"Automating the friction of group projects with Automata Theory & LLMs."**

**GPA** is an intelligent agent designed to streamline the chaotic "kickoff" phase of university group projects. By modeling administrative workflows as a **Deterministic Finite Automaton (DFA)**, this tool orchestrates the entire process—from analyzing assignment requirements to establishing collaborative workspaces—eliminating the initial friction of teamwork.

Developed for the **Theory of Computation** course at **National Cheng Kung University (NCKU)**.

---

## 💡 Background & Motivation

**The "Cold Start" Problem in General Education Courses**

In General Education (通識) courses, students are often assigned to interdisciplinary teams where members are strangers. The traditional initiation process is friction-heavy and inefficient:
1.  Awkwardly exchanging messaging app IDs (Line/IG).
2.  Creating chat groups manually.
3.  Asking for Student IDs one by one.
4.  Manually creating and sharing Google Docs/Slides links.

**GPA** solves this by automating the entire loop. Students simply input their **Student IDs** during class, and the Agent takes over: parsing the assignment, creating the workspace, and emailing every member with their tasks and access links instantly.

---

## 🎨 Design Philosophy

### Why not just use a shared Google Slide manually?

While a shared document is sufficient *once collaboration has already started*, this project focuses on automating the **initiation phase** of group work. This phase is often the most fragile and delay-prone stage, especially among students who are unfamiliar with each other.

**From Implicit to Explicit Coordination:**
By modeling the project startup process as a finite-state machine, this agent:
* Reduces **social friction** (no need to chase people for emails).
* Enforces **synchronization** (everyone receives the same info at the same time).
* Transforms implicit, human-dependent coordination into an **explicit, reproducible computational workflow**.

---

## ✨ Key Features

* **🤖 LLM-Powered Analysis**: Utilizes NCKU's internal LLM API (GPT-OSS/Llama 3) to parse PDF assignment guidelines and extract actionable tasks.
* **📄 Multi-Modal Output**:
    * **Google Docs**: Generates a comprehensive project proposal and task breakdown.
    * **Google Slides**: Creates a structured presentation outline for the project.
* **☁️ Google Workspace Automation**:
    * **Smart Identity Resolution**: Automatically converts Student IDs into official university email addresses.
    * **Drive & Gmail**: Automatically creates files, manages permissions, and sends kickoff emails.
* **⚡ State Visualization**: Visualizes the agent's workflow as a Directed Acyclic Graph (DAG) in real-time.

---

## 🧠 System Architecture (Automata Theory)

The agent operates as a robust state machine ($M$) where:

* $Q$ (States): `{Start, Analyze, Create_Doc, Create_Slide, Set_Permission, Notify, End, Error_State}`
* $\Sigma$ (Alphabet): `{User_Input, PDF_Content, API_Response}`
* $\delta$ (Transition Function): The logic defined in `main.py` ensuring a strictly ordered execution sequence.

### Error Handling as States
Unlike traditional scripts that crash on exception, **Failures are explicitly modeled as states ($Q_{err}$) rather than implicit exceptions.**
* If an API call (e.g., LLM timeout) fails, the system transitions to a specific error handling state to attempt recovery or graceful degradation, rather than terminating the process abruptly.

```mermaid
graph LR
    A((Start)) --> B[LLM Analysis]
    B --> C{Output Selection}
    C -->|Docs| D[Create G-Doc]
    C -->|Slides| E[Create G-Slide]
    D --> F[Set Permissions]
    E --> F
    F --> G[Send Email]
    G --> H(((End)))
    B -.->|Timeout| X[Error State]
    X -.->|Retry| B
