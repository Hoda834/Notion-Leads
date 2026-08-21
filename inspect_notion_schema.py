import json
import os
import sys

import requests


NOTION_VERSION = "2026-03-11"
API_BASE = "https://api.notion.com/v1"


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def notion_get(path: str, token: str) -> dict:
    response = requests.get(
        f"{API_BASE}{path}",
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
        timeout=30,
    )
    if not response.ok:
        try:
            detail = response.json().get("message", response.text)
        except ValueError:
            detail = response.text
        raise RuntimeError(f"Notion API returned {response.status_code}: {detail}")
    return response.json()


def plain_text(items: list[dict]) -> str:
    return "".join(item.get("plain_text", "") for item in items)


def main() -> int:
    token = require_env("NOTION_TOKEN")
    database_id = require_env("NOTION_DATABASE_ID")

    database = notion_get(f"/databases/{database_id}", token)
    title = plain_text(database.get("title", [])) or "Untitled database"
    data_sources = database.get("data_sources", [])
    if not data_sources:
        raise RuntimeError("The database has no data sources, or the token cannot see them.")

    result = {
        "database_title": title,
        "database_id": database.get("id", database_id),
        "data_sources": [],
    }

    for source_ref in data_sources:
        source = notion_get(f"/data_sources/{source_ref['id']}", token)
        properties = [
            {
                "name": name,
                "id": prop.get("id"),
                "type": prop.get("type"),
            }
            for name, prop in source.get("properties", {}).items()
        ]
        properties.sort(key=lambda item: item["name"].casefold())
        result["data_sources"].append(
            {
                "name": source_ref.get("name") or source.get("name") or "Unnamed data source",
                "id": source_ref["id"],
                "properties": properties,
            }
        )

    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    print(rendered)

    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write("## Notion schema inspection\n\n")
            summary.write("```json\n")
            summary.write(rendered)
            summary.write("\n```\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
