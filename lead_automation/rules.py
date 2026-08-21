import re

from .models import DuplicateDecision, ExistingLead, Lead
from .normalise import normalise_email, normalise_postcode, normalise_uk_phone


ACTIVE_STATUSES = {
    "Lead | Consultation Phase",
    "Invoice Requested",
    "On hold",
    "Pre-Project",
}


def next_lead_number(existing_numbers: list[str], year: int) -> str:
    year_code = str(year)[-2:]
    pattern = re.compile(rf"^L1-{year_code}-(\d{{5}})$", flags=re.IGNORECASE)
    sequences = [int(match.group(1)) for value in existing_numbers if (match := pattern.match(value.strip()))]
    return f"L1-{year_code}-{max(sequences, default=0) + 1:05d}"


def check_duplicate(lead: Lead, existing: list[ExistingLead]) -> DuplicateDecision:
    possible_match = False
    for item in existing:
        if item.outlook_message_id and item.outlook_message_id == lead.outlook_message_id:
            return DuplicateDecision(True, False, "Outlook Message ID already exists")

    lead_email = normalise_email(lead.client_email)
    lead_phone = normalise_uk_phone(lead.client_phone)
    lead_postcode = normalise_postcode(lead.postcode)

    for item in existing:
        if item.status not in ACTIVE_STATUSES:
            continue
        same_email = lead_email and lead_email == normalise_email(item.client_email)
        same_phone = lead_phone and lead_phone == normalise_uk_phone(item.client_phone)
        same_postcode = lead_postcode and lead_postcode == normalise_postcode(item.postcode)
        same_source = (item.source or "").casefold() == lead.source.casefold()
        if same_email and same_source and (same_phone or same_postcode):
            return DuplicateDecision(True, False, "Active lead has matching contact details")
        if same_email or (same_phone and same_postcode):
            possible_match = True

    if possible_match:
        return DuplicateDecision(False, True, "Possible duplicate requires review")
    return DuplicateDecision(False, False)
