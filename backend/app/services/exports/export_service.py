"""
Export service.
Generates XLSX workbooks for 3 export types.
"""
from uuid import UUID
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.import_row import ImportRow, ImportRowStatus
from app.models.assignment import UserCourseAssignment
from app.models.attempt import TestAttempt, AttemptStatus
from app.models.user import User


HEADER_FONT = Font(bold=True, color="FFFFFF")
HEADER_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")


def _style_header(ws, headers: list[str]):
    ws.append(headers)
    for cell in ws[1]:
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center")


class ExportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def export_logins_passwords(self, batch_id: UUID) -> Workbook:
        """Export #1: logins + initial passwords (from import_rows)."""
        wb = Workbook()
        ws = wb.active
        ws.title = "Доступы"
        _style_header(ws, ["ФИО", "Логин", "Пароль", "Организация", "Должность"])

        result = await self.db.execute(
            select(ImportRow)
            .options(selectinload(ImportRow.user))
            .where(
                ImportRow.batch_id == batch_id,
                ImportRow.status == ImportRowStatus.ok,
                ImportRow.user_id.isnot(None),
            )
        )
        rows = result.scalars().all()

        for row in rows:
            u = row.user
            nd = row.normalized_data or {}
            ws.append([
                u.full_name if u else nd.get("full_name", ""),
                u.login if u else "",
                "(сброс через админку)",  # password not stored in plain
                nd.get("organization", ""),
                u.position_raw if u else nd.get("position", ""),
            ])

        return wb

    async def export_all_results(self) -> Workbook:
        """Export #2: all assignment results."""
        return await self._build_results_workbook(batch_id=None)

    async def export_batch_results(self, batch_id: UUID) -> Workbook:
        """Export #3: results for a specific batch."""
        return await self._build_results_workbook(batch_id=batch_id)

    async def _build_results_workbook(self, batch_id: UUID | None) -> Workbook:
        wb = Workbook()
        ws = wb.active
        ws.title = "Результаты"
        _style_header(ws, [
            "ФИО", "Организация", "Должность",
            "Дисциплина", "Курс", "Статус",
            "% результат", "Сдал/не сдал", "Дата прохождения"
        ])

        q = (
            select(UserCourseAssignment)
            .options(
                selectinload(UserCourseAssignment.user),
                selectinload(UserCourseAssignment.course),
                selectinload(UserCourseAssignment.discipline),
                selectinload(UserCourseAssignment.attempts),
            )
        )
        if batch_id:
            q = q.where(UserCourseAssignment.batch_id == batch_id)

        result = await self.db.execute(q)
        assignments = result.scalars().all()

        for a in assignments:
            u = a.user
            best_attempt = None
            if a.attempts:
                completed = [x for x in a.attempts if x.status == AttemptStatus.completed]
                if completed:
                    best_attempt = max(completed, key=lambda x: x.score_percent or 0)

            ws.append([
                u.full_name if u else "",
                "",  # organization — join if needed
                u.position_raw if u else "",
                a.discipline.name if a.discipline else "",
                a.course.name if a.course else "",
                a.status.value,
                best_attempt.score_percent if best_attempt else "",
                "Да" if (best_attempt and best_attempt.passed) else "Нет" if best_attempt else "",
                a.completed_at.strftime("%d.%m.%Y") if a.completed_at else "",
            ])

        return wb
