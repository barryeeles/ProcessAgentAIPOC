"""POST /api/upload — receives one or two Excel files and runs the ingestion pipeline."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from ingestion.pipeline import run_ingestion

router = APIRouter()


@router.post("/upload")
async def upload_files(
    main_file: UploadFile | None = File(None),
    releases_file: UploadFile | None = File(None),
) -> JSONResponse:
    """
    Accept EPIC.xlsx and/or EPIC Releases.xlsx as multipart file uploads.
    At least one file must be provided. Runs the ingestion pipeline and
    returns a summary of what was processed.
    """
    if not main_file and not releases_file:
        raise HTTPException(status_code=422, detail="At least one file must be uploaded.")

    main_bytes = await main_file.read() if main_file else None
    releases_bytes = await releases_file.read() if releases_file else None

    try:
        result = run_ingestion(
            main_bytes=main_bytes,
            releases_bytes=releases_bytes,
            main_filename=main_file.filename if main_file else "EPIC.xlsx",
            releases_filename=releases_file.filename if releases_file else "EPIC Releases.xlsx",
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return JSONResponse(content=result)
