# 🏥 Appointment Assistant System
### Mojisola Akinniyi Medical Office
**Intelligent Middleware-Driven Appointment Orchestration using LangGraph + OpenAI**

---

## 📌 Project Overview

This project is a production-grade, AI-powered Appointment Assistant System 
designed and implemented as the final project for **MBAN 5510 — AI Systems and 
Agentic Workflows**.

The system demonstrates middleware-driven orchestration using **LangGraph** as 
a stateful workflow engine, with **Human-in-the-Loop (HITL)** review as a core 
governance control. It simulates how an intelligent agent can responsibly manage 
patient appointment interactions in a medical office setting — handling requests, 
enforcing safety boundaries, masking sensitive data, and ensuring no patient-facing 
response is sent without human authorisation.

> **Design Philosophy:** Safety is not a feature added at the end. It is the architecture.

---

## 🎯 Supported Request Types

| Intent | Description |
|---|---|
| `book` | Book a new appointment from available slots |
| `view_appointment` | View existing appointment details |
| `view_slots` | Browse all available appointment slots |
| `reschedule` | Reschedule an existing appointment to a new date and time |
| `cancel` | Cancel an existing appointment |
| `prep` | Get preparation instructions for an appointment type |
| `emergency` | Detected automatically — immediately directs patient to call 911 |
| `medical_advice` | Detected automatically — politely declined and referred to a doctor |

---

## 🏗️ System Architecture
```
User Input (CLI)
      ↓
[input_node] → Middleware checks (PII masking, moderation, tool limits)
      ↓
[intent_node] → GPT classifies intent and extracts entities
      ↓
[action_node] → Executes the appropriate tool
      ↓
[hitl_node] → Human reviews, approves, edits or rejects draft response
      ↓
[output] → Final status + patient response + execution trace
```

### Routing Logic

| Condition | Route |
|---|---|
| Emergency detected | → `emergency_node` (bypasses all processing) |
| Medical advice request | → `medical_advice_node` (immediate safe decline) |
| Middleware blocked | → `escalate_node` |
| Missing information | → `needs_info_node` |
| Successful action | → `hitl_node` → END |

---

## 🛡️ Middleware Components

The system implements a custom middleware stack that runs on every request:

| Middleware | Purpose |
|---|---|
| `PIIMiddleware` | Detects and masks phone numbers, emails, SSNs, and dates of birth |
| `ModerationMiddleware` | Blocks harmful or inappropriate keywords before reaching the LLM |
| `ToolCallLimitMiddleware` | Prevents infinite loops by capping tool calls at 5 per run |
| `RetryMiddleware` | Automatically retries failed tool calls up to 3 times |

All middleware runs **before** any LLM call, ensuring clean, safe inputs at every stage.

---

## 🔄 Human-in-the-Loop (HITL) Workflow

The HITL node is a mandatory checkpoint in every successful request flow.

**How it works:**
1. The system executes the requested action (book, cancel, reschedule, etc.)
2. GPT generates a professional draft response for the patient
3. The workflow **pauses** and presents the draft to the human reviewer
4. The reviewer chooses one of three options:
   - **[1] Approve** — response is sent as-is
   - **[2] Edit** — reviewer types a revised response which is used instead
   - **[3] Escalate** — request is escalated to a senior agent
5. Only after explicit human authorisation does the system produce a final output

> No patient-facing message is ever sent without human review.
> This is a hard architectural constraint, not a soft guideline.

---

## 📊 Final Status Codes

| Status | Meaning |
|---|---|
| `READY` | Request completed successfully and approved by human reviewer |
| `NEED_INFO` | More information is required from the patient to proceed |
| `ESCALATE` | Request escalated due to safety trigger, policy limit, or human rejection |

---

## 🗂️ Project Structure
```
appointment-assistant/
├── main.py            # CLI entry point — run the system end-to-end
├── graph.py           # LangGraph workflow — all nodes, routing, and HITL
├── tools.py           # Appointment tools (book, cancel, reschedule, etc.)
├── middleware.py      # Safety and control middleware stack
├── data.py            # Appointment database and available slots
├── hitl.py            # Logging, run ID generation, and trace writer
├── logs/              # Auto-generated execution traces (JSON)
├── .env               # Environment variables (NOT committed to GitHub)
├── .gitignore         # Ensures secrets are never committed
└── README.md          # This file
```

---

## ⚙️ Environment Setup

