from dataclasses import dataclass
import os


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().casefold() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    tenant_id: str
    client_id: str
    client_secret: str
    mailbox: str
    notion_token: str
    notion_data_source_id: str
    enable_writes: bool
    send_introduction_email: bool
    project_manager_id: str | None
    max_messages: int

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            tenant_id=_required("MS_TENANT_ID"),
            client_id=_required("MS_CLIENT_ID"),
            client_secret=_required("MS_CLIENT_SECRET"),
            mailbox=os.getenv("OUTLOOK_MAILBOX", "hello@design-itude.com").strip(),
            notion_token=_required("NOTION_TOKEN"),
            notion_data_source_id=_required("NOTION_DATA_SOURCE_ID"),
            enable_writes=_flag("ENABLE_WRITES", False),
            send_introduction_email=_flag("SEND_INTRODUCTION_EMAIL", False),
            project_manager_id=os.getenv("NOTION_PROJECT_MANAGER_ID", "").strip() or None,
            max_messages=max(1, min(int(os.getenv("MAX_MESSAGES", "50")), 250)),
        )
