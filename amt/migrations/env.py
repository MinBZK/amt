import os
from logging.config import fileConfig

from alembic import context
from amt.models import *  # noqa
from sqlalchemy import engine_from_config, pool
from sqlalchemy.schema import MetaData

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = MetaData()


def get_url() -> str:
    scheme = os.getenv("APP_DATABASE_SCHEME", "sqlite")

    if scheme == "sqlite":
        file = os.getenv("APP_DATABASE_FILE", "database.sqlite3")
        return f"{scheme}:///{file}"

    user = os.getenv("APP_DATABASE_USER", "amt")
    password = os.getenv("APP_DATABASE_PASSWORD", "")
    server = os.getenv("APP_DATABASE_SERVER", "db")
    port = os.getenv("APP_DATABASE_PORT", "5432")
    db = os.getenv("APP_DATABASE_DB", "amt")
    return f"{scheme}://{user}:{password}@{server}:{port}/{db}"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True, compare_type=True, render_as_batch=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = config.get_section(config.config_ini_section)
    if configuration is None:
        raise Exception("Failed to get configuration section")  # noqa: TRY002
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata, compare_type=True, render_as_batch=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
