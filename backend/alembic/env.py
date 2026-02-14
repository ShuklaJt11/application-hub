import asyncio
from logging.config import fileConfig

from alembic import context  # type: ignore[attr-defined]
from app.core.config import settings
from app.db.base import Base
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

config = context.config
fileConfig(config.config_file_name)

target_metadata = Base.metadata


async def run_migrations_online():
    connectable = create_async_engine(settings.DATABASE_URL, poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


asyncio.run(run_migrations_online())
