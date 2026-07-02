"""
Tuki Backend — Base Repository

Generic async CRUD repository with pagination support.
All domain repositories inherit from this.
"""

from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic repository providing common CRUD operations.

    Subclasses should set `model` to their SQLAlchemy model class.
    """

    model: type[ModelType]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, id: UUID) -> ModelType | None:
        """Get a single record by UUID."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ModelType], int]:
        """
        Get paginated records.

        Returns:
            Tuple of (items, total_count)
        """
        # Count total
        count_query = select(func.count()).select_from(self.model)
        total = (await self.session.execute(count_query)).scalar_one()

        # Fetch page
        offset = (page - 1) * page_size
        query = select(self.model).offset(offset).limit(page_size)
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def create(self, **kwargs: Any) -> ModelType:
        """Create a new record."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, id: UUID, **kwargs: Any) -> ModelType | None:
        """Update a record by UUID."""
        instance = await self.get_by_id(id)
        if not instance:
            return None
        for key, value in kwargs.items():
            setattr(instance, key, value)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, id: UUID) -> bool:
        """Delete a record by UUID. Returns True if deleted."""
        instance = await self.get_by_id(id)
        if not instance:
            return False
        await self.session.delete(instance)
        await self.session.flush()
        return True

    def _base_query(self) -> Select:
        """Return the base select query. Override in subclasses for joins."""
        return select(self.model)
