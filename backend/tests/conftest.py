"""
Shared fixtures for all tests.

Test DB: ozen_lms_test (separate from production, created automatically).
Each test gets a clean slate via table truncation (autouse fixture).
"""
import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import date
import base64 as _b64
import datetime as _dt

from cryptography import x509 as _x509
from cryptography.hazmat.primitives import hashes as _hashes, serialization as _ser
from cryptography.hazmat.primitives.asymmetric import rsa as _rsa
from cryptography.hazmat.primitives.serialization import pkcs7 as _pkcs7
from cryptography.x509.oid import NameOID as _NameOID

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text

# Import app first — this registers all models with Base.metadata via router imports
from app.main import app as fastapi_app  # noqa
import app.models.assignment   # noqa
import app.models.attempt      # noqa
import app.models.batch        # noqa
import app.models.certificate  # noqa
import app.models.course       # noqa
import app.models.discipline   # noqa
import app.models.import_row   # noqa
import app.models.material     # noqa
import app.models.organization # noqa
import app.models.position     # noqa
import app.models.protocol     # noqa
import app.models.rule         # noqa
import app.models.test         # noqa
import app.models.training_type # noqa
import app.models.user         # noqa

from app.core.database import Base, get_db
from app.core.security import hash_password, create_access_token
from app.models.user import AdminUser, User
from app.models.training_type import TrainingType
from app.models.batch import TrainingBatch, BatchStatus
from app.models.discipline import Discipline
from app.models.course import Course
from app.models.assignment import UserCourseAssignment, AssignmentStatus
from app.models.protocol import (
    Protocol, ProtocolCommissionMember, ProtocolParticipant,
    ProtocolStatus, CommissionRole, ParticipantResult,
)

TEST_DB_URL    = "postgresql+asyncpg://ozen_user:dev_pass_123@db:5432/ozen_lms_test"
ADMIN_CONN_URL = "postgresql+asyncpg://ozen_user:dev_pass_123@db:5432/postgres"


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def engine():
    """Create test DB + all tables once per test session."""
    # Ensure test database exists (drop & recreate for a clean schema)
    admin_eng = create_async_engine(ADMIN_CONN_URL, isolation_level="AUTOCOMMIT")
    async with admin_eng.connect() as conn:
        await conn.execute(text("DROP DATABASE IF EXISTS ozen_lms_test WITH (FORCE)"))
        await conn.execute(text("CREATE DATABASE ozen_lms_test"))
    await admin_eng.dispose()

    eng = create_async_engine(TEST_DB_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture(autouse=True, loop_scope="session")
async def clean_tables(engine):
    """Truncate all tables before every test — gives each test a clean slate."""
    table_names = ", ".join(t.name for t in Base.metadata.sorted_tables)
    # Use engine.begin() directly (auto-commits the DDL, avoids asyncpg open-tx conflicts)
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"))
    yield


@pytest_asyncio.fixture(loop_scope="session")
async def db(engine, clean_tables):
    """Raw DB session for seeding test data directly."""
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    async with SessionLocal() as session:
        yield session


@pytest_asyncio.fixture(loop_scope="session")
async def http(engine, clean_tables):
    """AsyncClient pointing at the FastAPI app, wired to the test DB."""
    SessionLocal = async_sessionmaker(engine, expire_on_commit=True)

    async def override_get_db():
        async with SessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    fastapi_app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
        yield ac
    fastapi_app.dependency_overrides.clear()


# ── CMS generation helper ────────────────────────────────────────────────────

def make_fresh_cms_b64(cn: str) -> str:
    """
    Generate a self-signed RSA-2048 CMS SignedData blob for testing.
    The certificate CN is set to *cn* and is valid for 10 years from now.
    Embedded (non-detached) so our cms_parser can extract the certificate.
    """
    key = _rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = _dt.datetime.now(_dt.timezone.utc)
    cert = (
        _x509.CertificateBuilder()
        .subject_name(_x509.Name([
            _x509.NameAttribute(_NameOID.COUNTRY_NAME, "KZ"),
            _x509.NameAttribute(_NameOID.COMMON_NAME, cn),
        ]))
        .issuer_name(_x509.Name([
            _x509.NameAttribute(_NameOID.COUNTRY_NAME, "KZ"),
            _x509.NameAttribute(_NameOID.COMMON_NAME, cn),
        ]))
        .public_key(key.public_key())
        .serial_number(_x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + _dt.timedelta(days=365 * 10))
        .sign(key, _hashes.SHA256())
    )
    cms_der = (
        _pkcs7.PKCS7SignatureBuilder()
        .set_data(b"PROTOCOL TEST PAYLOAD")
        .add_signer(cert, key, _hashes.SHA256())
        .sign(_ser.Encoding.DER, [])
    )
    return _b64.b64encode(cms_der).decode()


# ── Reusable data-setup helpers ───────────────────────────────────────────────

async def make_admin(db, full_name="Test Admin", is_superadmin=False,
                     is_commission_eligible=False):
    """Insert an AdminUser, return (admin, jwt_token)."""
    admin = AdminUser(
        id=uuid4(), login=f"admin_{uuid4().hex[:6]}",
        password_hash=hash_password("x"), full_name=full_name, is_active=True,
        is_superadmin=is_superadmin,
        is_commission_eligible=is_commission_eligible,
    )
    db.add(admin)
    await db.flush()
    token = create_access_token(str(admin.id), {"role": "admin"})
    return admin, token


async def make_training_type(db, code="biot_t"):
    tt = TrainingType(
        id=uuid4(), code=code, name_ru="БиОТ тест", name_short="БиОТ", validity_years=1,
    )
    db.add(tt)
    await db.flush()
    return tt


async def make_batch_with_users(db, statuses: list[AssignmentStatus]):
    """
    Create a batch + N users, each with one assignment whose status matches
    the corresponding entry in *statuses*.
    Returns (batch, users, assignments).
    """
    disc = Discipline(id=uuid4(), code=f"D_{uuid4().hex[:4]}", name="Test discipline")
    course = Course(id=uuid4(), discipline_id=disc.id, name="Test course")
    batch = TrainingBatch(id=uuid4(), name="Test batch", status=BatchStatus.completed)
    db.add_all([disc, course, batch])
    await db.flush()

    users, assignments = [], []
    for i, status in enumerate(statuses):
        u = User(
            id=uuid4(), login=f"u_{uuid4().hex[:6]}",
            password_hash=hash_password("x"),
            full_name=f"Сотрудник {i+1}",
            normalized_full_name=f"сотрудник {i+1}",
        )
        a = UserCourseAssignment(
            id=uuid4(), user_id=u.id, course_id=course.id,
            discipline_id=disc.id, batch_id=batch.id, status=status,
        )
        users.append(u)
        assignments.append(a)
    db.add_all(users)
    await db.flush()
    db.add_all(assignments)
    await db.flush()
    return batch, users, assignments


async def make_protocol(db, admin, tt, batch=None):
    protocol = Protocol(
        id=uuid4(), protocol_number=f"P-{uuid4().hex[:4]}",
        training_type_id=tt.id,
        batch_id=batch.id if batch else None,
        exam_date=date(2026, 5, 1),
        created_by_id=admin.id,
    )
    db.add(protocol)
    await db.flush()
    return protocol


async def make_commission_member(db, protocol, admin, role=CommissionRole.member):
    m = ProtocolCommissionMember(
        id=uuid4(), protocol_id=protocol.id,
        admin_user_id=admin.id, full_name=admin.full_name,
        role=role, sort_order=0,
    )
    db.add(m)
    await db.flush()
    return m
