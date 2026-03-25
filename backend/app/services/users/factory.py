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

        for _ in range(20):
            digits = "".join(random.choices(string.digits, k=random.randint(2, 3)))
            candidate = f"{base}{digits}"
            result = await self.db.execute(select(User).where(User.login == candidate))
            if not result.scalar_one_or_none():
                return candidate

        # Fallback: longer suffix
        suffix = "".join(random.choices(string.digits, k=6))
        return f"{base}{suffix}"

    @staticmethod
    def generate_password() -> str:
        length = random.randint(6, 7)
        return "".join(random.choices(string.digits, k=length))

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
