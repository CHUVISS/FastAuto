from logging.config import fileConfig

from sqlalchemy import create_engine, pool
from sqlmodel import SQLModel

# импорт всех моделей тут нужен, чтобы metadata о них знала
import app.models.ai  # noqa: F401
import app.models.catalog  # noqa: F401
import app.models.favorites  # noqa: F401
import app.models.geo  # noqa: F401
import app.models.notifications  # noqa: F401
import app.models.listings  # noqa: F401
import app.models.payout  # noqa: F401
import app.models.reservations  # noqa: F401
import app.models.tickets  # noqa: F401
import app.models.users  # noqa: F401
from alembic import context
from app.core.config import settings

_EXCLUDED_SCHEMAS = {"catalog", "geo"}


def include_object(obj, name, type_, reflected, compare_to) -> bool:  # noqa: ARG001
    if getattr(obj, "schema", None) in _EXCLUDED_SCHEMAS:
        return False
    if type_ == "foreign_key_constraint":
        referred = getattr(obj, "referred_table", None)
        if referred is not None and referred.schema in _EXCLUDED_SCHEMAS:
            return False
    return True

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    # disable_existing_loggers=False: alembic's logging config must not nuke
    # the application's (and test harness's) already-configured loggers when
    # migrations run programmatically (prestart, tests).
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url() -> str:
    return str(settings.sqlalchemy_sync_database_uri)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()



def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = create_engine(
        get_url(),
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()



if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
