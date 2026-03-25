from fastapi import APIRouter

from app.api.v1 import auth, users, organizations, batches, courses, materials, tests, rules, progress, exports, disciplines, positions

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, prefix="/admin/users", tags=["Admin — Users"])
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

# Learner routes
from app.api.v1 import learner
api_router.include_router(learner.router, prefix="/learner", tags=["Learner"])
