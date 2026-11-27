"""Re-export các dependency dùng chung cho router nghiệp vụ."""

from app.auth.dependencies import get_current_user, require_role, require_vendor_owner
from app.database import get_db

__all__ = ["get_db", "get_current_user", "require_role", "require_vendor_owner"]
