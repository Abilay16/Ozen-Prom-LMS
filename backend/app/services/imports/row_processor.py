"""
Import row processor.
Orchestrates: parse → normalize → create users → assign courses → log rows.
"""
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.batch import TrainingBatch
from app.models.import_row import ImportRow, ImportRowStatus
from app.models.assignment import UserCourseAssignment
from app.models.discipline import Discipline
from app.models.user import User
from app.services.imports.parser import ImportParserService
from app.services.users.factory import UserFactoryService
from app.services.assignments.engine import AssignmentEngineService
from app.services.positions.normalizer import normalize_position


class ImportRowProcessor:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_batch(self, batch: TrainingBatch) -> dict:
        parser = ImportParserService()
        preview = parser.parse_preview(batch.excel_file_path)

        if "error" in preview:
            return {"error": preview["error"]}

        user_factory = UserFactoryService(self.db)
        assignment_engine = AssignmentEngineService(self.db)

        created_users = []
        manual_review = []
        duplicates = []
        errors = []
        credentials = []  # plain passwords — only available here

        # Load disciplines once
        disc_result = await self.db.execute(select(Discipline))
        disciplines = {d.name.lower(): d for d in disc_result.scalars().all()}

        for row in preview["rows"]:
            if row["status"] == "error":
                log = ImportRow(
                    batch_id=batch.id,
                    row_number=row["row_number"],
                    raw_data=row["raw"],
                    status=ImportRowStatus.error,
                    error_message="; ".join(row["warnings"]),
                )
                self.db.add(log)
                errors.append(row)
                continue

            full_name = row["full_name"]
            norm_name = UserFactoryService.normalize_full_name(full_name)

            # Check duplicate
            existing = await self.db.execute(
                select(User).where(
                    User.normalized_full_name == norm_name,
                    User.organization_id == batch.organization_id,
                )
            )
            existing_user = existing.scalar_one_or_none()

            if existing_user:
                log = ImportRow(
                    batch_id=batch.id,
                    row_number=row["row_number"],
                    raw_data=row["raw"],
                    status=ImportRowStatus.duplicate,
                    error_message="User already exists",
                    user_id=existing_user.id,
                )
                self.db.add(log)
                duplicates.append({"row": row, "user_id": str(existing_user.id)})
                continue

            # Create user
            user, plain_password = await user_factory.create_user(
                full_name=full_name,
                organization_id=batch.organization_id,
                position_raw=row["position"],
                batch_id=batch.id,
            )
            credentials.append({
                "full_name": full_name,
                "login": user.login,
                "password": plain_password,
                "organization": row["organization"],
                "position": row["position"],
            })

            # Parse disciplines from cell
            disc_names = [d.strip() for d in row["disciplines_raw"].split(",") if d.strip()]
            normalized_position = normalize_position(row["position"])
            assigned_courses = []

            for disc_name in disc_names:
                disc = disciplines.get(disc_name.lower())
                if not disc:
                    manual_review.append({
                        "reason": f"Discipline not found: {disc_name}",
                        "row": row,
                    })
                    continue

                course_id = await assignment_engine.find_course(disc.id, normalized_position)
                if course_id:
                    assignment = UserCourseAssignment(
                        user_id=user.id,
                        course_id=course_id,
                        discipline_id=disc.id,
                        batch_id=batch.id,
                    )
                    self.db.add(assignment)
                    assigned_courses.append(str(course_id))
                else:
                    manual_review.append({
                        "reason": f"No rule for discipline '{disc_name}' + position '{row['position']}'",
                        "row": row,
                    })

            log = ImportRow(
                batch_id=batch.id,
                row_number=row["row_number"],
                raw_data=row["raw"],
                normalized_data={
                    "full_name": full_name,
                    "position": row["position"],
                    "disciplines": disc_names,
                    "assigned_courses": assigned_courses,
                },
                status=ImportRowStatus.ok if assigned_courses else ImportRowStatus.manual_review,
                user_id=user.id,
            )
            self.db.add(log)

            if assigned_courses:
                created_users.append({"login": user.login, "user_id": str(user.id)})

        await self.db.flush()

        # Store credentials in batch for export
        batch._credentials = credentials  # transient, used by export

        return {
            "created": len(created_users),
            "duplicates": len(duplicates),
            "manual_review": len(manual_review),
            "errors": len(errors),
            "credentials": credentials,  # returned once — caller should export immediately
        }
