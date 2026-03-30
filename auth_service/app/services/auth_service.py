from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from app.repositories.user_repository import UserRepository
from app.models.user import User, UserRegister
from typing import Optional

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "gizli_anahtar_123" # Daha sonra .env'e taşınacak [cite: 40]
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60

class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.repo = user_repository

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    def create_token(self, username: str, role: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
        payload = {"sub": username, "role": role, "exp": expire}
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def decode_token(self, token: str) -> Optional[dict]:
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError:
            return None

    async def register(self, data: UserRegister) -> bool:
        if await self.repo.username_exists(data.username):
            return False
        hashed = self.hash_password(data.password)
        user = User(username=data.username, hashed_password=hashed, role=data.role)
        return await self.repo.create_user(user)

    async def login(self, username: str, password: str) -> Optional[str]:
        user = await self.repo.find_by_username(username)
        if not user or not self.verify_password(password, user["hashed_password"]):
            return None
        return self.create_token(username, user["role"])