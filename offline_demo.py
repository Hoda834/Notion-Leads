import json
from datetime import datetime, timezone

from lead_automation.email_templates import render_introduction_email
from lead_automation.models import ExistingLead
from lead_automation.notion_mapping import (
    build_introduction_sent_properties,
    build_notion_properties,
)
from lead_automation.parser import parse_local_surveyors_lead
from lead_automation.rules import check_duplicate, next_lead_number


SAMPLE_EMAIL = """
<html><body>
<h2>Sales lead for Planning Permission</h2>
<p>The enquirer gave us the following details:</p>
<p><b>Name:</b> kIRSTY aCKLETON</p>
<p><b>Email:</b> KIRSTYACKLETON@GMAIL.COM</p>
<p><b>Phone:</b> 0000</p>
<p><b>Postcode:</b> da12 4el</p>
<p><b>Role:</b> Tenant</p>
<p><b>Information:</b> I live in a council house and need a plan for a driveway.</p>
<p>Assuming the customer is contactable, discuss their requirements.</p>
</body></html>
"""


def build_demo() -> dict:
    lead = parse_local_surveyors_lead(
        subject="Sales lead for Planning Permission",
        html_body=SAMPLE_EMAIL,
        message_id="offline-demo-message-001",
        received_at=datetime(2026, 8, 24, 9, 30, tzinfo=timezone.utc),
    )

    # Demonstrates a non-duplicate. Production will replace this list with
    # records queried from Notion.
    existing = [
        ExistingLead(
            outlook_message_id=None,
            client_email="someone.else@example.com",
            client_phone="00447700900999",
            postcode="ME14 1AA",
            source="Local Surveyors",
            status="Lead | Consultation Phase",
        )
    ]
    duplicate = check_duplicate(lead, existing)
    lead_number = next_lead_number(["L1-26-00364", "L1-25-00999"], 2026)
    notion_properties = build_notion_properties(lead, lead_number)
    email = render_introduction_email(lead)
    post_send_update = build_introduction_sent_properties(
        datetime(2026, 8, 24, 9, 31, tzinfo=timezone.utc)
    )

    return {
        "safety": {
            "outlook_read": False,
            "notion_write": False,
            "email_sent": False,
            "mode": "offline simulation",
        },
        "parsed_lead": {
            "client_name": lead.client_name,
            "client_email": lead.client_email,
            "client_phone": lead.client_phone,
            "postcode": lead.postcode,
            "source": lead.source,
            "service": lead.service,
            "project_type": lead.project_type,
            "discipline": lead.discipline,
            "location": lead.location,
        },
        "duplicate_decision": {
            "duplicate": duplicate.duplicate,
            "needs_review": duplicate.needs_review,
            "reason": duplicate.reason,
        },
        "lead_number": lead_number,
        "notion_properties_preview": notion_properties,
        "introduction_email_preview": {
            "to": email.to,
            "subject": email.subject,
            "template": email.template,
            "body": email.body,
        },
        "notion_update_after_successful_send_preview": post_send_update,
    }


def main() -> None:
    result = build_demo()
    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    print(rendered)

    import os

    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write("## Offline lead simulation\n\n")
            summary.write("No Outlook email was read, no Notion record was changed, and no email was sent.\n\n")
            summary.write("```json\n")
            summary.write(rendered)
            summary.write("\n```\n")


if __name__ == "__main__":
    main()
