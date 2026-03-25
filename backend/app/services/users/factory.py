import random
import string
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.utils.transliteration import transliterate_name_to_login
from app.core.security import hash_password


class UserFactoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_unique_login(self, full_name: str) -> str:
        base = transliterate_name_to_login(full_name)
        if not base:
            base = "user"

        # Try clean base first
        result = await self.db.execute(select(User).where(User.login == base))
        if not result.scalar_one_or_none():
            return base

        # Add numeric suffix until unique
        for i in range(2, 100):
            candidate = f"{base}{i}"
            result = await self.db.execute(select(User).where(User.login == candidate))
            if not result.scalar_one_or_none():
                return candidate

        import random as _r
        suffix = "".join(_r.choices(string.digits, k=4))
        return f"{base}{suffix}"

    @staticmethod
    def generate_password() -> str:
        # 3 letters + 3 digits — easy to remember
        letters = random.choices(string.ascii_lowercase, k=3)
        digits = random.choices(string.digits, k=3)
        combined = letters + digits
        random.shuffle(combined)
        return "".join(combined)

    @staticmethod
    def normalize_full_name(full_name: str) -> str:
        return " ".join(full_name.strip().split()).lower()

    async def create_user(
        self,
        full_name: str,
        organization_id=None,
        position_raw: str = None,
        batch_id=None,
    ) -> tuple[User, str]:
        """
        Creates user, returns (user, plain_password).
        Plain password is NOT stored — caller must export it before session closes.
        """
        login = await self.generate_unique_login(full_name)
        plain_password = self.generate_password()

        user = User(
            login=login,
            password_hash=hash_password(plain_password),
            full_name=full_name.strip(),
            normalized_full_name=self.normalize_full_name(full_name),
            organization_id=organization_id,
            position_raw=position_raw,
            batch_id=batch_id,
        )
        self.db.add(user)
        await self.db.flush()
        return user, plain_password