### Requirements
- Python 3.10 or higher
- An OpenAI API key (GPT-4o-mini)

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/EmjayAkinniyi/appointment-assistant.git
cd appointment-assistant
```

**2. Create and activate a virtual environment**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python -m venv venv
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install langgraph langchain langchain-openai python-dotenv
```

**4. Configure environment variables**

Create a `.env` file in the root directory:
```
OPENAI_API_KEY=your-openai-api-key-here
```
> ⚠️ Never commit your API key. The `.gitignore` file ensures `.env` is excluded.

---

## 🚀 How to Run
```bash
python main.py
```

### Example Commands to Try
```
Show me my appointments
What slots are available?
Book slot SLT002 for John Davis
Reschedule APT001 to 2026-03-20 at 11:00 AM
Cancel appointment APT002
Get prep instructions for APT003
I have chest pain                     ← triggers emergency handling
What medication should I take?        ← triggers medical advice decline
```

---

## 🧪 Example End-to-End Run
```
MOJISOLA AKINNIYI MEDICAL OFFICE
Appointment Assistant System

Your request: Cancel appointment APT002

[Run ID: RUN_20260224_144144_3d1482ef]
INFO | [Node: input] Processing user input
INFO | [Node: intent] Intent=cancel | APT=APT002
INFO | [Node: action] Executing tool
INFO | [Node: hitl] Awaiting human review

--- HUMAN-IN-THE-LOOP REVIEW ---
Draft: "Dear John Davis, your appointment APT002 has been 
successfully cancelled..."

Your choice (1/2/3): 1
Response approved.

FINAL STATUS  : READY
ROUTE TAKEN   : input_node → intent_node → action_node → hitl_node
TRACE SAVED   : logs/trace_RUN_20260224_144144_3d1482ef.json
```

---

## 🔒 Safety and Governance Design

This system was designed with the following non-negotiable safety principles:

**1. No clinical advice** — The system immediately declines any request that 
resembles a medical diagnosis or treatment recommendation and directs the 
patient to a qualified physician.

**2. Emergency-first routing** — Emergency keywords trigger an immediate 
bypass of all normal processing. The patient receives a 911 directive 
before any other action.

**3. PII protection** — Patient phone numbers, emails, SSNs, and dates of 
birth are masked automatically before any data reaches the LLM.

**4. Human authorisation required** — Every patient-facing response requires 
explicit human approval. The system cannot auto-send.

**5. Full auditability** — Every run produces a timestamped JSON trace log 
recording the run ID, route taken, final status, intent, and HITL outcome.

---

## 📁 Execution Trace Example

Every run automatically saves a trace file to `logs/`. Example:
```json
{
  "run_id": "RUN_20260224_144144_3d1482ef",
  "timestamp": "2026-02-24T14:41:44.483Z",
  "final_status": "READY",
  "intent": "cancel",
  "route_taken": ["input_node", "intent_node", "action_node", "hitl_node"],
  "tool_calls": 1,
  "pii_in_input": "none",
  "appointment_id": "APT002",
  "middleware_passed": true,
  "hitl_approved": true,
  "final_response": "Dear John Davis, your appointment APT002 has been successfully cancelled..."
}
```

---

## 🧠 Design Decisions

**Why LangGraph?**
LangGraph provides native support for stateful, conditional workflows with 
clear node-based architecture. This makes the execution path fully traceable 
and the routing logic explicit — critical for a governance-sensitive application.

**Why HITL as a hard constraint?**
In healthcare contexts, an automated response sent without review could cause 
harm. HITL is not optional in this system — it is a mandatory architectural node 
that cannot be bypassed for any successful action.

**Why custom middleware instead of passthrough?**
Each middleware component addresses a specific governance concern: data privacy 
(PII), content safety (moderation), and operational control (rate limiting). 
Keeping them modular makes them independently testable and replaceable.

---

## 👩‍💻 Author

**Mojisola Akinniyi**  
MBAN Candidate | Business Consultant | AI Systems Designer  
Bridging analytical rigour with practical AI implementation across 
Accounting, Auditing, HR, Business Consulting, and Entrepreneurship.

🔗 [GitHub](https://github.com/EmjayAkinniyi) | 
[LinkedIn](https://www.linkedin.com/in/your-linkedin-here)

---

## 📄 License

This project is submitted as academic work for MBAN 5510.  
All rights reserved © 2026 Mojisola Akinniyi.