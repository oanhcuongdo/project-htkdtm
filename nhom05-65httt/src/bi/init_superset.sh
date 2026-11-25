#!/bin/bash
set -e

echo "[*] Khoi tao metadata database cho Apache Superset..."
superset db upgrade

echo "[*] Tao tai khoan Admin Superset..."
superset fab create-admin \
    --username "${SUPERSET_ADMIN_USER:-admin}" \
    --firstname "Nguyen Quang" \
    --lastname "Duc" \
    --email "${SUPERSET_ADMIN_EMAIL:-2351160512@e.tlu.edu.vn}" \
    --password "${SUPERSET_ADMIN_PASSWORD:-admin}" || true

echo "[*] Khoi tao roles & permissions..."
superset init

if [ -f "/app/bi_assets/training_analytics_dashboards.zip" ]; then
    echo "[*] Import 3 Dashboards BI tu training_analytics_dashboards.zip..."
    superset import-dashboards -p /app/bi_assets/training_analytics_dashboards.zip -u "${SUPERSET_ADMIN_USER:-admin}" || true
fi

echo "[*] Khoi dong Apache Superset server tai cong 8088..."
/usr/bin/run-server.sh
