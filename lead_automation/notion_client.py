from __future__ import annotations

import requests

from .models import ExistingLead, Lead
from .notion_mapping import build_page_children
from .http import retrying_session


NOTION_VERSION = "2026-03-11"
API = "https://api.notion.com/v1"


def _plain(items: list[dict]) -> str:
    return "".join(item.get("plain_text", "") for item in items)


def _value(prop: dict | None):
    prop = prop or {}
    kind = prop.get("type")
    if kind == "title":
        return _plain(prop.get("title", []))
    if kind == "rich_text":
        return _plain(prop.get("rich_text", []))
    if kind == "email":
        return prop.get("email")
    if kind == "phone_number":
        return prop.get("phone_number")
    if kind in {"select", "status"}:
        return (prop.get(kind) or {}).get("name")
    if kind == "date":
        return (prop.get("date") or {}).get("start")
    return None


class NotionClient:
    def __init__(self, token: str, data_source_id: str) -> None:
        self.data_source_id = data_source_id
        self.session = retrying_session()
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        }

    @staticmethod
    def _raise(response: requests.Response) -> None:
        if response.ok:
            return
        try:
            detail = response.json().get("message", response.text)
        except ValueError:
            detail = response.text
        raise RuntimeError(f"Notion API returned {response.status_code}: {detail}")

    def query_all(self) -> list[dict]:
        pages: list[dict] = []
        payload: dict = {"page_size": 100}
        while True:
            response = self.session.post(
                f"{API}/data_sources/{self.data_source_id}/query",
                headers=self.headers,
                json=payload,
                timeout=30,
            )
            self._raise(response)
            body = response.json()
            pages.extend(body.get("results", []))
            if not body.get("has_more"):
                return pages
            payload["start_cursor"] = body["next_cursor"]

    def validate_schema(self) -> None:
        required = {
            "Lead No.": "title",
            "Inquiry Date": "date",
            "Client Name(s)": "rich_text",
            "Client Email": "email",
            "Client Phone": "phone_number",
            "Postcode": "rich_text",
            "Lead Source": "select",
            "Status": "status",
            "Project Type": "select",
            "Discipline": "select",
            "Location": "select",
            "Email Follow-Up?": "select",
            "Follow Up Status": "status",
            "Last Email Follow-Up": "date",
        }
        response = self.session.get(
            f"{API}/data_sources/{self.data_source_id}", headers=self.headers, timeout=30
        )
        self._raise(response)
        properties = response.json().get("properties", {})
        errors = [
            f"{name} (expected {kind})"
            for name, kind in required.items()
            if name not in properties or properties[name].get("type") != kind
        ]
        required_options = {
            "Lead Source": {"Local Surveyors"},
            "Status": {"Lead | Consultation Phase"},
            "Project Type": {"Residential", "Commercial", "Retail", "Workplace"},
            "Discipline": {"Architecture", "Interior Design", "Landscape"},
            "Location": {"UK"},
            "Email Follow-Up?": {"Yes"},
            "Follow Up Status": {"Introduction"},
        }
        for name, expected in required_options.items():
            prop = properties.get(name, {})
            kind = prop.get("type")
            actual = {item.get("name") for item in (prop.get(kind) or {}).get("options", [])}
            missing = expected - actual
            if missing:
                errors.append(f"{name} missing options: {', '.join(sorted(missing))}")
        if errors:
            raise RuntimeError("Notion schema mismatch: " + "; ".join(errors))

    def lead_numbers(self) -> list[str]:
        return [
            value
            for page in self.query_all()
            if (value := _value(page.get("properties", {}).get("Lead No.")))
        ]

    def _message_reference(self, page_id: str) -> str | None:
        response = self.session.get(
            f"{API}/blocks/{page_id}/children?page_size=100", headers=self.headers, timeout=30
        )
        self._raise(response)
        prefix = "Outlook message reference: "
        for block in response.json().get("results", []):
            rich_text = (block.get(block.get("type", "")) or {}).get("rich_text", [])
            text = _plain(rich_text)
            if text.startswith(prefix):
                return text[len(prefix):].strip() or None
        return None

    def snapshot(self) -> tuple[list[str], list[ExistingLead]]:
        numbers: list[str] = []
        leads: list[ExistingLead] = []
        for page in self.query_all():
            props = page.get("properties", {})
            number = _value(props.get("Lead No."))
            if number:
                numbers.append(number)
            # No new database column is required: the immutable ID is stored in the page body.
            message_id = self._message_reference(page["id"])
            leads.append(
                ExistingLead(
                    message_id,
                    _value(props.get("Client Email")),
                    _value(props.get("Client Phone")),
                    _value(props.get("Postcode")),
                    _value(props.get("Lead Source")),
                    _value(props.get("Status")),
                    page["id"],
                    _value(props.get("Last Email Follow-Up")),
                )
            )
        return numbers, leads

    def create_lead(self, properties: dict, lead: Lead) -> str:
        response = self.session.post(
            f"{API}/pages",
            headers=self.headers,
            json={
                "parent": {"type": "data_source_id", "data_source_id": self.data_source_id},
                "properties": properties,
                "icon": {"type": "emoji", "emoji": "🏠"},
                "children": build_page_children(lead),
            },
            timeout=30,
        )
        self._raise(response)
        return response.json()["id"]

    def update_page(self, page_id: str, properties: dict) -> None:
        response = self.session.patch(
            f"{API}/pages/{page_id}", headers=self.headers, json={"properties": properties}, timeout=30
        )
        self._raise(response)
