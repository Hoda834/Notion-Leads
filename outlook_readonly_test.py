"""Safely verify app-only read access to the DiA leads mailbox."""

import os
import sys

import requests


GRAPH_ROOT = "https://graph.microsoft.com/v1.0"
MAILBOX = "hello@design-itude.com"


def required_secret(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing GitHub secret: {name}")
    return value


def main() -> int:
    tenant_id = required_secret("MS_TENANT_ID")
    client_id = required_secret("MS_CLIENT_ID")
    client_secret = required_secret("MS_CLIENT_SECRET")

    token_response = requests.post(
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        },
        timeout=30,
    )
    token_response.raise_for_status()
    access_token = token_response.json()["access_token"]

    # Request one message ID only. No subject, sender, body, attachments, or
    # message content is printed or retained.
    mailbox_response = requests.get(
        f"{GRAPH_ROOT}/users/{MAILBOX}/mailFolders/inbox/messages",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"$top": "1", "$select": "id"},
        timeout=30,
    )

    if not mailbox_response.ok:
        print(f"READ TEST FAILED: Microsoft Graph returned {mailbox_response.status_code}.")
        print("No mailbox content was printed.")
        return 1

    message_count = len(mailbox_response.json().get("value", []))
    print("AUTHENTICATION: PASSED")
    print(f"MAILBOX READ ACCESS ({MAILBOX}): PASSED")
    print(f"SAFE QUERY RESULT: {message_count} item(s) returned; content not displayed")
    print("NOTION WRITE: NOT ATTEMPTED")
    print("EMAIL SEND: NOT ATTEMPTED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except requests.RequestException as exc:
        status = exc.response.status_code if exc.response is not None else "network error"
        print(f"AUTHENTICATION TEST FAILED: {status}")
        print("No secret or mailbox content was printed.")
        raise SystemExit(1) from None
    except (KeyError, RuntimeError) as exc:
        print(f"CONFIGURATION ERROR: {exc}")
        raise SystemExit(1) from None
