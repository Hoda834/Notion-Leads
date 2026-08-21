# DiA Notion Lead Automation

This repository will import lead emails from `hello@design-itude.com` into the DiA Notion lead tracker and send an introduction email.

The current workflow is read-only. It inspects the Notion database schema and does not create or update records.

## Required GitHub Actions secrets

- `NOTION_TOKEN`
- `NOTION_DATABASE_ID`

## Run the schema check

1. Open the **Actions** tab.
2. Select **Inspect Notion schema**.
3. Select **Run workflow**.
4. Open the completed run and view its job summary.

Never commit API tokens or client secrets to this repository.

## Safety state

The lead parsing, normalisation, duplicate detection, lead-number generation, and Notion payload mapping are implemented as offline functions. No production runner is included yet. The code cannot currently read Outlook, write to Notion, or send email.
