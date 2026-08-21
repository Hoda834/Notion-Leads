import re


INVALID_PHONE_VALUES = {"", "0", "00", "000", "0000", "n/a", "na", "none"}


def normalise_email(value: str | None) -> str:
    return (value or "").strip().casefold()


def normalise_postcode(value: str | None) -> str:
    compact = re.sub(r"\s+", "", (value or "").upper())
    if len(compact) > 3:
        return f"{compact[:-3]} {compact[-3:]}"
    return compact


def proper_name(value: str) -> str:
    cleaned = " ".join(value.strip().split())

    def capitalise_piece(piece: str) -> str:
        return "-".join(
            "'".join(part[:1].upper() + part[1:].lower() for part in segment.split("'"))
            for segment in piece.split("-")
        )

    return " ".join(capitalise_piece(piece) for piece in cleaned.split(" "))


def normalise_uk_phone(value: str | None) -> str | None:
    raw = (value or "").strip().casefold()
    if raw in INVALID_PHONE_VALUES:
        return None

    digits = re.sub(r"\D", "", raw)
    if digits in INVALID_PHONE_VALUES:
        return None

    if digits.startswith("0044"):
        national = digits[4:].lstrip("0")
    elif digits.startswith("44"):
        national = digits[2:].lstrip("0")
    elif digits.startswith("0"):
        national = digits[1:]
    else:
        return None

    # UK geographic and mobile numbers normally have ten digits after country code.
    if len(national) != 10:
        return None
    return f"0044{national}"
