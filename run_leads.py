import logging
import hashlib
from datetime import datetime, timezone

from lead_automation.config import Settings
from lead_automation.email_template import introduction_email
from lead_automation.graph_client import GraphClient
from lead_automation.notion_client import NotionClient
from lead_automation.notion_mapping import build_email_sent_properties, build_notion_properties
from lead_automation.parser import parse_local_surveyors_lead
from lead_automation.rules import check_duplicate, next_lead_number
from lead_automation.models import ExistingLead


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
LOG = logging.getLogger(__name__)


def safe_reference(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def main() -> int:
    settings = Settings.from_env()
    graph = GraphClient(settings.tenant_id, settings.client_id, settings.client_secret, settings.mailbox)
    notion = NotionClient(settings.notion_token, settings.notion_data_source_id)
    notion.validate_schema()
    numbers, existing = notion.snapshot()

    created = duplicates = reviews = errors = 0
    for message in graph.lead_messages(settings.max_messages):
        reference = safe_reference(message.internet_message_id or message.message_id)
        try:
            lead = parse_local_surveyors_lead(
                subject=message.subject,
                html_body=message.html_body,
                message_id=message.internet_message_id or message.message_id,
                received_at=message.received_at,
            )
            exact = next(
                (item for item in existing if item.outlook_message_id == lead.outlook_message_id), None
            )
            if exact and settings.enable_writes and settings.send_introduction_email and not exact.last_email_follow_up:
                subject, html = introduction_email(lead)
                graph.send_html_email(lead.client_email, subject, html)
                notion.update_page(
                    exact.page_id,
                    build_email_sent_properties(datetime.now(timezone.utc).date()),
                )
                LOG.info("Recovered pending introduction email: ref=%s", reference)
                continue
            decision = check_duplicate(lead, existing)
            if decision.duplicate:
                duplicates += 1
                LOG.info("Skipped duplicate: ref=%s reason=%s", reference, decision.reason)
                continue
            if decision.needs_review:
                reviews += 1
                LOG.warning("Skipped possible duplicate for manual review: ref=%s", reference)
                continue

            # Refresh immediately before assignment to include manual Notion entries.
            numbers = notion.lead_numbers()
            lead_number = next_lead_number(numbers, lead.received_at.year)
            props = build_notion_properties(lead, lead_number, settings.project_manager_id)
            if not settings.enable_writes:
                LOG.info("DRY RUN: would create %s ref=%s", lead_number, reference)
                continue

            page_id = notion.create_lead(props, lead)
            numbers.append(lead_number)
            existing.append(
                ExistingLead(
                    lead.outlook_message_id,
                    lead.client_email,
                    lead.client_phone,
                    lead.postcode,
                    lead.source,
                    "Lead | Consultation Phase",
                )
            )
            created += 1
            if settings.send_introduction_email:
                subject, html = introduction_email(lead)
                graph.send_html_email(lead.client_email, subject, html)
                notion.update_page(page_id, build_email_sent_properties(datetime.now(timezone.utc).date()))
            else:
                LOG.info("Introduction email disabled: ref=%s", reference)
        except Exception as exc:
            errors += 1
            LOG.error("Lead message failed: ref=%s error=%s", reference, type(exc).__name__)

    LOG.info("Complete: created=%d duplicates=%d reviews=%d errors=%d", created, duplicates, reviews, errors)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
