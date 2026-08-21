# DiA Notion Lead Automation

This repository will import lead emails from `hello@design-itude.com` into the DiA Notion lead tracker and send an introduction email.

The repository now contains the complete automation, but production actions are deliberately disabled. The workflow can read Outlook and Notion in dry-run mode; it cannot create a Notion lead or send an introduction email unless explicit safety switches are enabled later.

## Required GitHub Actions secrets

- `NOTION_TOKEN`
- `NOTION_DATABASE_ID` (schema inspection only)
- `NOTION_DATA_SOURCE_ID`
- `MS_TENANT_ID`
- `MS_CLIENT_ID`
- `MS_CLIENT_SECRET`

Microsoft Graph application permissions required from the Microsoft 365 admin:

- `Mail.Read` (Application)
- `Mail.Send` (Application)
- Admin consent for both permissions

For least privilege, the admin should also restrict the application to `hello@design-itude.com` using the Microsoft 365 application access policy / Exchange application RBAC appropriate to the tenant.

## Run the schema check

1. Open the **Actions** tab.
2. Select **Inspect Notion schema**.
3. Select **Run workflow**.
4. Open the completed run and view its job summary.

Never commit API tokens or client secrets to this repository.

## Implemented rules

- Local Surveyors HTML email parsing, including noisy table-based messages
- Correct name capitalisation
- UK phone normalisation to `0044...`; invalid placeholders such as `0000` are omitted
- Postcode normalisation and country/location `UK`
- Project Type and Discipline classification
- `Lead Source = Local Surveyors`
- `Status = Lead | Consultation Phase`
- Lead numbering as `L1-YY-#####`
- Exact Outlook message-ID duplicate detection plus active-contact duplicate rules
- `Project Name` and `Project Notes` are never populated
- Service, role, information and immutable Outlook message reference are saved in the page body
- Introduction email template is a clearly marked placeholder

## Safety state

- The twice-daily schedule is not enabled.
- `ENABLE_WRITES=false` prevents Notion creation.
- `SEND_INTRODUCTION_EMAIL=false` prevents sending.
- The GitHub workflow is manual-only and forces both switches to `false`.
- Do not enable either switch until the admin permissions and a controlled test lead have been reviewed.

## Later activation (not for now)

After admin setup and approval of the final email text, add the secrets under **GitHub → Settings → Secrets and variables → Actions**, perform one manual dry run, perform one controlled live test, and only then enable two cron entries. Keep GitHub Actions concurrency enabled to protect lead-number sequencing.
