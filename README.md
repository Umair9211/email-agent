# 📧 Gmail Email Agent

An AI email assistant built with **LangChain / LangGraph**, **Gemini**, and the **Gmail API**. Chat with your inbox in plain English: list, search, read, draft and reply to emails. Anything that sends mail pauses for **your approval** first.

> Example: *"Read the email from Umair and reply to him"* → the agent drafts a reply, shows it to you, and only sends after you **approve**, **edit**, or **reject** it.

---

## ✨ Features

- **Inbox listing**: latest Primary-tab emails (no spam, promotions, or social)
- **Gmail search**: supports Gmail operators like `from:`, `subject:`, `has:attachment`
- **Read emails**: plain text extracted from multipart and HTML messages
- **AI-drafted replies**: Gemini writes a reply in your voice, sent in the **same thread**
- **Human-in-the-loop**: every `send_mail` and `reply_email` call pauses for approve / edit / reject
- **Conversation memory**: say "read the 2nd one" or "reply to him" without repeating IDs
- **Prompt-injection guard**: email bodies are treated as untrusted data when drafting

---

## 🏗️ How it works

```
You ──► Agent (Gemini) ──► Tools ──► Gmail API
            │                 │
            │                 └─ send_mail / reply_email ──► ⏸ Approval prompt
            │                                                  (approve / edit / reject)
            └─ State + checkpointer: remembers emails, current message, chat history
```

| Component | Role |
|---|---|
| `create_agent` | LangGraph agent loop (model ↔ tools) |
| `GmailState` | Custom state: `emails`, `current_message_id` |
| `InMemorySaver` | Checkpointer: thread memory and pause/resume for approvals |
| `HumanInTheLoopMiddleware` | Interrupts before sending anything |

### Agent tools

| Tool | Description | Needs approval |
|---|---|:---:|
| `inbox_list` | List latest Primary inbox emails | No |
| `search_email` | Search mail with Gmail query syntax | No |
| `read_email` | Read the full body of one email | No |
| `draft_reply` | Generate a reply draft (sends nothing) | No |
| `reply_email` | Send a reply in the original thread | **Yes** |
| `send_mail` | Send a brand new email | **Yes** |

---

## 📁 Project structure

```
email-agent/
├── main.py                     # Agent setup + chat/approval loop
├── backend/
│   ├── authentication.py       # Gmail OAuth flow
│   ├── gmail_message_helper.py # Body parsing, HTML→text, message builder
│   ├── gmail_message_function.py # Gmail API wrappers (list, read, search, send, reply)
│   ├── tools.py                # LangChain tool definitions
│   └── llm.py                  # Shared Gemini model instance
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🚀 Getting started

### 1. Clone and install

```bash
git clone https://github.com/<your-username>/email-agent.git
cd email-agent
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set up Gmail API access

1. Open the [Google Cloud Console](https://console.cloud.google.com/) and create a project.
2. Enable the **Gmail API**.
3. Configure the **OAuth consent screen** and add yourself as a test user.
4. Create **OAuth client ID** credentials (type: *Desktop app*).
5. Download the JSON and save it as `credentials.json` in the project root.

Scopes used:

```python
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]
```

### 3. Get a Gemini API key

Create a key in [Google AI Studio](https://aistudio.google.com/) and add it to a `.env` file:

```env
GOOGLE_API_KEY=your_key_here
```

### 4. Run

```bash
python main.py
```

The first run opens a browser window for Google sign-in and creates `token.json`.

---

## 💬 Example session

```
You: List my latest 5 emails
Agent: 1. Subject: You free | From: Umair Farooq | Message ID: 1a1b...

You: Reply to the 1st one saying I'm in

Replying to: Umair Farooq <...>
Subject: You free

--- DRAFT ---
Yes, I'm in! See you tomorrow.

Umair Farooq
-------------
[a]pprove / [e]dit / [r]eject: a

Agent: Replied to Umair Farooq with subject "Re: You free".
```

| Choice | Result |
|---|---|
| **approve** | Sends the draft as written |
| **edit** | You type a new body, and your text is what gets sent |
| **reject** | Nothing is sent, and your reason goes back to the agent so it can redraft |

---

## 🔒 Security notes

- **Never commit** `.env`, `credentials.json`, or `token.json`. They are listed in `.gitignore`. `token.json` gives access to your mailbox.
- Sending is **gated by human approval**, so the agent can't email anyone on its own.
- Incoming email text is treated as **untrusted data** when generating replies, which reduces prompt-injection risk. It does not remove it, so keep approvals on.
- To revoke access at any time, visit [Google Account permissions](https://myaccount.google.com/permissions).

---

## 🔍 Visualize the agent

```python
from main import agent
print(agent.get_graph().draw_mermaid())   # paste into https://mermaid.live
```

Or run it in **LangGraph Studio**:

```bash
pip install -U "langgraph-cli[inmem]"
langgraph dev
```

---

## 🧰 Tech stack

- Python 3.12
- [LangChain](https://python.langchain.com/) and [LangGraph](https://langchain-ai.github.io/langgraph/)
- Google Gemini via `langchain-google-genai`
- Gmail API (`google-api-python-client`, `google-auth-oauthlib`)

---

## UI:
Since Frontend has not build yet, you can use https://agentchat.vercel.app/ for visualization.

---

## 🗺️ Roadmap
- [ ] Web UI ( React)
- [ ] Attachment download and summarization
- [ ] Email classification and priority labels
- [ ] Persistent memory with SQLite checkpointer
- [ ] Unit tests for Gmail helpers

---


## 👤 Author

**Umair Farooq**
