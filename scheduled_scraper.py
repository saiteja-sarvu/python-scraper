import logging
import os
from datetime import datetime

from helpers.ungm_scraper import scrape_ungm
from helpers.devnet_scraper import scrape_devnet

from model.tender_model import (
    tender_exists,
    create_tender
)


# ==========================================
# LOGGING
# ==========================================

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/scheduled_scraper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# ==========================================
# RUN SCRAPER
# ==========================================

def run_scraper(source, scraper_function):

    logger.info("========================================")
    logger.info("Starting %s scraper", source)
    logger.info("========================================")

    inserted = 0
    skipped = 0
    failed = 0

    try:

        tenders = scraper_function()

        logger.info(
            "%s tenders scraped: %s",
            source,
            len(tenders)
        )

    except Exception:

        logger.exception(
            "%s scraper failed",
            source
        )

        return {
            "scraped": 0,
            "inserted": 0,
            "skipped": 0,
            "failed": 1
        }

    for tender in tenders:

        try:

            source_name = tender.get("source")
            external_id = tender.get("external_id")

            if not source_name or not external_id:

                failed += 1

                logger.warning(
                    "Invalid tender skipped: %s",
                    tender
                )

                continue

            # Check duplicate
            if tender_exists(
                source_name,
                external_id
            ):

                skipped += 1

                logger.info(
                    "Duplicate skipped: %s - %s",
                    source_name,
                    external_id
                )

                continue

            # Insert
            create_tender(tender)

            inserted += 1

            logger.info(
                "Tender inserted: %s - %s",
                source_name,
                external_id
            )

        except Exception:

            failed += 1

            logger.exception(
                "Failed to save tender"
            )

    logger.info(
        "%s completed | scraped=%s inserted=%s skipped=%s failed=%s",
        source,
        len(tenders),
        inserted,
        skipped,
        failed
    )

    return {
        "scraped": len(tenders),
        "inserted": inserted,
        "skipped": skipped,
        "failed": failed
    }


# ==========================================
# MAIN
# ==========================================

def main():

    start_time = datetime.now()

    logger.info("")
    logger.info("========================================")
    logger.info("SCHEDULED SCRAPER STARTED")
    logger.info("Time: %s", start_time)
    logger.info("========================================")

    # --------------------------------------
    # UNGM
    # --------------------------------------

    ungm_result = run_scraper(
        "UNGM",
        scrape_ungm
    )

    # --------------------------------------
    # DEVNET
    # --------------------------------------

    devnet_result = run_scraper(
        "DEVNET",
        scrape_devnet
    )

    # --------------------------------------
    # FINAL SUMMARY
    # --------------------------------------

    logger.info("========================================")
    logger.info("SCHEDULED SCRAPER COMPLETED")
    logger.info("UNGM: %s", ungm_result)
    logger.info("DEVNET: %s", devnet_result)
    logger.info(
        "Duration: %s",
        datetime.now() - start_time
    )
    logger.info("========================================")


if __name__ == "__main__":
    main()