"""
Tuki Backend — Database Dependencies

FastAPI dependency for injecting async database sessions.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session

# Type alias for clean dependency injection
DBSession = Annotated[AsyncSession, Depends(get_async_session)]
