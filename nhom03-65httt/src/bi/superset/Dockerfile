# Apache Superset cho EduVision BI: ảnh chính thức cộng driver PostgreSQL, cấu hình và script khởi tạo.
# Ảnh chính thức không kèm psycopg2 nên không kết nối được PostgreSQL nếu không cài thêm.
FROM apache/superset:4.1.4

USER root
RUN pip install --no-cache-dir psycopg2-binary==2.9.10
COPY superset_config.py /app/pythonpath/superset_config.py
COPY docker-init.sh register_dw.py /app/
RUN sed -i 's/\r$//' /app/docker-init.sh && chmod +x /app/docker-init.sh
USER superset

EXPOSE 8088
ENTRYPOINT ["/app/docker-init.sh"]
