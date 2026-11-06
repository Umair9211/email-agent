from langchain.messages import HumanMessage
from typing_extensions import NotRequired
from langchain.agents import create_agent
from langgraph.types import Command
from backend.tools import *

from langchain.agents import AgentState
from backend.llm import model
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.middleware import HumanInTheLoopMiddleware
class GmailState(AgentState):
    emails: NotRequired[list[dict]]
    current_message_id: NotRequired[str]
  



agent = create_agent(
model = model,
tools=[inbox_list,read_email,search_email,send_mail,reply_email,draft_reply],
system_prompt=(
    "You are an email assistant. List emails as a numbered list with Subject, "
    "From, Date and Message ID. When the user says 'the 2nd one' or 'that email', "
    "resolve it from the previously listed emails and call read_email with its "
    "message_id. Never ask for an ID you already have. You can also search the "
    "mailbox if asked. To send a NEW email, use send_mail only when the user "
    "clearly gives a recipient and what to say; if either is missing, ask first. "
    "To respond to an existing email, use reply_email with that email's message_id. "
    "To reply without user-dictated text: call draft_reply, then call reply_email "
    "with the draft passed EXACTLY as returned, signature included, no changes. "
    "Never claim an email was sent unless the tool result says status sent. "
    "If the user rejects or edits, follow their feedback. "
    "After sending or replying, confirm who it went to and the subject. "
    "Always finish with a short text reply, even after a tool call."
),
state_schema=GmailState,
 middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={
                "send_mail":   {"allowed_decisions": ["approve", "edit", "reject"]},
                "reply_email": {"allowed_decisions": ["approve", "edit", "reject"]},
            },
            description_prefix="Email awaiting your approval",
        )
    ],
checkpointer=InMemorySaver()

)




def read_multiline(prompt: str) -> str:
    print(prompt + " (finish with a line containing only END)")
    lines = []
    while (line := input()) != "END":
        lines.append(line)
    return "\n".join(lines)

def handle_interrupt(interrupt) -> dict:
    req = interrupt.value["action_requests"][0]
    name, args = req["name"], req["args"]

    # Context the interrupt doesn't include
    if name == "reply_email":
        orig = read_message(args["message_id"])
        print(f"\nReplying to: {orig['from']}\nSubject: {orig['subject']}")
    else:
        print(f"\nTo: {args.get('to')}\nSubject: {args.get('subject')}")
    print(f"\n--- DRAFT ---\n{args['body']}\n-------------")

    choice = input("[a]pprove / [e]dit / [r]eject: ").strip().lower()
    if choice == "a":
        return {"type": "approve"}
    if choice == "e":
        new_body = read_multiline("Enter the new body")
        return {
            "type": "edit",
            "edited_action": {"name": name, "args": {**args, "body": new_body}},
        }
    reason = input("Why? (the model will see this): ")
    return {"type": "reject", "message": reason or "User rejected the email."}


def final_text(result) -> str:
    text = result["messages"][-1].text.strip()
    if text:
        return text
    last_tool = next((m for m in reversed(result["messages"]) if m.type == "tool"), None)
    return f"[Model returned no text. Last tool result: {last_tool.content if last_tool else 'none'}]"

if __name__ == "__main__":
    config = {"configurable": {"thread_id": "1"}}
    while True:
        q = input("\nYou: ")
        if q.lower() in {"exit", "quit"}:
            break

        result = agent.invoke({"messages": [HumanMessage(q)]}, config)

        # Agent is paused waiting for approval: ask, resume, repeat
        while "__interrupt__" in result:
            decision = handle_interrupt(result["__interrupt__"][0])
            result = agent.invoke(Command(resume={"decisions": [decision]}), config)

        print("\nAgent:", final_text(result))