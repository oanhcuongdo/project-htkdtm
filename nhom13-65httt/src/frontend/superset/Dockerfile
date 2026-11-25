FROM apache/superset:latest

USER root

# Cài đặt psycopg2-binary trực tiếp vào virtualenv (/app/.venv) của Superset bằng uv
RUN uv pip install --python /app/.venv/bin/python psycopg2-binary

# Tạo gói ngôn ngữ tiếng Việt để tránh lỗi crash React SPA khi trình duyệt dùng tiếng Việt
RUN mkdir -p /app/superset/translations/vi/LC_MESSAGES && \
    cp /app/superset/translations/empty_language_pack.json /app/superset/translations/vi/LC_MESSAGES/messages.json && \
    chmod -R 777 /app/superset/translations/vi

# Sao chép script khởi tạo tự động (db upgrade, create-admin, init, provision dashboards, start server)
COPY entrypoint.sh /app/entrypoint-custom.sh
RUN sed -i 's/\r$//' /app/entrypoint-custom.sh && chmod +x /app/entrypoint-custom.sh

USER superset

CMD ["/app/entrypoint-custom.sh"]
