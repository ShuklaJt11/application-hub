import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context  # type: ignore[attr-defined]
from app.core.config import settings  # type: ignore[import-not-found]
from app.db.base import Base  # type: ignore[import-not-found]

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata  # type: ignore[attr-defined]


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
