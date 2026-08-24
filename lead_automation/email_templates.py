from .models import IntroductionEmail, Lead


SUBJECT = "We hear you have something exciting in the pipeline?"

DISCLAIMER = """Designitude Associates LTD | A company registered in England and Wales No. 13241637
Registered Office: 124 City Road, London, EC1V 2NX

Disclaimer
The information contained in this message is likely to be confidential. It is intended only for the person(s) named above. If you have received this message in error, please immediately notify us and delete it. Any dissemination, distribution, copying, disclosure or use of this message or its contents unless authorised by Designitude Associates Limited is strictly prohibited.

We cannot guarantee the integrity or suitability of this message for your computer. It is possible that our message to you might contain destructive programmes known as Viruses or Worms and we would advise you that we do not accept any liability for consequential effects caused to your computer, or others connected to it and that you should determine the likelihood of such content yourself. Business e-mails are sent to you subject to our usual terms of business. When the content of an e-mail is a personal message, the sender is not acting in his/her capacity as a director or employee of Designitude Associates Limited.

Please consider the environment and don't print this e-mail unless you really need to."""

RESIDENTIAL_BODY = """Dear {client_name},

Thank you for getting in touch regarding your potential project. We would welcome the opportunity to discuss your brief in more detail and to see how we may be of assistance.

Design-Itude is a full-service architectural and interior design studio. We work closely with our clients to develop considered, practical and well-designed spaces, guiding projects carefully from early stages through to delivery.

A short introductory discussion would allow us to understand your requirements, clarify scope and priorities, and advise on the most appropriate next steps. This would also enable us to outline our approach and provide an initial fee proposal, where appropriate.

If you would like to arrange a call, please book a convenient time via the link below:
https://design-itude.com/contact-us/

In the meantime, further information about our services can be found at www.design-itude.com. For reference, we have included links to our residential brochures below.

Residential Architecture
https://design-itude.com/dia-residential-architecture/

Residential Interior Design
https://design-itude.com/dia-residential-interior/

We would be pleased to offer initial guidance on the most suitable way forward once we have a clearer understanding of your requirements.

Kind Regards,
Omnia Medhat
Egypt Studio Manager | DiA - Design-Itude Associates

-----------------------
{disclaimer}"""

COMMERCIAL_BODY = """Hello {client_name},

It's great to hear you are considering starting a new project! We are emailing you as we got your contact details regarding your enquiry.

Here at Design-Itude, we are a full-service architectural and interior design studio dedicated to developing inspiring, socially safe, and practical spaces, and we'd appreciate the opportunity to hear more about your project. Our architects and designers are ready to help and advise on your project, all the while delivering on budget and within your timeframe.

Are you free to chat in the next couple of days to get more details from you and possibly give you a bespoke quote? Please feel free to book a time that is convenient for you, and one of our advisers will be there to tell you more.

https://design-itude.com/contact-us/

In the meantime, please feel free to visit our website (www.design-itude.com). You can also find us on Facebook and Instagram at @designitude.associates.

I have also placed a link below, which contains our commercial brochure for your reference.
https://design-itude.com/dia-commercial-brochure/

Looking forward to hearing from you.

Kind Regards,
DiA - Design-Itude Associates.

-----------------------
{disclaimer}"""


def introduction_template_name(project_type: str | None) -> str | None:
    if project_type == "Residential":
        return "residential"
    if project_type in {"Commercial", "Retail", "Workplace"}:
        return "commercial"
    return None


def render_introduction_email(lead: Lead) -> IntroductionEmail:
    """Render a preview only. This function sends nothing."""
    template = introduction_template_name(lead.project_type)
    if template is None:
        raise ValueError("Project Type must be classified before choosing an email template")

    source = RESIDENTIAL_BODY if template == "residential" else COMMERCIAL_BODY
    return IntroductionEmail(
        to=lead.client_email,
        subject=SUBJECT,
        body=source.format(client_name=lead.client_name, disclaimer=DISCLAIMER),
        template=template,
    )
