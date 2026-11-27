"""ORM models package. Import all models here so Alembic autogenerate detects them."""

from app.models.audit_log import AuditLog
from app.models.erp import (
    Category,
    CostComponent,
    Inventory,
    Product,
    Supplier,
    SupplierProduct,
)
from app.models.market import (
    ChannelProduct,
    CompetitorPrice,
    CompetitorPriceHistory,
    SalesChannel,
    SalesRecord,
)
from app.models.pricing import (
    ModelRun,
    PriceApproval,
    PriceRecommendation,
    PriceSyncLog,
    PricingRule,
)
from app.models.user import User

__all__ = [
    "AuditLog",
    "Category",
    "ChannelProduct",
    "CompetitorPrice",
    "CompetitorPriceHistory",
    "CostComponent",
    "Inventory",
    "ModelRun",
    "PriceApproval",
    "PriceRecommendation",
    "PriceSyncLog",
    "PricingRule",
    "Product",
    "SalesChannel",
    "SalesRecord",
    "Supplier",
    "SupplierProduct",
    "User",
]
