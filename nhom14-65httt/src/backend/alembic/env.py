"""Alembic env – kết nối SQLAlchemy Base.metadata để autogenerate migration."""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.config import settings
from app.database import Base
from app.menu.models import CanonicalDish, Ingredient, MenuItem, MenuItemIngredient  # noqa: F401
from app.orders.models import Order, OrderItem, OrderStatusHistory  # noqa: F401
from app.preferences.models import Preference  # noqa: F401 - đăng ký bảng preferences
from app.restaurants.models import Restaurant, RestaurantMembership  # noqa: F401
from app.reviews.models import Review  # noqa: F401 - đăng ký bảng reviews
from app.tracking.models import InteractionEvent, RecommendationImpression, RecommendationRequest  # noqa: F401
from app.users.models import User  # noqa: F401 - đăng ký bảng users vào Base.metadata
from migration_support import compare_server_default

# Alembic Config object
config = context.config

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# SQLAlchemy MetaData cho autogenerate
target_metadata = Base.metadata


def get_url() -> str:
    return settings.database_url


def run_migrations_offline() -> None:
    """Chạy migration ở chế độ offline (chỉ sinh SQL)."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=compare_server_default,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Chạy migration ở chế độ online (kết nối DB thật)."""
    configuration = config.get_section(config.config_ini_section, {})
    # Đây là dict truyền trực tiếp cho SQLAlchemy, không qua ConfigParser interpolation.
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        if connection.dialect.name == "sqlite":
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
            connection.commit()
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=compare_server_default,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
