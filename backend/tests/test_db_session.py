import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db


@pytest.mark.asyncio
async def test_get_db_yields_async_session():
    agen = get_db()
    db = await anext(agen)
    assert isinstance(db, AsyncSession)
    await agen.aclose()
