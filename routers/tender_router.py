import logging

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.concurrency import run_in_threadpool

from helpers.ungm_scraper import scrape_ungm
from helpers.devnet_scraper import scrape_devnet

from utils.auth import require_login
from utils.template import render

from model.tender_model import (
    get_all_tenders,
    get_tender_by_id,
    tender_exists,
    create_tender
)


router = APIRouter(
    prefix="/tenders",
    tags=["Tenders"],
    dependencies=[Depends(require_login)]
)

logger = logging.getLogger(__name__)


@router.get("/")
async def index(request: Request):
    tenders = get_all_tenders()
    return render(
        request,
        "tenders/index.html",
        tenders=tenders
    )

@router.get("/list")
def tender_list_api(request: Request):
    tenders = get_all_tenders()
    return tenders

@router.get("/view/{tender_id}")
async def view_tender(
    request: Request,
    tender_id: int
):
    tender = get_tender_by_id(tender_id)
    if not tender:
        raise HTTPException(
            status_code=404,
            detail="Tender not found"
        )
    return render(
        request,
        "tenders/view.html",
        tender=tender
    )


@router.get("/scraper/run")
async def run_scraper():
    tenders = await run_in_threadpool(scrape_ungm)
    inserted = 0
    skipped = 0
    failed = 0

    for tender in tenders:
        try:
            exists = tender_exists(
                tender["source"],
                tender["external_id"]
            )
            if exists:
                skipped += 1
                continue
            create_tender(tender)
            inserted += 1

        except Exception as error:
            failed += 1
            logger.error(
                "Failed to save tender %s: %s",
                tender.get("external_id"), error
            )
    return {
        "status": "success",
        "scraped": len(tenders),
        "inserted": inserted,
        "skipped": skipped,
        "failed": failed
    }

@router.get("/scraper/test")
async def scraper_test():
    tenders = await run_in_threadpool(scrape_devnet)
    return {
        "status": "success",
        "count": len(tenders),
        "data": tenders
    }

@router.get("/scrape/devnet")
async def scrape_devnet_tenders():
    tenders = await run_in_threadpool(scrape_devnet)

    inserted = 0
    skipped = 0
    failed = 0

    for tender in tenders:
        try:
            source = tender.get("source")
            external_id = tender.get("external_id")
            if not source or not external_id:
                failed += 1
                continue
            if tender_exists(
                source,
                external_id
            ):
                skipped += 1
                continue
            create_tender(
                tender
            )
            inserted += 1
        except Exception as error:
            failed += 1
            logger.error(
                "Failed to save DevNet tender %s: %s",
                external_id, error
            )
    return {
        "status": "success",
        "scraped": len(tenders),
        "inserted": inserted,
        "skipped": skipped,
        "failed": failed
    }
