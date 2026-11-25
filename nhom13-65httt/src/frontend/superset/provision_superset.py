# pyright: reportMissingImports=false
"""
Script tự động cấu hình Apache Superset (Idempotent Provisioning):
1. Tạo kết nối Database tới PostgreSQL Data Warehouse (`personal_finance_dw`).
2. Đồng bộ 8 Semantic Views làm Datasets chuẩn cho BI.
3. Tạo 18 Charts (Big Number, Gauge, Sankey, Heatmap, Donut, Time-Series Forecast, Tables).
4. Xây dựng 3 Dashboards hoàn chỉnh theo Đề cương Project (Nhóm 13 - 65HTTT):
   - 01. Tổng quan Dòng tiền (Cashflow Overview)
   - 02. Phân tích Hành vi Chi tiêu (Spending Behavior)
   - 03. Dự báo & Cảnh báo AI (AI Forecast & Anomalies)
5. Xuất bản sao cấu hình JSON ra `dashboards_export/` và `datasources/`.
"""

import importlib
import json
import os
import sys
import uuid
from typing import Any, Optional

EXPORT_DIR = "/app/superset_assets/dashboards_export"
DATASOURCE_DIR = "/app/superset_assets/datasources"


def make_adhoc_metric(column_name: str, aggregate: str = "SUM", label: Optional[str] = None) -> dict:
    return {
        "expressionType": "SIMPLE",
        "column": {"column_name": column_name},
        "aggregate": aggregate,
        "label": label or f"{aggregate}({column_name})",
        "optionName": f"metric_{column_name}_{aggregate.lower()}",
    }


def make_filter(col: str, op: str, val) -> dict:
    return {
        "expressionType": "SIMPLE",
        "subject": col,
        "operator": op,
        "comparator": val,
        "clause": "WHERE",
        "isExtra": False,
        "isNew": False,
    }


def build_grid_position(dashboard_title: str, rows_layout: list) -> dict:
    """
    Xây dựng position_json chuẩn 12 cột cho Superset Dashboard.
    rows_layout: list of rows, each row is list of tuples: (slice_obj, width_cols, height_units)
    """
    pos = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
        "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [], "parents": ["ROOT_ID"]},
        "HEADER_ID": {
            "id": "HEADER_ID",
            "type": "HEADER",
            "meta": {"text": dashboard_title},
        },
    }

    for r_idx, row_items in enumerate(rows_layout):
        row_id = f"ROW-row-{r_idx}"
        pos["GRID_ID"]["children"].append(row_id)
        pos[row_id] = {
            "type": "ROW",
            "id": row_id,
            "children": [],
            "parents": ["ROOT_ID", "GRID_ID"],
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
        }
        for c_idx, (slc, width, height) in enumerate(row_items):
            chart_key = f"CHART-c-{r_idx}-{c_idx}-{slc.id}"
            pos[row_id]["children"].append(chart_key)
            pos[chart_key] = {
                "type": "CHART",
                "id": chart_key,
                "children": [],
                "parents": ["ROOT_ID", "GRID_ID", row_id],
                "meta": {
                    "width": width,
                    "height": height,
                    "chartId": slc.id,
                    "sliceName": slc.slice_name,
                    "uuid": str(slc.uuid) if slc.uuid else str(uuid.uuid4()),
                },
            }
    return pos


