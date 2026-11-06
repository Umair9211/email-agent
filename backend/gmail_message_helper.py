import base64
import re
from html import unescape
import mimetypes
import os
from email.message import EmailMessage

def decode_data(data):
    """Decode Gmail's base64url body data."""
    if not data:
        return ""
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", errors="replace")


def find_body(payload):
    """Recursively search message parts. Prefer plain text, fall back to HTML."""
    mime = payload.get("mimeType", "")
    data = payload.get("body", {}).get("data")

    if mime == "text/plain" and data:
        return decode_data(data), "plain"
    if mime == "text/html" and data:
        return decode_data(data), "html"

    plain, html = None, None
    for part in payload.get("parts", []):
        text, kind = find_body(part)
        if kind == "plain" and not plain:
            plain = text
        elif kind == "html" and not html:
            html = text

    if plain:
        return plain, "plain"
    if html:
        return html, "html"
    return "", None


def html_to_text(html):
    """Quick-and-dirty HTML to text conversion."""
    html = re.sub(r"(?is)<(script|style).*?>.*?</\1>", "", html)
    html = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>", "\n", html)
    text = re.sub(r"<[^>]+>", "", html)
    text = unescape(text)
    return re.sub(r"\n\s*\n+", "\n\n", text).strip()






def create_message(to, subject, body, cc=None, bcc=None, attachments=None, html=False):
    """Build a Gmail-ready message dict."""
    msg = EmailMessage()
    msg["To"] = to
    msg["Subject"] = subject
    if cc:
        msg["Cc"] = cc
    if bcc:
        msg["Bcc"] = bcc

    if html:
        msg.set_content("This email requires an HTML-capable client.")
        msg.add_alternative(body, subtype="html")
    else:
        msg.set_content(body)

    for path in attachments or []:
        ctype, _ = mimetypes.guess_type(path)
        maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
        with open(path, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype=maintype,
                subtype=subtype,
                filename=os.path.basename(path),
            )

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return {"raw": raw}
