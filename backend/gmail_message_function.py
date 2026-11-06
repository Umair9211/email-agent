from backend.authentication import authenticate_gmail
from backend.gmail_message_helper import *

service = authenticate_gmail()

results = service.users().labels().list(
    userId="me"
).execute()

labels = results.get("labels", [])

print("Gmail connected successfully! \n")
profile = service.users().getProfile(
    userId="me"
).execute()

print("Email account:", profile["emailAddress"])
print("Total messages:", profile["messagesTotal"])
print("Total threads:", profile["threadsTotal"])



def get_inbox_messages( max_results: int = 5) -> list[dict]:
    results = service.users().messages().list(
        userId="me",
        q="category:primary in:inbox",
        maxResults=max_results,
    ).execute()

    emails = []
    for m in results.get("messages", []):
        email = service.users().messages().get(
            userId="me",
            id=m["id"],
            format="metadata",
            metadataHeaders=["Subject", "From", "Date"],
        ).execute()

        headers = {h["name"]: h["value"] for h in email.get("payload", {}).get("headers", [])}
        emails.append({
            "message_id": m["id"],
            "subject": headers.get("Subject"),
            "from": headers.get("From"),
            "date": headers.get("Date"),
            "snippet": email.get("snippet", ""),
        })
    return emails  # inside the function, after the loop finishes
def read_message( message_id)-> dict:
    email = service.users().messages().get(
        userId="me",
        id=message_id,
        format="full"
    ).execute()

    payload = email.get("payload", {})
    headers = {h["name"]: h["value"] for h in payload.get("headers", [])}

    body, kind = find_body(payload)
    if kind == "html":
        body = html_to_text(body)

    return {
        "message_id": message_id,
        "from": headers.get("From"),
        "subject": headers.get("Subject"),
        "date": headers.get("Date"),
        "body": (body or "[No readable body found]")[:4000],  # cap size for the LLM
    }


def send_message( to, subject, body, **kwargs):
    
    message = create_message(to, subject, body, **kwargs)
    sent = service.users().messages().send(userId="me", body=message).execute()
    print("Email sent! Message ID:", sent["id"])
    return sent



def reply_to_message(message_id: str, body: str):
    original = service.users().messages().get(
        userId="me", id=message_id, format="metadata",
        metadataHeaders=["From", "Reply-To", "Subject", "Message-ID"],
    ).execute()

    headers = {h["name"].lower(): h["value"] for h in original["payload"]["headers"]}
    subject = headers.get("subject", "")
    if not subject.lower().startswith("re:"):
        subject = "Re: " + subject

    msg = EmailMessage()
    msg["To"] = headers.get("reply-to") or headers["from"]
    msg["Subject"] = subject
    if "message-id" in headers:
        msg["In-Reply-To"] = headers["message-id"]
        msg["References"] = headers["message-id"]
    msg.set_content(body)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return service.users().messages().send(
        userId="me",
        body={"raw": raw, "threadId": original["threadId"]},
    ).execute()
def search_messages(query: str, max_results: int = 10, inbox_only: bool = False) -> list[dict]:
    """Search Gmail for `query` and return matches, newest first."""
    q = f"in:inbox {query}" if inbox_only else query

    results = service.users().messages().list(
        userId="me",
        q=q,
        maxResults=max_results,
    ).execute()

    emails = []
    for m in results.get("messages", []):
        email = service.users().messages().get(
            userId="me",
            id=m["id"],
            format="metadata",
            metadataHeaders=["Subject", "From", "Date"],
        ).execute()

        headers = {h["name"]: h["value"] for h in email.get("payload", {}).get("headers", [])}
        emails.append({
            "message_id": m["id"],
            "subject": headers.get("Subject"),
            "from": headers.get("From"),
            "date": headers.get("Date"),
            "snippet": email.get("snippet", ""),
            "internal_date": int(email.get("internalDate", 0)),
        })

    # Newest first (explicit, so order is guaranteed)
    emails.sort(key=lambda e: e["internal_date"], reverse=True)
    return emails