def provision():
    create_app = importlib.import_module("superset.app").create_app
    app = create_app()
    with app.app_context():
        SqlaTable = importlib.import_module("superset.connectors.sqla.models").SqlaTable
        superset_ext = importlib.import_module("superset.extensions")
        db = superset_ext.db
        security_manager = superset_ext.security_manager
        Database = importlib.import_module("superset.models.core").Database
        Dashboard = importlib.import_module("superset.models.dashboard").Dashboard
        Slice = importlib.import_module("superset.models.slice").Slice

        admin_user = security_manager.find_user(username=os.getenv("SUPERSET_ADMIN_USERNAME", "admin"))
        owners = [admin_user] if admin_user else []

        # ------------------------------------------------------------------
        # 1. Kết nối Cơ sở dữ liệu PostgreSQL Data Warehouse
        # ------------------------------------------------------------------
        pg_user = os.getenv("POSTGRES_USER", "finance_user")
        pg_pass = os.getenv("POSTGRES_PASSWORD", "SecurePassword123!")
        pg_host = os.getenv("POSTGRES_HOST", "postgres_db")
        pg_port = os.getenv("POSTGRES_PORT", "5432")
        pg_db = os.getenv("POSTGRES_DB", "personal_finance_dw")
        uri = f"postgresql+psycopg2://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"

        db_name = "Personal Finance DW (PostgreSQL)"
        database = db.session.query(Database).filter_by(database_name=db_name).first()
        if not database:
            database = Database(
                database_name=db_name,
                sqlalchemy_uri=uri,
                expose_in_sqllab=True,
                allow_ctas=True,
                allow_cvas=True,
                allow_dml=False,
                allow_file_upload=True,
            )
            db.session.add(database)
            db.session.commit()
            print(f"[+] Đã tạo kết nối Database: {db_name} (id={database.id})")
        else:
            database.sqlalchemy_uri = uri
            database.expose_in_sqllab = True
            db.session.commit()
            print(f"[=] Đã tồn tại kết nối Database: {db_name} (id={database.id})")

        # ------------------------------------------------------------------
        # 2. Khai báo & Đồng bộ Metadata cho 8 Semantic Views
        # ------------------------------------------------------------------
        view_configs = [
            ("vw_clean_transactions", "full_date"),
            ("vw_monthly_savings_rate", "report_month"),
            ("vw_category_budget_monitoring", "report_month"),
            ("vw_spending_heatmap", None),
            ("vw_anomaly_feed", "full_date"),
            ("vw_cashflow_sankey", None),
            ("vw_ai_forecast_combined", "record_date"),
            ("vw_burn_rate_gauge", "report_month"),
        ]

        datasets = {}
        for tbl_name, main_dttm in view_configs:
            tbl = (
                db.session.query(SqlaTable)
                .filter_by(table_name=tbl_name, database_id=database.id)
                .first()
            )
            if not tbl:
                tbl = SqlaTable(
                    table_name=tbl_name,
                    database_id=database.id,
                    schema="public",
                    owners=owners,
                )
                db.session.add(tbl)
                db.session.commit()
            tbl.fetch_metadata()
            if main_dttm:
                tbl.main_dttm_col = main_dttm
            db.session.commit()
            datasets[tbl_name] = tbl
            print(f"[✓] Đồng bộ Dataset: {tbl_name} (id={tbl.id}, cols={len(tbl.columns)})")

        # ------------------------------------------------------------------
        # Helper tạo query_context chuẩn cho Superset 6.x để chart chạy ngay trên API & Dashboard
        # ------------------------------------------------------------------
        def build_query_context(ds_id: int, viz_type: str, params: dict) -> dict:
            filters = []
            for f in params.get("adhoc_filters", []):
                filters.append({
                    "col": f["subject"],
                    "op": f["operator"],
                    "val": f["comparator"],
                })

            query: dict = {
                "filters": filters,
                "extras": {"having": "", "where": ""},
                "applied_time_extras": {},
                "row_limit": int(params.get("row_limit", 1000)),
                "time_range": "No filter",
            }

            if viz_type in ("big_number_total", "gauge_chart"):
                query["columns"] = []
                query["metrics"] = [params["metric"]]
            elif viz_type in ("echarts_timeseries_bar", "echarts_timeseries_line"):
                x_col = params["x_axis"]
                query["columns"] = [x_col]
                query["metrics"] = params["metrics"]
                query["is_timeseries"] = False
                query["orderby"] = [[x_col, True]]
            elif viz_type == "sankey_v2":
                query["columns"] = [params["source"], params["target"]]
                query["metrics"] = [params["metric"]]
            elif viz_type == "heatmap_v2":
                query["columns"] = [params["x_axis"], params["groupby"]]
                query["metrics"] = [params["metric"]]
            elif viz_type == "pie":
                query["columns"] = params["groupby"]
                query["metrics"] = [params["metric"]]
                query["orderby"] = [[params["metric"], False]]
            elif viz_type == "table":
                if params.get("query_mode") == "raw":
                    query["columns"] = params["all_columns"]
                    query["metrics"] = []
                    orderby = []
                    for ob in params.get("order_by_cols", []):
                        col_name, is_asc = json.loads(ob)
                        orderby.append([col_name, is_asc])
                    if orderby:
                        query["orderby"] = orderby
                else:
                    query["columns"] = params.get("groupby", [])
                    query["metrics"] = params.get("metrics", [])
                    if query["metrics"]:
                        query["orderby"] = [[query["metrics"][0], False]]

            return {
                "datasource": {"id": ds_id, "type": "table"},
                "force": False,
                "queries": [query],
                "form_data": params,
                "result_format": "json",
                "result_type": "full",
            }

        # ------------------------------------------------------------------
        # Helper tạo hoặc cập nhật Chart (Slice)
        # ------------------------------------------------------------------
        def upsert_chart(name: str, dataset_name: str, viz_type: str, params: dict) -> Any:
            ds = datasets[dataset_name]
            full_params = dict(params)
            full_params["datasource"] = f"{ds.id}__table"
            full_params["viz_type"] = viz_type
            qctx = build_query_context(ds.id, viz_type, full_params)

            slc = db.session.query(Slice).filter_by(slice_name=name).first()
            if not slc:
                slc = Slice(
                    slice_name=name,
                    datasource_id=ds.id,
                    datasource_type="table",
                    viz_type=viz_type,
                    params=json.dumps(full_params, ensure_ascii=False),
                    query_context=json.dumps(qctx, ensure_ascii=False),
                    owners=owners,
                )
                db.session.add(slc)
            else:
                slc.datasource_id = ds.id
                slc.datasource_type = "table"
                slc.viz_type = viz_type
                slc.params = json.dumps(full_params, ensure_ascii=False)
                slc.query_context = json.dumps(qctx, ensure_ascii=False)
            db.session.commit()
            return slc

        # ------------------------------------------------------------------
        # 3. Tạo 18 Charts cho 3 Dashboards chuyên biệt
        # ------------------------------------------------------------------
        # === DASHBOARD 1: TỔNG QUAN DÒNG TIỀN (CASHFLOW OVERVIEW) ===
        c1_income = upsert_chart(
            "KPI: Tổng Thu Nhập Tháng Hiện Tại (VND)",
            "vw_burn_rate_gauge",
            "big_number_total",
            {
                "metric": make_adhoc_metric("mtd_income", "MAX", "Thu nhập tháng (VND)"),
                "subheader": "Tháng hiện tại (đã loại chuyển nội bộ)",
                "y_axis_format": ",.0f",
                "header_font_size": 0.4,
                "subheader_font_size": 0.15,
            },
        )
        c1_expense = upsert_chart(
            "KPI: Tổng Chi Tiêu Tháng Hiện Tại (VND)",
            "vw_burn_rate_gauge",
            "big_number_total",
            {
                "metric": make_adhoc_metric("mtd_expense", "MAX", "Chi tiêu tháng (VND)"),
                "subheader": "Thực chi lũy kế trong tháng",
                "y_axis_format": ",.0f",
                "header_font_size": 0.4,
                "subheader_font_size": 0.15,
            },
        )
        c1_savings_rate = upsert_chart(
            "KPI: Tỷ Lệ Tiết Kiệm Ròng Tháng (%)",
            "vw_burn_rate_gauge",
            "big_number_total",
            {
                "metric": make_adhoc_metric("mtd_savings_rate_pct", "MAX", "Tiết kiệm ròng (%)"),
                "subheader": "Câu hỏi 1: (Thu - Chi) / Thu × 100%",
                "y_axis_format": ".2f",
                "header_font_size": 0.4,
                "subheader_font_size": 0.15,
            },
        )
        c1_eom_balance = upsert_chart(
            "KPI: Số Dư Cuối Tháng Dự Kiến (VND)",
            "vw_burn_rate_gauge",
            "big_number_total",
            {
                "metric": make_adhoc_metric("projected_eom_balance", "MAX", "Dự kiến cuối tháng"),
                "subheader": "Câu hỏi 4: Dự phóng theo tốc độ chi",
                "y_axis_format": ",.0f",
                "header_font_size": 0.4,
                "subheader_font_size": 0.15,
            },
        )
        c1_gauge = upsert_chart(
            "Tốc Độ Đốt Ngân Sách Tháng Hiện Tại (%)",
            "vw_burn_rate_gauge",
            "gauge_chart",
            {
                "metric": make_adhoc_metric("budget_utilization_pct", "MAX", "Tỷ lệ dùng ngân sách (%)"),
                "min_val": 0,
                "max_val": 150,
                "start_angle": 225,
                "end_angle": -45,
                "show_pointer": True,
                "show_progress": True,
                "value_formatter": "{value}%",
                "intervals": "0,80,100,150",
                "interval_color_indices": "1,2,3",
            },
        )
        c1_monthly_bar = upsert_chart(
            "Thu Nhập vs Chi Tiêu & Tiết Kiệm Ròng Theo Tháng",
            "vw_monthly_savings_rate",
            "echarts_timeseries_bar",
            {
                "x_axis": "report_month",
                "time_grain_sqla": "P1M",
                "metrics": [
                    make_adhoc_metric("total_income", "SUM", "Thu nhập thực"),
                    make_adhoc_metric("total_expense", "SUM", "Chi tiêu thực"),
                    make_adhoc_metric("net_savings", "SUM", "Tiết kiệm ròng"),
                ],
                "color_scheme": "supersetColors",
                "show_legend": True,
                "y_axis_format": ",.0f",
                "rich_tooltip": True,
            },
        )
        c1_sankey = upsert_chart(
            "Sankey: Luồng Di Chuyển Dòng Tiền (Thu Nhập → Quỹ Chi → Danh Mục)",
            "vw_cashflow_sankey",
            "sankey_v2",
            {
                "source": "source",
                "target": "target",
                "metric": make_adhoc_metric("value", "SUM", "Giá trị dòng tiền (VND)"),
                "color_scheme": "supersetColors",
                "row_limit": 100,
            },
        )
        c1_budget_table = upsert_chart(
            "Giám Sát Ngân Sách Vượt Trần Theo Danh Mục (Câu hỏi 2)",
            "vw_category_budget_monitoring",
            "table",
            {
                "query_mode": "raw",
                "all_columns": [
                    "report_month",
                    "parent_category",
                    "category_name",
                    "monthly_budget",
                    "actual_spent",
                    "over_budget_amount",
                    "over_budget_pct",
                    "is_over_budget",
                ],
                "order_by_cols": ['["report_month", false]', '["over_budget_pct", false]'],
                "row_limit": 200,
                "include_search": True,
                "page_length": 15,
                "show_cell_bars": True,
                "color_pn": True,
            },
        )

        # === DASHBOARD 2: PHÂN TÍCH HÀNH VI CHI TIÊU (SPENDING BEHAVIOR) ===
        c2_heatmap = upsert_chart(
            "Heatmap: Mật Độ Chi Tiêu Theo Khung Giờ × Thứ Trong Tuần (Câu hỏi 3)",
            "vw_spending_heatmap",
            "heatmap_v2",
            {
                "x_axis": "hour_label",
                "groupby": "day_name",
                "metric": make_adhoc_metric("total_spending", "SUM", "Tổng chi tiêu (VND)"),
                "linear_color_scheme": "superset_seq_1",
                "show_values": False,
                "show_legend": True,
                "normalize_across": "heatmap",
                "yscale_interval": -1,
                "xscale_interval": -1,
                "sort_x_axis": "alpha_asc",
                "row_limit": 500,
            },
        )
        c2_donut = upsert_chart(
            "Tỷ Trọng Chi Tiêu Theo Danh Mục (Donut Chart)",
            "vw_clean_transactions",
            "pie",
            {
                "groupby": ["category_name"],
                "metric": make_adhoc_metric("abs_amount", "SUM", "Tổng chi (VND)"),
                "adhoc_filters": [make_filter("direction", "==", "EXPENSE")],
                "donut": True,
                "innerRadius": 45,
                "outerRadius": 75,
                "show_labels": True,
                "label_type": "key_percent",
                "show_legend": True,
                "color_scheme": "supersetColors",
                "row_limit": 20,
            },
        )
        c2_accounts = upsert_chart(
            "Phân Bổ Chi Tiêu Theo Nguồn Tiền / Ví Điện Tử",
            "vw_clean_transactions",
            "pie",
            {
                "groupby": ["account_name"],
                "metric": make_adhoc_metric("abs_amount", "SUM", "Tổng chi (VND)"),
                "adhoc_filters": [make_filter("direction", "==", "EXPENSE")],
                "donut": True,
                "innerRadius": 40,
                "outerRadius": 75,
                "show_labels": True,
                "label_type": "key_percent",
                "show_legend": True,
                "color_scheme": "supersetColors",
            },
        )
        c2_merchants = upsert_chart(
            "Top Đơn Vị Thụ Hưởng (Merchants) Chi Tiêu Nhiều Nhất",
            "vw_clean_transactions",
            "table",
            {
                "query_mode": "aggregate",
                "groupby": ["merchant_name", "category_name"],
                "metrics": [
                    make_adhoc_metric("transaction_id", "COUNT", "Số giao dịch"),
                    make_adhoc_metric("abs_amount", "SUM", "Tổng chi tiêu (VND)"),
                    make_adhoc_metric("abs_amount", "AVG", "Trung bình / GD (VND)"),
                ],
                "adhoc_filters": [make_filter("direction", "==", "EXPENSE")],
                "order_desc": True,
                "row_limit": 20,
                "show_cell_bars": True,
                "include_search": True,
            },
        )
        c2_drilldown = upsert_chart(
            "Bảng Chi Tiết Giao Dịch Sạch (Drill-down & Tìm Kiếm)",
            "vw_clean_transactions",
            "table",
            {
                "query_mode": "raw",
                "all_columns": [
                    "full_date",
                    "hour",
                    "day_name",
                    "account_name",
                    "category_name",
                    "merchant_name",
                    "direction",
                    "amount",
                    "clean_description",
                    "source_type",
                ],
                "order_by_cols": ['["full_date", false]'],
                "row_limit": 500,
                "include_search": True,
                "page_length": 15,
                "color_pn": True,
            },
        )

        # === DASHBOARD 3: DỰ BÁO & CẢNH BÁO AI (AI FORECAST & ANOMALIES) ===
        c3_fc_total = upsert_chart(
            "KPI: Tổng Chi Tiêu Dự Báo 30 Ngày Tới (VND)",
            "vw_burn_rate_gauge",
            "big_number_total",
            {
                "metric": make_adhoc_metric("total_30d_forecast", "MAX", "Dự báo 30 ngày (VND)"),
                "subheader": "Mô hình chuỗi thời gian SARIMAX (MAPE 8.77%)",
                "y_axis_format": ",.0f",
                "header_font_size": 0.4,
                "subheader_font_size": 0.15,
            },
        )
        c3_anom_count = upsert_chart(
            "KPI: Giao Dịch Bất Thường Cần Rà Soát",
            "vw_burn_rate_gauge",
            "big_number_total",
            {
                "metric": make_adhoc_metric("total_anomalies", "MAX", "Số giao dịch bất thường"),
                "subheader": "Câu hỏi 5: Isolation Forest + Z-Score (>2.5σ)",
                "y_axis_format": ",.0f",
                "header_font_size": 0.4,
                "subheader_font_size": 0.15,
            },
        )
        c3_eom_balance = upsert_chart(
            "KPI: Dự Phóng Số Dư Cuối Tháng (VND)",
            "vw_burn_rate_gauge",
            "big_number_total",
            {
                "metric": make_adhoc_metric("projected_eom_balance", "MAX", "Số dư cuối tháng"),
                "subheader": "Thu nhập tháng - (Thực chi + Dự báo ngày còn lại)",
                "y_axis_format": ",.0f",
                "header_font_size": 0.4,
                "subheader_font_size": 0.15,
            },
        )
        c3_forecast_line = upsert_chart(
            "Dự Báo Chi Tiêu 30 Ngày Tới Kèm Khoảng Tin Cậy 95% (SARIMAX/ARIMA)",
            "vw_ai_forecast_combined",
            "echarts_timeseries_line",
            {
                "x_axis": "record_date",
                "time_grain_sqla": "P1D",
                "metrics": [
                    make_adhoc_metric("actual_spending", "SUM", "Chi tiêu thực tế (VND)"),
                    make_adhoc_metric("predicted_spending", "SUM", "Dự báo AI (VND)"),
                    make_adhoc_metric("upper_bound", "SUM", "Cận trên 95%"),
                    make_adhoc_metric("lower_bound", "SUM", "Cận dưới 95%"),
                ],
                "color_scheme": "supersetColors",
                "show_legend": True,
                "y_axis_format": ",.0f",
                "rich_tooltip": True,
                "markerEnabled": True,
                "markerSize": 4,
            },
        )
        c3_anomalies_table = upsert_chart(
            "Danh Sách Giao Dịch Bất Thường AI Cảnh Báo (Câu hỏi 5)",
            "vw_anomaly_feed",
            "table",
            {
                "query_mode": "raw",
                "all_columns": [
                    "full_date",
                    "day_name",
                    "hour",
                    "account_name",
                    "category_name",
                    "amount",
                    "anomaly_score",
                    "clean_description",
                    "source_type",
                ],
                "order_by_cols": ['["anomaly_score", false]'],
                "row_limit": 100,
                "include_search": True,
                "page_length": 15,
                "show_cell_bars": True,
                "color_pn": True,
            },
        )

        # ------------------------------------------------------------------
        # 4. Xây dựng 3 Dashboards Hoàn Chỉnh
        # ------------------------------------------------------------------
        dashboards_spec = [
            (
                "01. Tổng quan Dòng tiền (Cashflow Overview)",
                "cashflow-overview",
                "01_cashflow_overview.json",
                [
                    [(c1_income, 3, 24), (c1_expense, 3, 24), (c1_savings_rate, 3, 24), (c1_eom_balance, 3, 24)],
                    [(c1_gauge, 5, 48), (c1_monthly_bar, 7, 48)],
                    [(c1_sankey, 12, 56)],
                    [(c1_budget_table, 12, 54)],
                ],
            ),
            (
                "02. Phân tích Hành vi Chi tiêu (Spending Behavior)",
                "spending-behavior",
                "02_spending_behavior.json",
                [
                    [(c2_heatmap, 12, 56)],
                    [(c2_donut, 6, 52), (c2_accounts, 6, 52)],
                    [(c2_merchants, 12, 50)],
                    [(c2_drilldown, 12, 56)],
                ],
            ),
            (
                "03. Dự báo & Cảnh báo AI (AI Forecast & Anomalies)",
                "ai-forecast-anomalies",
                "03_ai_forecast_anomalies.json",
                [
                    [(c3_fc_total, 4, 24), (c3_anom_count, 4, 24), (c3_eom_balance, 4, 24)],
                    [(c3_forecast_line, 12, 60)],
                    [(c3_anomalies_table, 12, 54)],
                ],
            ),
        ]

        os.makedirs(EXPORT_DIR, exist_ok=True)
        os.makedirs(DATASOURCE_DIR, exist_ok=True)

        created_dashboards = []
        for title, slug, export_file, layout_rows in dashboards_spec:
            dash_slices = [slc for row in layout_rows for (slc, _, _) in row]
            pos_json = build_grid_position(title, layout_rows)
            meta_json = {
                "cross_filters_enabled": True,
                "color_scheme": "supersetColors",
                "refresh_frequency": 0,
                "timed_refresh_immune_slices": [],
                "expanded_slices": {},
                "shared_label_colors": {},
            }

            dash = db.session.query(Dashboard).filter_by(slug=slug).first()
            if not dash:
                dash = Dashboard(
                    dashboard_title=title,
                    slug=slug,
                    published=True,
                    position_json=json.dumps(pos_json, ensure_ascii=False),
                    json_metadata=json.dumps(meta_json, ensure_ascii=False),
                    slices=dash_slices,
                    owners=owners,
                )
                db.session.add(dash)
            else:
                dash.dashboard_title = title
                dash.published = True
                dash.position_json = json.dumps(pos_json, ensure_ascii=False)
                dash.json_metadata = json.dumps(meta_json, ensure_ascii=False)
                dash.slices = dash_slices
            db.session.commit()
            created_dashboards.append(dash)
            print(f"[✓] Dashboard sẵn sàng: '{title}' (id={dash.id}, slug={slug}, charts={len(dash_slices)})")

            # Xuất bản sao JSON đặc tả Dashboard ra thư mục dashboards_export/
            export_payload = {
                "dashboard_id": dash.id,
                "dashboard_title": dash.dashboard_title,
                "slug": dash.slug,
                "published": dash.published,
                "position_json": pos_json,
                "json_metadata": meta_json,
                "charts": [
                    {
                        "id": s.id,
                        "slice_name": s.slice_name,
                        "viz_type": s.viz_type,
                        "datasource_id": s.datasource_id,
                        "params": json.loads(s.params),
                    }
                    for s in dash_slices
                ],
            }
            with open(os.path.join(EXPORT_DIR, export_file), "w", encoding="utf-8") as f:
                json.dump(export_payload, f, ensure_ascii=False, indent=2)

        # Xuất cấu hình datasources YAML
        ds_yaml_lines = [
            "# Cấu hình Database & 8 Semantic Views cho Apache Superset (Nhóm 13 - 65HTTT)",
            f"database_name: \"{db_name}\"",
            f"sqlalchemy_uri: \"postgresql+psycopg2://{pg_user}:<PASSWORD>@{pg_host}:{pg_port}/{pg_db}\"",
            "datasets:",
        ]
        for tbl_name, main_dttm in view_configs:
            ds_yaml_lines.append(f"  - table_name: {tbl_name}")
            ds_yaml_lines.append(f"    schema: public")
            if main_dttm:
                ds_yaml_lines.append(f"    main_dttm_col: {main_dttm}")
        with open(os.path.join(DATASOURCE_DIR, "superset_datasources.yaml"), "w", encoding="utf-8") as f:
            f.write("\n".join(ds_yaml_lines) + "\n")

        print(f"\n[DONE] Đã khởi tạo thành công {len(created_dashboards)} Dashboards, 18 Charts và xuất file JSON!")


if __name__ == "__main__":
    try:
        provision()
    except Exception as exc:
        print(f"[ERROR] Lỗi provisioning Superset: {exc}", file=sys.stderr)
        raise
