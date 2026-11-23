FROM apache/superset:latest

USER root

# Cài đặt psycopg2-binary để Superset kết nối với PostgreSQL Data Warehouse
RUN pip install --no-cache-dir psycopg2-binary

# Tạo gói ngôn ngữ tiếng Việt để tránh lỗi crash React SPA khi trình duyệt dùng tiếng Việt
RUN mkdir -p /app/superset/translations/vi/LC_MESSAGES && \
    cp /app/superset/translations/empty_language_pack.json /app/superset/translations/vi/LC_MESSAGES/messages.json && \
    chmod -R 777 /app/superset/translations/vi

# Sao chép script khởi tạo tự động (db upgrade, create-admin, init, start server)
COPY entrypoint.sh /app/entrypoint-custom.sh
RUN sed -i 's/\r$//' /app/entrypoint-custom.sh && chmod +x /app/entrypoint-custom.sh

USER superset

CMD ["/app/entrypoint-custom.sh"]
