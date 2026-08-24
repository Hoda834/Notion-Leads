from datetime import datetime, timezone

from lead_automation.models import ExistingLead
from lead_automation.notion_mapping import build_notion_properties
from lead_automation.normalise import normalise_uk_phone, proper_name
from lead_automation.parser import parse_local_surveyors_lead
from lead_automation.rules import check_duplicate, next_lead_number


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
    assert "Project Name" not in properties
    assert "Project Notes" not in properties


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
