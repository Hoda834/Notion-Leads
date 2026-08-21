from datetime import datetime, timezone

from lead_automation.models import ExistingLead
from lead_automation.notion_mapping import build_notion_properties, build_page_children
from lead_automation.normalise import normalise_postcode, normalise_uk_phone, proper_name
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
    assert lead.role == "Tenant"
    assert lead.project_type == "Residential"
    assert lead.discipline == "Architecture"
    assert lead.location == "UK"

    properties = build_notion_properties(lead, "L1-26-00365")
    assert properties["Status"]["status"]["name"] == "Lead | Consultation Phase"
    assert "Project Name" not in properties
    assert "Project Notes" not in properties
    body = "\n".join(block["paragraph"]["rich_text"][0]["text"]["content"] for block in build_page_children(lead))
    assert "Role: Tenant" in body
    assert "Information: I live in a council house" in body
    assert "Outlook message reference: message-123" in body


def test_lead_number():
    assert next_lead_number(["L1-26-00364", "L1-25-00999"], 2026) == "L1-26-00365"
    assert next_lead_number([], 2027) == "L1-27-00001"
    assert next_lead_number(["L1-26-99999"], 2027) == "L1-27-00001"


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


def test_strong_duplicate_wins_regardless_of_order():
    lead = make_lead()
    weak = ExistingLead(None, lead.client_email, None, None, "Other", "Lead | Consultation Phase")
    strong = ExistingLead(
        None,
        lead.client_email,
        lead.client_phone,
        lead.postcode,
        lead.source,
        "Lead | Consultation Phase",
    )
    for records in ([weak, strong], [strong, weak]):
        decision = check_duplicate(lead, records)
        assert decision.duplicate is True
        assert decision.needs_review is False


def test_weak_duplicate_requires_review():
    lead = make_lead()
    decision = check_duplicate(
        lead,
        [ExistingLead(None, lead.client_email, None, None, "Other", "Lead | Consultation Phase")],
    )
    assert decision.duplicate is False
    assert decision.needs_review is True


def test_invalid_postcode_is_rejected():
    try:
        normalise_postcode("not sure")
    except ValueError as exc:
        assert str(exc) == "Invalid UK postcode"
    else:
        raise AssertionError("Invalid postcode was accepted")


def test_parser_does_not_confuse_business_name_with_name():
    html = HTML.replace(
        "<p><b>Name:</b> kIRSTY aCKLETON</p>",
        "<p><b>Business Name:</b> Acme Ltd</p><p><b>Name:</b> kIRSTY aCKLETON</p>",
    )
    lead = parse_local_surveyors_lead(
        subject="Sales lead for Planning Permission",
        html_body=html,
        message_id="message-business-name",
        received_at=datetime(2026, 8, 21, 9, 30, tzinfo=timezone.utc),
    )
    assert lead.client_name == "Kirsty Ackleton"


def test_non_lead_message_is_rejected():
    try:
        parse_local_surveyors_lead(
            subject="Newsletter",
            html_body="<p>Hello</p>",
            message_id="not-a-lead",
            received_at=datetime(2026, 8, 21, 9, 30, tzinfo=timezone.utc),
        )
    except ValueError as exc:
        assert "not a Local Surveyors sales lead" in str(exc)
    else:
        raise AssertionError("Non-lead message was accepted")
