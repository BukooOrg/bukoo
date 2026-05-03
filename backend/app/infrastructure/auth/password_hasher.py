from __future__ import annotations

from typing import override

from passlib.context import CryptContext

from app.application.interfaces.password_hasher import IPasswordHasher

_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class BcryptPasswordHasher(IPasswordHasher):
    @override
    def hash(self, plain: str) -> str:
        return _context.hash(plain)

    @override
    def verify(self, plain: str, hashed: str) -> bool:
        return _context.verify(plain, hashed)
