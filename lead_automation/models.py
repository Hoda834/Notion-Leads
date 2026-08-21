from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Lead:
    outlook_message_id: str
    received_at: datetime
    client_name: str
    client_email: str
    client_phone: str | None
    postcode: str
    role: str
    source: str
    service: str
    information: str
    project_type: str | None
    discipline: str | None
    location: str | None


@dataclass(frozen=True)
class ExistingLead:
    outlook_message_id: str | None
    client_email: str | None
    client_phone: str | None
    postcode: str | None
    source: str | None
    status: str | None
    page_id: str | None = None
    last_email_follow_up: str | None = None


@dataclass(frozen=True)
class DuplicateDecision:
    duplicate: bool
    needs_review: bool
    reason: str | None = None


@dataclass(frozen=True)
class MailMessage:
    message_id: str
    internet_message_id: str | None
    subject: str
    received_at: datetime
    html_body: str
