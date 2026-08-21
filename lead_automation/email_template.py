from html import escape

from .models import Lead


def introduction_email(lead: Lead) -> tuple[str, str]:
    """Temporary copy. Replace this function after the final company text is approved."""
    first_name = escape(lead.client_name.split()[0] if lead.client_name else "there")
    subject = "Thank you for your enquiry"
    html = f"""
    <p>Dear {first_name},</p>
    <p>Thank you for your enquiry regarding {escape(lead.service or 'your project')}.</p>
    <p>[COMPANY INTRODUCTION EMAIL TEXT TO BE ADDED LATER]</p>
    <p>Kind regards,<br>Design-itude Associates Ltd</p>
    """.strip()
    return subject, html
