from datetime import datetime, timezone

from lead_automation.email_templates import render_introduction_email
from lead_automation.models import ExistingLead
from lead_automation.notion_mapping import (
    build_introduction_sent_properties,
    build_notion_properties,
)
from lead_automation.normalise import normalise_uk_phone, proper_name
from lead_automation.parser import parse_local_surveyors_lead
from lead_automation.rules import check_duplicate, next_lead_number
from offline_demo import build_demo


HTML = """
<html><body>
<h2>Sales lead for Planning Permission</h2>
<p>The enquirer gave us the following details:</p>
<p><b>Name:</b> kIRSTY aCKLETON</p>
<p><b>Email:</b> KIRSTYACKLETON@GMAIL.COM</p>
<p><b>Phone:</b> 07700 900123</p>
<p><b>Postcode:</b> da12 4el</p>
<p><b>Role:</b> Tenant</p>
<p><b>Information:</b> I live in a council house and need a plan for a driveway.</p>
<p>Assuming the customer is contactable, discuss their requirements.</p>
</body></html>
"""


def make_lead():
    return parse_local_surveyors_lead(
        subject="Sales lead for Planning Permission",
        html_body=HTML,
        message_id="message-123",
        received_at=datetime(2026, 8, 21, 9, 30, tzinfo=timezone.utc),
    )


def test_normalisation():
    assert proper_name("kIRSTY aCKLETON") == "Kirsty Ackleton"
    assert normalise_uk_phone("+44 (0)7700 900123") == "00447700900123"
    assert normalise_uk_phone("0000") is None


def test_parser_and_mapping_exclude_project_fields():
    lead = make_lead()
    assert lead.client_name == "Kirsty Ackleton"
    assert lead.client_email == "kirstyackleton@gmail.com"
    assert lead.client_phone == "00447700900123"
    assert lead.postcode == "DA12 4EL"
    assert lead.project_type == "Residential"
    assert lead.discipline == "Architecture"
    assert lead.location == "UK"

    properties = build_notion_properties(lead, "L1-26-00365")
    assert properties["Status"]["status"]["name"] == "Lead | Consultation Phase"
    assert "Email Follow-Up?" not in properties
    assert "Follow Up Status" not in properties
    assert "Last Email Follow-Up" not in properties
    assert "Project Name" not in properties
    assert "Project Notes" not in properties


def test_residential_email_preview_and_post_send_update():
    email = render_introduction_email(make_lead())
    assert email.to == "kirstyackleton@gmail.com"
    assert email.template == "residential"
    assert email.subject == "We hear you have something exciting in the pipeline?"
    assert email.body.startswith("Dear Kirsty Ackleton,")
    assert "dia-residential-architecture" in email.body

    sent_at = datetime(2026, 8, 24, 12, 15, tzinfo=timezone.utc)
    update = build_introduction_sent_properties(sent_at)
    assert update["Follow Up Status"]["status"]["name"] == "Introduction"
    assert update["Email Follow-Up?"]["select"]["name"] == "Yes"
    assert update["Last Email Follow-Up"]["date"]["start"] == sent_at.isoformat()


def test_commercial_email_preview():
    lead = make_lead()
    commercial = lead.__class__(**{**lead.__dict__, "project_type": "Commercial"})
    email = render_introduction_email(commercial)
    assert email.template == "commercial"
    assert email.body.startswith("Hello Kirsty Ackleton,")
    assert "dia-commercial-brochure" in email.body


def test_lead_number():
    assert next_lead_number(["L1-26-00364", "L1-25-00999"], 2026) == "L1-26-00365"


def test_exact_message_is_duplicate():
    decision = check_duplicate(
        make_lead(),
        [ExistingLead("message-123", None, None, None, None, None)],
    )
    assert decision.duplicate is True


def test_active_matching_contact_is_duplicate():
    decision = check_duplicate(
        make_lead(),
        [
            ExistingLead(
                None,
                "KIRSTYACKLETON@GMAIL.COM",
                "+44 7700 900123",
                "DA124EL",
                "Local Surveyors",
                "Lead | Consultation Phase",
            )
        ],
    )
    assert decision.duplicate is True


def test_complete_offline_demo_is_safe_and_has_no_project_manager():
    result = build_demo()
    assert result["safety"] == {
        "outlook_read": False,
        "notion_write": False,
        "email_sent": False,
        "mode": "offline simulation",
    }
    properties = result["notion_properties_preview"]
    assert "Project Manager" not in properties
    assert "Project Name" not in properties
    assert "Project Notes" not in properties
    assert result["duplicate_decision"]["duplicate"] is False
