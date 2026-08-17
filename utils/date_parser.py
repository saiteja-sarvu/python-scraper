from datetime import datetime
import re


DATE_FORMATS = [
    "%d-%b-%Y",          # 23-Jul-2026
    "%d-%B-%Y",          # 23-July-2026
    "%d/%m/%Y",          # 23/07/2026
    "%d-%m-%Y",           # 23-07-2026
    "%Y-%m-%d",           # 2026-07-23
    "%d %b %Y",           # 23 Jul 2026
    "%d %B %Y",           # 23 July 2026
    "%B %d, %Y",          # July 23, 2026
]


DATETIME_FORMATS = [
    "%d-%b-%Y %H:%M",
    "%d-%B-%Y %H:%M",
    "%d/%m/%Y %H:%M",
    "%d-%m-%Y %H:%M",
    "%Y-%m-%d %H:%M",
    "%d %b %Y %H:%M",
    "%d %B %Y %H:%M",
    "%B %d, %Y %H:%M",
]


def parse_date(value):
    if not value:
        return None

    value = " ".join(value.split()).strip()

    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(
                value,
                fmt
            ).date()

        except ValueError:
            continue

    return None


def parse_deadline(value):
    """
    Parse deadline dynamically.

    Examples:
        06-Aug-2026 06:00 (GMT -4.00)
        10 Aug 2026
        10-Aug-2026
        10/08/2026
        Aug 16, 2026, at 23:59 PM

    Returns:
        (datetime, timezone)
    """

    if not value:
        return None, None

    value = " ".join(value.split()).strip()

    timezone = None

    # ---------------------------------
    # Extract GMT timezone
    # ---------------------------------

    timezone_match = re.search(
        r"\((GMT\s*[+-]\s*\d+(?:\.\d+)?)\)",
        value,
        re.IGNORECASE
    )

    if timezone_match:

        timezone = timezone_match.group(1)

        value = re.sub(
            r"\s*\(GMT.*?\)",
            "",
            value,
            flags=re.IGNORECASE
        ).strip()

    # ---------------------------------
    # Normalize "at"
    #
    # Aug 16, 2026, at 23:59 PM
    # ↓
    # Aug 16, 2026, 23:59 PM
    # ---------------------------------

    value = re.sub(
        r",?\s+at\s+",
        " ",
        value,
        flags=re.IGNORECASE
    ).strip()

    # ---------------------------------
    # Normalize 24-hour time with AM/PM
    #
    # 23:59 PM → 23:59
    # 06:00 AM → 06:00
    #
    # This handles websites that append
    # AM/PM incorrectly to 24-hour times.
    # ---------------------------------

    value = re.sub(
        r"(\d{2}:\d{2})\s*(AM|PM)\b",
        r"\1",
        value,
        flags=re.IGNORECASE
    ).strip()

    # ---------------------------------
    # Try datetime formats
    # ---------------------------------

    for fmt in DATETIME_FORMATS:

        try:
            deadline = datetime.strptime(
                value,
                fmt
            )

            return deadline, timezone

        except ValueError:
            continue

    # ---------------------------------
    # Try date-only formats
    # ---------------------------------

    for fmt in DATE_FORMATS:

        try:
            parsed_date = datetime.strptime(
                value,
                fmt
            )

            return parsed_date, timezone

        except ValueError:
            continue

    return None, timezone