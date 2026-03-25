from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
import io

from app.api.deps import CurrentAdmin, DB

router = APIRouter()


@router.get("/logins-passwords")
async def export_logins_passwords(
    db: DB,
    admin: CurrentAdmin,
    batch_id: UUID = Query(...),
):
    """Export #1: logins and (initial) passwords for a batch."""
    from app.services.exports.export_service import ExportService
    service = ExportService(db)
    workbook = await service.export_logins_passwords(batch_id)

    stream = io.BytesIO()
    workbook.save(stream)
    stream.seek(0)

    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=logins_batch_{batch_id}.xlsx"},
    )


@router.get("/results")
async def export_all_results(db: DB, admin: CurrentAdmin):
    """Export #2: results for all users."""
    from app.services.exports.export_service import ExportService
    service = ExportService(db)
    workbook = await service.export_all_results()

    stream = io.BytesIO()
    workbook.save(stream)
    stream.seek(0)

    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=results_all.xlsx"},
    )


@router.get("/batches/{batch_id}")
async def export_batch_results(batch_id: UUID, db: DB, admin: CurrentAdmin):
    """Export #3: results for a specific batch."""
    from app.services.exports.export_service import ExportService
    service = ExportService(db)
    workbook = await service.export_batch_results(batch_id)

    stream = io.BytesIO()
    workbook.save(stream)
    stream.seek(0)

    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=results_batch_{batch_id}.xlsx"},
    )
