import logging
import re

from playwright.sync_api import sync_playwright

from utils.date_parser import parse_date, parse_deadline

logger = logging.getLogger(__name__)


DEVNET_URL = "https://www.devnetjobsindia.org/rfp_assignments.aspx"
DEVNET_BASE_URL = "https://www.devnetjobsindia.org"


def scrape_devnet():
    """
    Scrape RFPs / Tenders from DevNet Jobs India.

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
                DEVNET_URL,
                wait_until="domcontentloaded",
                timeout=60000
            )

            page.wait_for_load_state(
                "networkidle",
                timeout=60000
            )

            links = page.locator(
                'a[href*="jobdescription.aspx?job_id="]'
            )

            total_links = links.count()

            logger.info("DevNet links found: %s", total_links)

            processed_ids = set()

            for index in range(total_links):

                link = links.nth(index)

                try:

                    title = link.inner_text().strip()

                    href = link.get_attribute(
                        "href"
                    )

                    if not href:
                        continue

                    # Only RFP / Tender / EOI records
                    if not _is_tender(title):
                        continue

                    source_url = _build_url(
                        href
                    )

                    external_id = _extract_job_id(
                        source_url
                    )

                    if not external_id:
                        continue

                    # Prevent duplicate links
                    if external_id in processed_ids:
                        continue

                    processed_ids.add(
                        external_id
                    )

                    tender = _extract_tender(
                        browser,
                        source_url
                    )

                    if tender:

                        tenders.append(
                            tender
                        )

                        logger.info("Scraped DevNet: %s", external_id)

                except Exception as error:

                    logger.error(
                        "Failed DevNet record %s: %s",
                        index + 1, error
                    )

        except Exception as error:

            logger.error("DevNet scraping failed: %s", error)

        finally:

            browser.close()

    logger.info("Total DevNet tenders: %s", len(tenders))

    return tenders


# ==========================================
# EXTRACT SINGLE TENDER
# ==========================================

def _extract_tender(browser, source_url):

    page = browser.new_page()

    try:

        page.goto(
            source_url,
            wait_until="domcontentloaded",
            timeout=60000
        )

        page.wait_for_load_state(
            "networkidle",
            timeout=60000
        )

        body_text = page.locator(
            "body"
        ).inner_text()

        if not body_text:
            return None

        # ----------------------------------
        # External ID
        # ----------------------------------

        external_id = _extract_job_id(
            source_url
        )

        # ----------------------------------
        # Title
        # ----------------------------------

        title = _extract_title(
            page,
            body_text
        )

        # ----------------------------------
        # Organization
        # ----------------------------------

        organization = _extract_organization(
            page,
            body_text
        )

        # ----------------------------------
        # Location
        # ----------------------------------

        location = _extract_line_value(
            body_text,
            "Location:"
        )

        # ----------------------------------
        # Country
        # ----------------------------------

        country = _extract_country(
            location
        )

        # ----------------------------------
        # Deadline
        # ----------------------------------

        closing_date = _extract_closing_date(
            body_text
        )

        if closing_date:

            deadline, deadline_timezone = (
                parse_deadline(closing_date)
            )

        else:

            apply_by = _extract_line_value(
                body_text,
                "Apply by:"
            )

            deadline, deadline_timezone = (
                parse_deadline(apply_by)
            )

        # ----------------------------------
        # Published Date
        # ----------------------------------

        published_text = _extract_line_value(
            body_text,
            "Posted:"
        )

        published_date = parse_date(
            published_text
        )

        # ----------------------------------
        # Category
        # ----------------------------------

        category = _detect_category(
            title
        )

        # ----------------------------------
        # Relevant sectors
        # ----------------------------------

        keyword = _extract_sectors(
            body_text
        )

        # ----------------------------------
        # Description
        # ----------------------------------

        description = _extract_description(
            body_text
        )

        return {
            "external_id": external_id,
            "source": "DEVNET",
            "source_url": source_url,
            "reference_number": None,
            "title": title,
            "organization": organization,
            "country": country,
            "published_date": published_date,
            "deadline": deadline,
            "deadline_timezone": deadline_timezone,
            "category": category,
            "keyword": keyword,
            "description": description,
            "status": "new",
        }

    except Exception as error:

        logger.error(
            "Failed to extract DevNet tender %s: %s",
            source_url, error
        )

        return None

    finally:

        page.close()


# ==========================================
# TITLE
# ==========================================

def _extract_title(page, body_text):

    # Try common heading elements first

    for selector in [
        "h1",
        "h2",
        "h3",
        ".jobtitle",
        ".job_title",
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

            if text and "Job ID:" not in text:

                return text

    # Fallback: locate text after Job ID

    lines = [
        line.strip()
        for line in body_text.splitlines()
        if line.strip()
    ]

    for index, line in enumerate(lines):

        if line.lower().startswith(
            "job id:"
        ):

            if index + 1 < len(lines):

                return lines[
                    index + 1
                ]

    return None


# ==========================================
# ORGANIZATION
# ==========================================

def _extract_organization(
    page,
    body_text
):

    lines = [
        line.strip()
        for line in body_text.splitlines()
        if line.strip()
    ]

    for index, line in enumerate(lines):

        if line.lower().startswith(
            "location:"
        ):

            if index > 0:

                organization = lines[
                    index - 1
                ]

                if (
                    organization
                    and not organization.lower()
                    .startswith("job id:")
                ):

                    return organization

    return None


# ==========================================
# LOCATION
# ==========================================

def _extract_line_value(
    text,
    label
):

    for line in text.splitlines():

        line = line.strip()

        if line.lower().startswith(
            label.lower()
        ):

            return line[
                len(label):
            ].strip()

    return None


# ==========================================
# COUNTRY
# ==========================================

def _extract_country(location):

    if not location:
        return None

    # DevNet commonly provides:
    #
    # Location: India
    #
    # or:
    #
    # Location: Hyderabad, Telangana

    location_lower = location.lower()

    indian_locations = [
        "india",
        "delhi",
        "mumbai",
        "hyderabad",
        "bangalore",
        "bengaluru",
        "chennai",
        "kolkata",
        "pune",
        "lucknow",
        "patna",
        "jaipur",
        "ahmedabad",
        "guwahati",
        "assam",
        "uttar pradesh",
        "telangana",
        "maharashtra",
        "karnataka",
        "tamil nadu",
        "west bengal",
        "bihar",
        "rajasthan",
    ]

    if any(
        item in location_lower
        for item in indian_locations
    ):

        return "India"

    return location


# ==========================================
# CLOSING DATE
# ==========================================

def _extract_closing_date(text):

    match = re.search(
        r"Closing Date for Submission\s+"
        r"([A-Za-z]+\s+\d{1,2},\s+\d{4}"
        r"(?:,\s*at\s+|\s+)"
        r"\d{1,2}:\d{2}\s*(?:AM|PM)?)",
        text,
        re.IGNORECASE
    )

    if match:

        return match.group(1).strip()

    return None


# ==========================================
# CATEGORY
# ==========================================

def _detect_category(title):

    if not title:
        return None

    title_lower = title.lower()

    if (
        "request for proposal" in title_lower
        or "rfp" in title_lower
    ):
        return "RFP"

    if (
        "request for quotation" in title_lower
        or "rfq" in title_lower
    ):
        return "RFQ"

    if (
        "expression of interest" in title_lower
        or "eoi" in title_lower
    ):
        return "EOI"

    if "tender" in title_lower:
        return "Tender"

    return None


# ==========================================
# RELEVANT SECTORS
# ==========================================

def _extract_sectors(text):

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    for index, line in enumerate(lines):

        if line.lower() == "relevant sectors":

            sectors = []

            for next_line in lines[
                index + 1:
            ]:

                upper_line = (
                    next_line.upper()
                )

                if upper_line.startswith(
                    (
                        "REQUEST FOR",
                        "EXPRESSION OF",
                        "TENDER",
                    )
                ):
                    break

                sectors.append(
                    next_line
                )

            return ", ".join(
                sectors
            ) or None

    return None


# ==========================================
# DESCRIPTION
# ==========================================

def _extract_description(text):

    if not text:
        return None

    start_position = None

    markers = [
        "REQUEST FOR PROPOSAL",
        "REQUEST FOR QUOTATION",
        "EXPRESSION OF INTEREST",
        "TENDER",
    ]

    upper_text = text.upper()

    for marker in markers:

        position = upper_text.find(
            marker
        )

        if position != -1:

            if (
                start_position is None
                or position < start_position
            ):

                start_position = position

    if start_position is not None:

        text = text[
            start_position:
        ]

    # Remove website footer

    end_markers = [
        "\nDisclaimer",
        "\nPrivacy Policy",
        "\nTerms & Conditions",
        "\nRecruitment Exchange",
    ]

    for marker in end_markers:

        position = text.find(
            marker
        )

        if position != -1:

            text = text[
                :position
            ]

    return text.strip() or None


# ==========================================
# CHECK WHETHER LINK IS A TENDER
# ==========================================

def _is_tender(title):

    if not title:
        return False

    title_lower = title.lower()

    keywords = [
        "rfp",
        "request for proposal",
        "tender",
        "rfq",
        "request for quotation",
        "eoi",
        "expression of interest",
    ]

    return any(
        keyword in title_lower
        for keyword in keywords
    )


# ==========================================
# BUILD URL
# ==========================================

def _build_url(href):

    if href.startswith("http"):

        return href

    return (
        f"{DEVNET_BASE_URL}/"
        f"{href.lstrip('/')}"
    )


# ==========================================
# EXTRACT JOB ID
# ==========================================

def _extract_job_id(url):

    match = re.search(
        r"job_id=(\d+)",
        url,
        re.IGNORECASE
    )

    if match:

        return match.group(1)

    return None

def scrape_devnet_url(source_url):
    """
    Scrape a single DevNet tender URL.
    """

    external_id = _extract_job_id(source_url)

    if not external_id:
        raise ValueError("Invalid DevNet tender URL")

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        try:
            tender = _extract_tender(
                browser,
                source_url
            )

            return tender

        finally:
            browser.close()