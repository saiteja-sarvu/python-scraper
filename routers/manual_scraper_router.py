import logging

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.concurrency import run_in_threadpool

from helpers.ungm_scraper import scrape_ungm, scrape_ungm_url
from helpers.devnet_scraper import scrape_devnet, scrape_devnet_url

from utils.auth import require_login
from utils.template import render

from model.tender_model import (
    tender_exists, create_tender
)

router = APIRouter(
    prefix="/manual-scraper",
    tags=["Manual Scraper"],
    dependencies=[Depends(require_login)]
)

logger = logging.getLogger(__name__)


@router.get("/")
async def index(request: Request):
    return render(
        request,
        "manual_scraper/index.html",
        result=None
    )


@router.post("/run")
async def run_manual_scraper(
    request: Request,
    source: str = Form(...)
):

    if source == "devnet":
        tenders = await run_in_threadpool(scrape_devnet)

    elif source == "ungm":
        tenders = await run_in_threadpool(scrape_ungm)

    elif source == "ngobox":
        return render(
            request,
            "manual_scraper/index.html",
            result={
                "source": source.upper(),
                "scraped": 0,
                "inserted": 0,
                "skipped": 0,
                "failed": 0,
                "message": "NGOBox scraping is not implemented yet."
            },
            selected_source=source
        )

    else:
        return render(
            request,
            "manual_scraper/index.html",
            result={
                "source": (source or "").upper(),
                "scraped": 0,
                "inserted": 0,
                "skipped": 0,
                "failed": 0,
                "message": "Unsupported source."
            },
            selected_source=source
        )

    inserted = 0
    skipped = 0
    failed = 0

    for tender in tenders:

        try:

            source_name = tender.get("source")
            external_id = tender.get("external_id")

            if not source_name or not external_id:
                failed += 1
                continue

            if tender_exists(
                source_name,
                external_id
            ):
                skipped += 1
                continue

            create_tender(tender)

            inserted += 1

        except Exception as error:

            logger.error("Failed to save tender: %s", error)

            failed += 1

    result = {
        "source": source.upper(),
        "scraped": len(tenders),
        "inserted": inserted,
        "skipped": skipped,
        "failed": failed
    }

    return render(
        request,
        "manual_scraper/index.html",
        result=result,
        selected_source=source
    )


@router.post("/scrape")
async def manual_scrape(
    request: Request
):

    form = await request.form()

    source = form.get("source")
    url = form.get("url")

    if not source or not url:
        raise HTTPException(
            status_code=400,
            detail="Source and URL are required"
        )

    source = source.upper()

    if source == "UNGM":

        tender = await run_in_threadpool(
            scrape_ungm_url,
            url
        )

    elif source == "DEVNET":

        tender = await run_in_threadpool(
            scrape_devnet_url,
            url
        )

    else:

        raise HTTPException(
            status_code=400,
            detail="Unsupported source"
        )

    if not tender:

        raise HTTPException(
            status_code=404,
            detail="Unable to scrape tender"
        )

    return {
        "status": "success",
        "data": tender
    }


@router.get("/test")
async def manual_scraper_test(
    source: str,
    url: str
):

    source = source.upper()

    if source == "UNGM":

        tender = await run_in_threadpool(
            scrape_ungm_url,
            url
        )

    elif source == "DEVNET":

        tender = await run_in_threadpool(
            scrape_devnet_url,
            url
        )

    else:

        raise HTTPException(
            status_code=400,
            detail="Unsupported source"
        )

    if not tender:

        raise HTTPException(
            status_code=404,
            detail="Tender could not be scraped"
        )

    return {
        "status": "success",
        "data": tender
    }
