from datetime import datetime

from .models import Lead


def rich_text(value: str) -> dict:
    return {"rich_text": [{"type": "text", "text": {"content": value}}]}


def build_notion_properties(lead: Lead, lead_number: str, project_manager_id: str | None = None) -> dict:
    """Build the proposed payload only. This function performs no API call."""
    properties = {
        "Lead No.": {"title": [{"type": "text", "text": {"content": lead_number}}]},
        "Inquiry Date": {"date": {"start": lead.received_at.date().isoformat()}},
        "Client Name(s)": rich_text(lead.client_name),
        "Client Email": {"email": lead.client_email},
        "Lead Source": {"select": {"name": "Local Surveyors"}},
        "Status": {"status": {"name": "Lead | Consultation Phase"}},
    }
    if lead.client_phone:
        properties["Client Phone"] = {"phone_number": lead.client_phone}
    if lead.postcode:
        properties["Postcode"] = rich_text(lead.postcode)
    if lead.project_type:
        properties["Project Type"] = {"select": {"name": lead.project_type}}
    if lead.discipline:
        properties["Discipline"] = {"select": {"name": lead.discipline}}
    if lead.location:
        properties["Location"] = {"select": {"name": lead.location}}
    if project_manager_id:
        properties["Project Manager"] = {"people": [{"id": project_manager_id}]}

    # Project Name and Project Notes are intentionally excluded for new leads.
    return properties


def build_introduction_sent_properties(sent_at: datetime) -> dict:
    """Build the update applied only after the introduction email succeeds."""
    return {
        "Follow Up Status": {"status": {"name": "Introduction"}},
        "Last Email Follow-Up": {"date": {"start": sent_at.isoformat()}},
        "Email Follow-Up?": {"select": {"name": "Yes"}},
    }
