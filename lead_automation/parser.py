import re
from datetime import datetime
from html.parser import HTMLParser

from .models import Lead
from .normalise import normalise_postcode, normalise_uk_phone, proper_name


FIELD_PATTERNS = {
    "name": r"\bName:\s*(.+)",
    "email": r"\bEmail:\s*([^\s]+)",
    "phone": r"\bPhone:\s*(.+)",
    "postcode": r"\bPostcode:\s*(.+)",
    "role": r"\bRole:\s*(.+)",
}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self.ignored_depth += 1
        elif tag in {"br", "p", "div", "tr", "td", "th", "h1", "h2", "h3", "li"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self.ignored_depth:
            self.ignored_depth -= 1
        elif tag in {"p", "div", "tr", "td", "th", "h1", "h2", "h3", "li"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.ignored_depth:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    extractor = _TextExtractor()
    extractor.feed(html)
    text = "".join(extractor.parts)
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def find_field(text: str, pattern: str, required: bool = True) -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        if required:
            raise ValueError(f"Required lead field was not found: {pattern}")
        return ""
    return match.group(1).strip()


def extract_information(text: str) -> str:
    match = re.search(
        r"\bInformation:\s*(.*?)(?=\nAssuming the customer is contactable|\nThe full set of results|\Z)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return re.sub(r"\s+", " ", match.group(1)).strip() if match else ""


def classify_project_type(information: str) -> str | None:
    text = information.casefold()
    rules = {
        "Residential": ("house", "flat", "home", "garden", "driveway", "loft", "extension"),
        "Workplace": ("office", "workspace"),
        "Retail": ("shop", "store", "retail unit"),
        "Commercial": ("commercial", "restaurant", "hotel", "business premises"),
    }
    matches = [label for label, terms in rules.items() if any(term in text for term in terms)]
    return matches[0] if len(matches) == 1 else None


def classify_discipline(service: str, information: str) -> str | None:
    text = f"{service} {information}".casefold()
    if any(term in text for term in ("planning permission", "architect", "drawing", "floor plan")):
        return "Architecture"
    if any(term in text for term in ("landscape", "garden design")):
        return "Landscape"
    if any(term in text for term in ("interior design", "interiors")):
        return "Interior Design"
    return None


def parse_local_surveyors_lead(
    *,
    subject: str,
    html_body: str,
    message_id: str,
    received_at: datetime,
) -> Lead:
    text = html_to_text(html_body)
    if "sales lead for" not in subject.casefold() and "sales lead for" not in text.casefold():
        raise ValueError("Message is not a Local Surveyors sales lead")

    service_match = re.search(r"Sales lead for\s+(.+)", subject, flags=re.IGNORECASE)
    if not service_match:
        service_match = re.search(r"Sales lead for\s+(.+)", text, flags=re.IGNORECASE)
    service = service_match.group(1).strip() if service_match else ""
    information = extract_information(text)
    postcode = normalise_postcode(find_field(text, FIELD_PATTERNS["postcode"]))

    return Lead(
        outlook_message_id=message_id,
        received_at=received_at,
        client_name=proper_name(find_field(text, FIELD_PATTERNS["name"])),
        client_email=find_field(text, FIELD_PATTERNS["email"]).casefold(),
        client_phone=normalise_uk_phone(find_field(text, FIELD_PATTERNS["phone"], required=False)),
        postcode=postcode,
        source="Local Surveyors",
        service=service,
        information=information,
        project_type=classify_project_type(information),
        discipline=classify_discipline(service, information),
        location="UK" if postcode else None,
    )
