from fastapi import APIRouter
from app.api.v1.endpoints import auth, jobs, transactions

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])

# ВАЖНО: без prefix здесь
router.include_router(transactions.router)
