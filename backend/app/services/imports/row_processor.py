"""
Import row processor v2.

Flow:
  batch.discipline_ids (selected by admin)  find courses per discipline
  Excel: ФИО, Должность, Организация  (no disciplines column needed)
  For each row:
    1. Get or create Organization by name
    2. Duplicate check (normalized_full_name + org_id)
    3. Create user (login/password)
    4. For each discipline  find course by target_positions match
    5. Create UserCourseAssignment
    6. Log ImportRow
Returns summary + credentials list.
"""
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.batch import TrainingBatch
from app.models.import_row import ImportRow, ImportRowStatus
from app.models.assignment import UserCourseAssignment, AssignmentStatus
from app.models.discipline import Discipline
from app.models.course import Course
from app.models.organization import Organization
from app.models.user import User
from app.services.imports.parser import ImportParserService
from app.services.users.factory import UserFactoryService
from app.services.positions.normalizer import normalize_position, positions_match


class ImportRowProcessor:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_or_create_org(self, name: str):
        norm = name.strip().lower()
        result = await self.db.execute(select(Organization))
        for org in result.scalars().all():
            if org.name.strip().lower() == norm:
                return org
        org = Organization(name=name.strip(), is_active=True)
        self.db.add(org)
        await self.db.flush()
        return org

    async def _find_course_for_position(self, discipline_id: UUID, norm_position: str):
        result = await self.db.execute(
            select(Course)
            .where(Course.discipline_id == discipline_id, Course.is_active == True)
            .order_by(Course.name)
        )
        courses = result.scalars().all()
        generic = None
        for course in courses:
            tp = (course.target_positions or "").strip()
            if not tp:
                generic = course
                continue
            for kw in [k.strip() for k in tp.replace(";", ",").split(",") if k.strip()]:
                if positions_match(kw, norm_position):
                    return course
        return generic

    async def process_batch(self, batch: TrainingBatch) -> dict:
        parser = ImportParserService()
        preview = parser.parse_preview(batch.excel_file_path)
        if "error" in preview:
            return {"error": preview["error"]}

        user_factory = UserFactoryService(self.db)

        batch_disciplines: list[Discipline] = []
        for did_str in (batch.discipline_ids or []):
            r = await self.db.execute(select(Discipline).where(Discipline.id == did_str))
            d = r.scalar_one_or_none()
            if d:
                batch_disciplines.append(d)

        credentials: list[dict] = []
        created_count = duplicate_count = error_count = manual_count = 0

        for row in preview["rows"]:
            if row["status"] == "error":
                self.db.add(ImportRow(
                    batch_id=batch.id, row_number=row["row_number"],
                    raw_data=row["raw"], status=ImportRowStatus.error,
                    error_message="; ".join(row["warnings"]),
                ))
                error_count += 1
                continue

            full_name = row["full_name"]
            position_raw = row["position"]
            org_name = row.get("organization", "").strip()
            norm_name = UserFactoryService.normalize_full_name(full_name)
            norm_position = normalize_position(position_raw)

            org = await self._get_or_create_org(org_name) if org_name else None
            org_id = org.id if org else None

            dup_q = select(User).where(User.normalized_full_name == norm_name)
            if org_id:
                dup_q = dup_q.where(User.organization_id == org_id)
            existing = (await self.db.execute(dup_q)).scalar_one_or_none()

            if existing:
                self.db.add(ImportRow(
                    batch_id=batch.id, row_number=row["row_number"],
                    raw_data=row["raw"], status=ImportRowStatus.duplicate,
                    error_message="Пользователь уже существует", user_id=existing.id,
                ))
                duplicate_count += 1
                for disc in batch_disciplines:
                    course = await self._find_course_for_position(disc.id, norm_position)
                    if course:
                        already = (await self.db.execute(
                            select(UserCourseAssignment).where(
                                UserCourseAssignment.user_id == existing.id,
                                UserCourseAssignment.course_id == course.id,
                            )
                        )).scalar_one_or_none()
                        if not already:
                            self.db.add(UserCourseAssignment(
                                user_id=existing.id, course_id=course.id,
                                discipline_id=disc.id, batch_id=batch.id,
                                status=AssignmentStatus.assigned,
                            ))
                continue

            user, plain_password = await user_factory.create_user(
                full_name=full_name, organization_id=org_id,
                position_raw=position_raw, batch_id=batch.id,
            )

            assigned_courses = []
            no_course_discs = []
            for disc in batch_disciplines:
                course = await self._find_course_for_position(disc.id, norm_position)
                if course:
                    self.db.add(UserCourseAssignment(
                        user_id=user.id, course_id=course.id,
                        discipline_id=disc.id, batch_id=batch.id,
                        status=AssignmentStatus.assigned,
                    ))
                    assigned_courses.append(f"{disc.name}: {course.name}")
                else:
                    no_course_discs.append(disc.name)

            credentials.append({
                "num": created_count + duplicate_count + 1,
                "full_name": full_name,
                "organization": org_name or "",
                "position": position_raw,
                "login": user.login,
                "password": plain_password,
                "courses": ", ".join(assigned_courses) or "",
            })

            row_status = ImportRowStatus.ok if assigned_courses else ImportRowStatus.manual_review
            if not assigned_courses:
                manual_count += 1
            else:
                created_count += 1

            self.db.add(ImportRow(
                batch_id=batch.id, row_number=row["row_number"],
                raw_data=row["raw"],
                normalized_data={"full_name": full_name, "position": position_raw,
                                 "organization": org_name, "assigned": assigned_courses,
                                 "no_course": no_course_discs},
                status=row_status,
                error_message=f"Нет курса: {', '.join(no_course_discs)}" if no_course_discs else None,
                user_id=user.id,
            ))

        await self.db.flush()
        return {
            "summary": {
                "created": created_count, "duplicates": duplicate_count,
                "errors": error_count, "manual_review": manual_count,
                "total": len(preview["rows"]),
            },
            "credentials": credentials,
            "disciplines_used": [d.name for d in batch_disciplines],
        }
