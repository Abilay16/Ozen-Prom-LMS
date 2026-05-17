from fastapi import APIRouter

from app.api.v1 import auth, users, organizations, batches, courses, materials, tests, rules, progress, exports, disciplines, positions, training_types, protocols, certificates, admin_users, user_documents, medical_exams

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, prefix="/admin/users", tags=["Admin — Users"])
api_router.include_router(users.public_router, prefix="/users", tags=["Public"])
api_router.include_router(organizations.router, prefix="/admin/organizations", tags=["Admin — Organizations"])
api_router.include_router(batches.router, prefix="/admin/batches", tags=["Admin — Batches"])
api_router.include_router(courses.router, prefix="/admin/courses", tags=["Admin — Courses"])
api_router.include_router(materials.router, prefix="/admin/materials", tags=["Admin — Materials"])
api_router.include_router(tests.router, prefix="/admin/tests", tags=["Admin — Tests"])
api_router.include_router(rules.router, prefix="/admin/rules", tags=["Admin — Rules"])
api_router.include_router(disciplines.router, prefix="/admin/disciplines", tags=["Admin — Disciplines"])
api_router.include_router(positions.router, prefix="/admin/positions", tags=["Admin — Positions"])
api_router.include_router(progress.router, prefix="/admin/progress", tags=["Admin — Progress"])
api_router.include_router(exports.router, prefix="/admin/exports", tags=["Admin — Exports"])
api_router.include_router(training_types.router, prefix="/admin/training-types", tags=["Admin — Training Types"])
api_router.include_router(protocols.router, prefix="/admin/protocols", tags=["Admin — Protocols"])
api_router.include_router(certificates.router, prefix="/admin/certificates", tags=["Admin — Certificates"])
api_router.include_router(admin_users.router, prefix="/admin/admin-users", tags=["Admin — Commission Users"])
api_router.include_router(certificates.public_router, prefix="", tags=["Public"])

# Learner routes
from app.api.v1 import learner
api_router.include_router(learner.router, prefix="/learner", tags=["Learner"])
api_router.include_router(certificates.learner_router, prefix="/learner/certificates", tags=["Learner — Certificates"])
api_router.include_router(user_documents.router, prefix="/learner/documents", tags=["Learner — Documents"])
api_router.include_router(medical_exams.router, prefix="/admin/medical-exams", tags=["Admin — Medical Exams"])
api_router.include_router(medical_exams.learner_router, prefix="/learner/medical-exams", tags=["Learner — Medical Exams"])
