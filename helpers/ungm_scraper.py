import logging

from playwright.sync_api import sync_playwright
from utils.date_parser import parse_date, parse_deadline

logger = logging.getLogger(__name__)


UNGM_URL = "https://www.ungm.org/Public/Notice"
UNGM_BASE_URL = "https://www.ungm.org"



def scrape_ungm():
    """
    Scrape currently listed procurement opportunities
    from UNGM.

    Returns:
        list[dict]
    """

    tenders = []

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        try:
            page = browser.new_page()

            page.goto(
                UNGM_URL,
                wait_until="domcontentloaded",
                timeout=60000
            )

            page.wait_for_selector(
                "[data-noticeid]",
                timeout=60000
            )

            rows = page.locator("[data-noticeid]")

            total_rows = rows.count()

            logger.info("UNGM tenders found: %s", total_rows)

            for index in range(total_rows):

                row = rows.nth(index)

                try:
                    tender = _extract_tender(row)

                    if tender:
                        tenders.append(tender)

                except Exception as error:
                    logger.error(
                        "Failed to process UNGM row %s: %s",
                        index + 1, error
                    )

        finally:
            browser.close()

    return tenders


# =================================
# EXTRACT SINGLE TENDER
# =================================

def _extract_tender(row):

    cells = row.locator('[role="cell"]')

    # ---------------------------------
    # Notice ID
    # ---------------------------------

    external_id = row.get_attribute(
        "data-noticeid"
    )


    title_link = row.locator(
        '.resultTitle a[href*="/Public/Notice/"]'
    )

    if title_link.count() == 0:
        logger.warning(
            "UNGM row has no tender link. Skipping row."
        )
        return None

    # ---------------------------------
    # Title
    # ---------------------------------

    try:
        title = title_link.inner_text(
            timeout=5000
        ).strip()
    except Exception as error:

        logger.warning(
            "Unable to read UNGM title. Skipping row: %s",
            error
        )

        return None

    relative_url = title_link.get_attribute(
        "href",
        timeout=5000
    )

    source_url = (
        f"{UNGM_BASE_URL}{relative_url}"
        if relative_url
        else None
    )

    # ---------------------------------
    # Deadline
    # ---------------------------------

    deadline_text = (
        cells.nth(2)
        .locator("span")
        .first
        .inner_text()
        .strip()
    )

    deadline, deadline_timezone = parse_deadline(deadline_text)


    # ---------------------------------
    # Published Date
    # ---------------------------------

    published_text = (
        cells.nth(3)
        .inner_text()
        .strip()
    )

    published_date = parse_date(published_text)

    # ---------------------------------
    # Organization
    # ---------------------------------

    organization = (
        cells.nth(4)
        .inner_text()
        .strip()
    )

    # ---------------------------------
    # Opportunity Type
    # ---------------------------------

    category = (
        cells.nth(5)
        .inner_text()
        .strip()
    )

    # ---------------------------------
    # Reference Number
    # ---------------------------------

    reference_number = (
        cells.nth(6)
        .inner_text()
        .strip()
    )

    # ---------------------------------
    # Country
    # ---------------------------------

    country = (
        cells.nth(7)
        .inner_text()
        .strip()
    )

    # ---------------------------------
    # Final Tender Data
    # ---------------------------------

    return {
        "external_id": external_id,
        "source": "UNGM",
        "source_url": source_url,
        "reference_number": reference_number,
        "title": title,
        "organization": organization,
        "country": country,
        "published_date": published_date,
        "deadline": deadline,
        "deadline_timezone": deadline_timezone,
        "category": category,
        "keyword": None,
        "description": None,
        "status": "new",
    }
      
# =================================
# SCRAPE SINGLE UNGM TENDER URL
# =================================

def scrape_ungm_url(source_url):
    """
    Scrape a single UNGM tender detail page.
    """

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        try:

            page = browser.new_page()

            page.goto(
                source_url,
                wait_until="domcontentloaded",
                timeout=60000
            )

            try:
                page.wait_for_load_state(
                    "networkidle",
                    timeout=60000
                )
            except Exception as error:
                logger.warning(
                    "UNGM detail page never reached networkidle for %s: %s",
                    source_url,
                    error
                )

            return _extract_tender_from_page(
                page,
                source_url
            )

        finally:

            browser.close()


