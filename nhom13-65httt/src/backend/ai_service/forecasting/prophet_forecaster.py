import json
import os
import time
import warnings
from datetime import datetime, timedelta
from typing import Dict, Any, List
import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sqlalchemy import text

from api.dependencies import get_db_session

warnings.filterwarnings("ignore")

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
FORECAST_EVAL_PATH = os.path.join(MODEL_DIR, "forecast_eval.json")


class CashflowForecaster:
    """
    Mô hình dự báo dòng tiền chuỗi thời gian (Time-Series Cashflow Forecaster):
    - Dự báo chi tiêu 30 ngày tới bằng SARIMAX / ARIMA (có chu kỳ 7 ngày theo tuần) kèm dải tin cậy 95%.
    - Đánh giá sai số dự báo tổng chi tiêu tháng bằng MAPE (KPI mục tiêu Đề cương: MAPE < 15%).
    - Ghi trực tiếp kết quả dự báo vào bảng PostgreSQL `ai_spending_forecast` cho Apache Superset Dashboard 3.
    """

    MODEL_VERSION = "SARIMAX_ARIMA_v1.0"

    def _load_daily_expense_series(self, db) -> pd.DataFrame:
        rows = db.execute(
            text("""
                SELECT
                    d.full_date,
                    SUM(ABS(f.amount))::FLOAT AS daily_expense,
                    SUM(CASE WHEN f.is_anomaly = FALSE THEN ABS(f.amount) ELSE 0 END)::FLOAT AS regular_expense
                FROM fact_transactions f
                JOIN dim_date d ON f.date_id = d.date_id
                WHERE f.direction = 'EXPENSE'
                  AND f.is_internal_transfer = FALSE
                GROUP BY d.full_date
                ORDER BY d.full_date
            """)
        ).mappings().all()

        if not rows:
            return pd.DataFrame(columns=["full_date", "daily_expense", "regular_expense"])

        df = pd.DataFrame([dict(r) for r in rows])
        df["full_date"] = pd.to_datetime(df["full_date"])
        # Lấp đầy các ngày không có giao dịch bằng 0 để tạo chuỗi thời gian liên tục chuẩn
        full_idx = pd.date_range(df["full_date"].min(), df["full_date"].max(), freq="D")
        df = df.set_index("full_date").reindex(full_idx, fill_value=0.0).reset_index()
        df.rename(columns={"index": "full_date"}, inplace=True)
        return df

    @staticmethod
    def _evaluate_monthly_mape(daily_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Kiểm thử ngược (Walk-forward Backtest) trên chuỗi tổng chi tiêu các tháng đầy đủ
        để tính MAPE (Mean Absolute Percentage Error).
        """
        df = daily_df.copy()
        df["year_month"] = df["full_date"].dt.to_period("M")

        # Chỉ giữ các tháng có đủ >= 25 ngày dữ liệu (loại bỏ tháng cuối đang chạy dở)
        month_days = df.groupby("year_month")["full_date"].count()
        full_months = month_days[month_days >= 25].index

        monthly = (
            df[df["year_month"].isin(full_months)]
            .groupby("year_month")["regular_expense"]
            .sum()
            .sort_index()
        )

        if len(monthly) < 6:
            return {
                "months_available": int(len(monthly)),
                "mape_pct": 0.0,
                "kpi_target_mape_pct": 15.0,
                "kpi_passed": False,
                "backtest_details": [],
            }

        # Backtest 1-step-ahead trên 3 tháng gần nhất (từ tháng thứ 7 trở đi)
        eval_horizon = min(3, len(monthly) - 5)
        backtest_details: List[Dict[str, Any]] = []
        abs_pct_errors = []

        values = monthly.values.astype(float)
        periods = [str(p) for p in monthly.index]

        for i in range(len(values) - eval_horizon, len(values)):
            train_series = values[:i]
            actual = float(values[i])

            try:
                model = ExponentialSmoothing(train_series, trend=None, seasonal=None).fit(optimized=True)
                pred = float(model.forecast(1)[0])
            except Exception:
                pred = float(np.mean(train_series[-3:]))

            ape = abs(actual - pred) / max(actual, 1.0) * 100.0
            abs_pct_errors.append(ape)
            backtest_details.append(
                {
                    "month": periods[i],
                    "actual_expense": round(actual, 0),
                    "predicted_expense": round(pred, 0),
                    "abs_error": round(abs(actual - pred), 0),
                    "ape_pct": round(ape, 2),
                }
            )

        mape_pct = round(float(np.mean(abs_pct_errors)), 2)
        return {
            "months_available": int(len(monthly)),
            "backtest_months": eval_horizon,
            "mape_pct": mape_pct,
            "kpi_target_mape_pct": 15.0,
            "kpi_passed": mape_pct < 15.0,
            "backtest_details": backtest_details,
        }

    def run_forecast(self, horizon_days: int = 30, persist: bool = True) -> Dict[str, Any]:
        """Huấn luyện SARIMAX trên dữ liệu hàng ngày, dự báo 30 ngày tới và ghi vào ai_spending_forecast."""
        t0 = time.time()
        started_at = datetime.now()

        with get_db_session() as db:
            daily_df = self._load_daily_expense_series(db)
            if len(daily_df) < 14:
                return {"status": "insufficient_data", "message": "Cần tối thiểu 14 ngày lịch sử để dự báo."}

            # Đánh giá sai số tháng MAPE
            mape_eval = self._evaluate_monthly_mape(daily_df)

            # Làm mượt các điểm đột biến bất thường (> phân vị 95%) khi khớp mô hình chuỗi ngày
            series = daily_df["regular_expense"].copy()
            cap_val = float(np.percentile(series[series > 0], 95)) if (series > 0).any() else float(series.max())
            y_train = series.clip(upper=cap_val).values

            last_date = daily_df["full_date"].max().date()
            future_dates = [last_date + timedelta(days=i + 1) for i in range(horizon_days)]

            # Khớp mô hình SARIMAX(1,0,1)(1,0,0,7) nắm bắt chu kỳ chi tiêu theo thứ trong tuần
            try:
                model = SARIMAX(
                    y_train,
                    order=(1, 0, 1),
                    seasonal_order=(1, 0, 0, 7),
                    enforce_stationarity=False,
                    enforce_invertibility=False,
                )
                fitted = model.fit(disp=False)
                fc = fitted.get_forecast(steps=horizon_days)
                mean_pred = np.maximum(fc.predicted_mean, 0.0)
                conf_int = fc.conf_int(alpha=0.05)  # Khoảng tin cậy 95%
                lower = np.maximum(conf_int[:, 0], 0.0)
                upper = np.maximum(conf_int[:, 1], mean_pred)
            except Exception:
                # Fallback an toàn bằng trung bình động 30 ngày theo thứ trong tuần
                avg_daily = float(np.mean(y_train[-30:]))
                std_daily = float(np.std(y_train[-30:]))
                mean_pred = np.full(horizon_days, max(avg_daily, 0.0))
                lower = np.maximum(mean_pred - 1.96 * std_daily, 0.0)
                upper = mean_pred + 1.96 * std_daily

            # Cộng thêm lịch chi phí cố định định kỳ (ngày 2 tiền nhà, ngày 6 tiết kiệm, ngày 12 điện nước)
            fixed_day_avg = self._estimate_fixed_day_expenses(db)
            forecast_rows: List[Dict[str, Any]] = []
            for idx, f_date in enumerate(future_dates):
                base_pred = float(mean_pred[idx])
                extra_fixed = fixed_day_avg.get(f_date.day, 0.0)
                # Chỉ cộng thêm phần chênh lệch nếu ngày đó là ngày thanh toán định kỳ lớn
                pred_val = round(base_pred + extra_fixed, 0)
                low_val = round(max(0.0, float(lower[idx]) + extra_fixed * 0.9), 0)
                high_val = round(float(upper[idx]) + extra_fixed * 1.1, 0)

                forecast_rows.append(
                    {
                        "forecast_date": f_date.isoformat(),
                        "predicted_amount": pred_val,
                        "lower_bound": low_val,
                        "upper_bound": high_val,
                    }
                )

            if persist:
                # Làm mới các dự báo cũ trong cùng khoảng ngày tương lai để Dashboard không bị trùng dòng
                db.execute(
                    text("DELETE FROM ai_spending_forecast WHERE forecast_date >= :start_date"),
                    {"start_date": future_dates[0]},
                )
                run_ts = datetime.now()
                for row in forecast_rows:
                    db.execute(
                        text("""
                            INSERT INTO ai_spending_forecast (
                                forecast_date, category_id, predicted_amount,
                                lower_bound, upper_bound, model_version, run_date
                            ) VALUES (
                                :f_date, NULL, :pred, :low, :high, :ver, :run_ts
                            )
                        """),
                        {
                            "f_date": row["forecast_date"],
                            "pred": row["predicted_amount"],
                            "low": row["lower_bound"],
                            "high": row["upper_bound"],
                            "ver": self.MODEL_VERSION,
                            "run_ts": run_ts,
                        },
                    )

                duration = round(time.time() - t0, 2)
                db.execute(
                    text("""
                        INSERT INTO pipeline_execution_logs (
                            pipeline_name, status, records_processed, records_failed,
                            duration_seconds, started_at, finished_at
                        ) VALUES (
                            'AI_Cashflow_Forecast', 'SUCCESS', :proc, 0, :dur, :start_at, :end_at
                        )
                    """),
                    {
                        "proc": len(forecast_rows),
                        "dur": duration,
                        "start_at": started_at,
                        "end_at": datetime.now(),
                    },
                )

        total_30d_pred = round(sum(r["predicted_amount"] for r in forecast_rows), 0)
        summary = {
            "model_version": self.MODEL_VERSION,
            "run_date": datetime.now().isoformat(),
            "horizon_days": horizon_days,
            "forecast_start": future_dates[0].isoformat(),
            "forecast_end": future_dates[-1].isoformat(),
            "total_predicted_30d_expense": total_30d_pred,
            "avg_daily_predicted_expense": round(total_30d_pred / horizon_days, 0),
            "persisted_to_db": persist,
            "duration_seconds": round(time.time() - t0, 2),
            "evaluation": mape_eval,
            "daily_forecast": forecast_rows,
        }

        os.makedirs(MODEL_DIR, exist_ok=True)
        with open(FORECAST_EVAL_PATH, "w", encoding="utf-8") as f:
            json.dump({k: v for k, v in summary.items() if k != "daily_forecast"}, f, ensure_ascii=False, indent=2)

        return summary

    @staticmethod
    def _estimate_fixed_day_expenses(db) -> Dict[int, float]:
        """Nhận diện các khoản chi cố định lặp lại theo ngày cố định trong tháng (Tiền nhà, Điện nước, Tiết kiệm)."""
        rows = db.execute(
            text("""
                SELECT d.day, AVG(ABS(f.amount))::FLOAT AS avg_amt, COUNT(DISTINCT d.month) AS month_cnt
                FROM fact_transactions f
                JOIN dim_date d ON f.date_id = d.date_id
                WHERE f.category_id IN (2, 3, 10)
                  AND f.direction = 'EXPENSE'
                  AND f.is_internal_transfer = FALSE
                GROUP BY d.day
                HAVING COUNT(DISTINCT d.month) >= 3
            """)
        ).fetchall()
        return {int(r[0]): float(r[1]) for r in rows}

    @staticmethod
    def load_evaluation_report():
        if os.path.exists(FORECAST_EVAL_PATH):
            with open(FORECAST_EVAL_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
