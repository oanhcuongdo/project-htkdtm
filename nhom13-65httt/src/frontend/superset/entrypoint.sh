#!/bin/bash
set -e

echo "[*] Upgrading Superset metadata database..."
superset db upgrade

echo "[*] Creating default admin user (if not exists)..."
superset fab create-admin \
    --username "${SUPERSET_ADMIN_USERNAME:-admin}" \
    --firstname Admin \
    --lastname User \
    --email admin@finance.local \
    --password "${SUPERSET_ADMIN_PASSWORD:-admin}" || true

echo "[*] Initializing Superset roles and permissions..."
superset init

echo "[*] Ensuring Public role can access language_pack..."
python -c "
from superset.app import create_app
app = create_app()
with app.app_context():
    from superset import security_manager
    public_role = security_manager.find_role('Public')
    perm = security_manager.find_permission_view_menu('can_language_pack', 'Superset')
    if perm and public_role:
        security_manager.add_permission_role(public_role, perm)
" || true

echo "[*] Starting Superset server..."
exec /app/docker/entrypoints/run-server.sh
