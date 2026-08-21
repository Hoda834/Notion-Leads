from datetime import datetime
from urllib.parse import quote

import requests

from .models import MailMessage
from .http import retrying_session


GRAPH = "https://graph.microsoft.com/v1.0"


class GraphClient:
    def __init__(self, tenant_id: str, client_id: str, client_secret: str, mailbox: str) -> None:
        self.mailbox = mailbox
        self.session = retrying_session()
        response = self.session.post(
            f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": "https://graph.microsoft.com/.default",
                "grant_type": "client_credentials",
            },
            timeout=30,
        )
        self._raise(response)
        self.token = response.json()["access_token"]

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    @staticmethod
    def _raise(response: requests.Response) -> None:
        if response.ok:
            return
        try:
            detail = response.json().get("error", {}).get("message", response.text)
        except ValueError:
            detail = response.text
        raise RuntimeError(f"Microsoft Graph returned {response.status_code}: {detail}")

    def lead_messages(self, limit: int) -> list[MailMessage]:
        mailbox = quote(self.mailbox)
        url = f"{GRAPH}/users/{mailbox}/mailFolders/inbox/messages"
        params = {
            "$select": "id,internetMessageId,subject,receivedDateTime,body",
            "$orderby": "receivedDateTime desc",
            "$top": str(limit),
        }
        response = self.session.get(url, headers=self.headers, params=params, timeout=30)
        self._raise(response)
        messages = [
            MailMessage(
                message_id=item["id"],
                internet_message_id=item.get("internetMessageId"),
                subject=item.get("subject", ""),
                received_at=datetime.fromisoformat(item["receivedDateTime"].replace("Z", "+00:00")),
                html_body=item.get("body", {}).get("content", ""),
            )
            for item in response.json().get("value", [])
        ]
        return [message for message in reversed(messages) if "sales lead for" in message.subject.casefold()]

    def send_html_email(self, recipient: str, subject: str, html: str) -> None:
        mailbox = quote(self.mailbox)
        response = self.session.post(
            f"{GRAPH}/users/{mailbox}/sendMail",
            headers=self.headers,
            json={
                "message": {
                    "subject": subject,
                    "body": {"contentType": "HTML", "content": html},
                    "toRecipients": [{"emailAddress": {"address": recipient}}],
                },
                "saveToSentItems": True,
            },
            timeout=30,
        )
        self._raise(response)
