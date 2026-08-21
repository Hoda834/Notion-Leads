from datetime import date

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
        "Email Follow-Up?": {"select": {"name": "Yes"}},
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


def build_page_children(lead: Lead) -> list[dict]:
    """Preserve source details in the page body without using Project Name or Project Notes."""
    lines = [
        f"Service: {lead.service or '-'}",
        f"Role: {lead.role or '-'}",
        f"Information: {lead.information or '-'}",
        f"Outlook message reference: {lead.outlook_message_id}",
    ]
    return [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": line}}]},
        }
        for line in lines
    ]


def build_email_sent_properties(sent_on: date) -> dict:
    return {
        "Last Email Follow-Up": {"date": {"start": sent_on.isoformat()}},
        "Follow Up Status": {"status": {"name": "Introduction"}},
    }
