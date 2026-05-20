from __future__ import annotations

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from app.infrastructure.db.models.base import Base
from app.core.config import get_configs


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from app.infrastructure.db.models import (
    UserModel, # noqa: F401
    AccountModel, # noqa: F401
    AddressModel, # noqa: F401
    CollectionModel, # noqa: F401
    CategoryModel, # noqa: F401
    PublisherModel, # noqa: F401
    AuthorModel, # noqa: F401
    BookModel, # noqa: F401
    BookAuthorModel, # noqa: F401
    WishlistModel, # noqa: F401
    WishlistItemModel, # noqa: F401
    CartModel, # noqa: F401
    CartItemModel, # noqa: F401
    OrderModel, # noqa: F401
    OrderItemModel, # noqa: F401
    PaymentModel, # noqa: F401
    ReviewModel, # noqa: F401
    NotificationModel, # noqa: F401
    ReportJobModel, # noqa: F401
    VerificationTokenModel, # noqa: F401
)
target_metadata = Base.metadata


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.
app_configs = get_configs()
db_url = f"{app_configs.POSTGRES_ASYNC_PREFIX}{app_configs.POSTGRES_URI}"
config.set_main_option("sqlalchemy.url", db_url)

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