def _extract_tender_from_page(
    page,
    source_url
):

    body_text = page.locator(
        "body"
    ).inner_text()

    if not body_text:
        return None

    # ---------------------------------
    # External ID
    # ---------------------------------

    external_id = _extract_notice_id(
        source_url,
        body_text
    )

    # ---------------------------------
    # Title
    # ---------------------------------

    title = _extract_page_title(page)

    # ---------------------------------
    # Organization
    # ---------------------------------

    organization = _extract_field(
        body_text,
        [
            "UN Organization",
            "Organization"
        ]
    )

    # ---------------------------------
    # Country
    # ---------------------------------

    country = _extract_field(
        body_text,
        [
            "Country"
        ]
    )

    # ---------------------------------
    # Deadline
    # ---------------------------------

    deadline_text = _extract_field(
        body_text,
        [
            "Deadline",
            "Closing Date"
        ]
    )

    deadline, deadline_timezone = (
        parse_deadline(deadline_text)
    )

    # ---------------------------------
    # Published Date
    # ---------------------------------

    published_text = _extract_field(
        body_text,
        [
            "Published",
            "Published Date"
        ]
    )

    published_date = parse_date(
        published_text
    )

    # ---------------------------------
    # Category
    # ---------------------------------

    category = _extract_field(
        body_text,
        [
            "Procurement Type",
            "Opportunity Type"
        ]
    )

    # ---------------------------------
    # Reference Number
    # ---------------------------------

    reference_number = _extract_field(
        body_text,
        [
            "Reference Number"
        ]
    )

    # ---------------------------------
    # Description
    # ---------------------------------

    description = _extract_description(
        body_text
    )

    return {
        "external_id": external_id,
        "source": "UNGM",
        "source_url": source_url,
        "reference_number": reference_number,
        "title": title,
        "organization": organization,
        "country": country,
        "published_date": published_date,
        "deadline": deadline,
        "deadline_timezone": deadline_timezone,
        "category": category,
        "keyword": None,
        "description": description,
        "status": "new",
    }
    
# =================================
# EXTRACT NOTICE ID
# =================================

def _extract_notice_id(
    source_url,
    body_text
):

    import re

    match = re.search(
        r"/Public/Notice/(\d+)",
        source_url,
        re.IGNORECASE
    )

    if match:
        return match.group(1)

    match = re.search(
        r"Notice ID\s*:?\s*(\d+)",
        body_text,
        re.IGNORECASE
    )

    if match:
        return match.group(1)

    return None


# =================================
# TITLE
# =================================

def _extract_page_title(page):

    for selector in [
        "h1",
        "h2",
        ".notice-title",
        ".resultTitle",
        "title"
    ]:

        locator = page.locator(
            selector
        )

        if locator.count():

            text = (
                locator.first
                .inner_text()
                .strip()
            )

            if text:
                return text

    return None


# =================================
# EXTRACT FIELD
# =================================

def _extract_field(
    text,
    labels
):

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    for index, line in enumerate(lines):

        for label in labels:

            if line.lower().startswith(
                label.lower()
            ):

                value = line[
                    len(label):
                ].strip(
                    " :\t"
                )

                if value:
                    return value

                if index + 1 < len(lines):
                    return lines[
                        index + 1
                    ]

    return None


# =================================
# DESCRIPTION
# =================================

def _extract_description(text):

    if not text:
        return None

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    description_started = False
    description = []

    for line in lines:

        lower_line = line.lower()

        if lower_line in [
            "description",
            "notice description",
            "short description"
        ]:
            description_started = True
            continue

        if description_started:

            # Stop when another major field starts
            if lower_line in [
                "contact information",
                "documents",
                "attachments",
                "deadline",
                "closing date",
                "submission information"
            ]:
                break

            description.append(line)

    return "\n".join(
        description
    ).strip() or None