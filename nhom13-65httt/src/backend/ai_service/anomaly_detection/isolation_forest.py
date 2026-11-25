import time
from datetime import datetime
from typing import Dict, Any, List
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sqlalchemy import text

from api.dependencies import get_db_session
from .zscore_detector import ZScoreDetector


class AnomalyDetectionService:
    """
    Dịch vụ phát hiện giao dịch bất thường kết hợp:
    1. Isolation Forest đa chiều (Số tiền log, tỷ lệ so với trung vị danh mục, khung giờ khuya, Z-Score).
    2. Z-Score thống kê theo từng danh mục (> 2.5 sigma).
    Tự động cập nhật cờ is_anomaly và anomaly_score ngược lại vào bảng fact_transactions.
    """

    def __init__(self, contamination: float = 0.03, min_anomaly_amount: float = 1_000_000.0):
        self.contamination = contamination
        self.min_anomaly_amount = min_anomaly_amount

    def detect_and_update_db(self, persist: bool = True) -> Dict[str, Any]:
        t0 = time.time()
        started_at = datetime.now()

        with get_db_session() as db:
            rows = db.execute(
                text("""
                    SELECT
                        f.transaction_id,
                        f.category_id,
                        c.category_name,
                        ABS(f.amount)::FLOAT AS abs_amount,
                        f.amount::FLOAT AS signed_amount,
                        f.clean_description,
                        f.raw_description,
                        d.full_date,
                        d.hour,
                        d.is_weekend,
                        a.account_name
                    FROM fact_transactions f
                    JOIN dim_date d ON f.date_id = d.date_id
                    JOIN dim_category c ON f.category_id = c.category_id
                    JOIN dim_account a ON f.account_id = a.account_id
                    WHERE f.direction = 'EXPENSE'
                      AND f.is_internal_transfer = FALSE
                    ORDER BY f.transaction_id
                """)
            ).mappings().all()

            if not rows:
                return {"status": "empty", "total_evaluated": 0, "anomalies_detected": 0, "anomalies": []}

            df = pd.DataFrame([dict(r) for r in rows])

            # Bước 1: Tính Z-Score theo từng danh mục
            df = ZScoreDetector.compute_category_zscores(df)

            # Bước 2: Xây dựng đặc trưng đa chiều cho Isolation Forest
            df["log_amount"] = np.log1p(df["abs_amount"])
            df["ratio_to_median"] = df["abs_amount"] / df["cat_median"].clip(lower=1.0)
            df["is_late_night"] = df["hour"].isin([0, 1, 2, 3, 4]).astype(float)
            df["is_weekend_num"] = df["is_weekend"].astype(float)

            feature_cols = ["log_amount", "ratio_to_median", "z_score", "is_late_night", "is_weekend_num"]
            X = df[feature_cols].fillna(0.0).values

            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            iso = IsolationForest(
                n_estimators=150,
                contamination=self.contamination,
                random_state=42,
            )
            if_preds = iso.fit_predict(X_scaled)  # -1 = anomaly, 1 = normal
            raw_decision = iso.decision_function(X_scaled)  # Giá trị càng âm càng bất thường

            # Chuẩn hóa điểm Isolation Forest về thang [0.0, 1.0] (càng gần 1 càng bất thường)
            min_d, max_d = float(raw_decision.min()), float(raw_decision.max())
            if max_d > min_d:
                if_scores = (max_d - raw_decision) / (max_d - min_d)
            else:
                if_scores = np.zeros(len(df))

            # Chuẩn hóa điểm Z-Score về thang [0.0, 1.0]
            z_scores_norm = np.clip(df["z_score"].values / 5.0, 0.0, 1.0)

            # Điểm tổng hợp Ensemble
            ensemble_scores = np.clip(0.55 * if_scores + 0.45 * z_scores_norm, 0.0, 0.9999)
            df["if_pred"] = if_preds
            df["anomaly_score"] = np.round(ensemble_scores, 4)

            # Luật quyết định bất thường Ensemble (tránh báo giả các giao dịch nhỏ lẻ hoặc tiền nhà định kỳ)
            def _decide(row):
                reasons = []
                is_anom = False

                if row["z_score"] > ZScoreDetector.Z_THRESHOLD and row["abs_amount"] >= self.min_anomaly_amount:
                    is_anom = True
                    reasons.append(f"Chi tiêu vượt ngưỡng {row['z_score']:.2f}σ so với trung bình danh mục '{row['category_name']}'")

                if row["is_late_night"] == 1.0 and row["abs_amount"] >= self.min_anomaly_amount:
                    is_anom = True
                    reasons.append(f"Phát sinh giao dịch giá trị cao ({row['abs_amount']:,.0f} VND) lúc {int(row['hour'])}h đêm")

                if row["if_pred"] == -1 and row["ratio_to_median"] >= 4.0 and row["abs_amount"] >= self.min_anomaly_amount:
                    is_anom = True
                    reasons.append(f"Isolation Forest phát hiện lệch chuẩn gấp {row['ratio_to_median']:.1f}x trung vị danh mục")

                return is_anom, "; ".join(reasons)

            decisions = df.apply(_decide, axis=1)
            df["is_anomaly"] = [d[0] for d in decisions]
            df["anomaly_reason"] = [d[1] for d in decisions]

            # Tăng điểm tin cậy lên >= 0.80 đối với các giao dịch đã xác định bất thường rõ ràng
            df.loc[df["is_anomaly"], "anomaly_score"] = np.maximum(
                df.loc[df["is_anomaly"], "anomaly_score"], 0.82
            ).round(4)

            if persist:
                # Reset trạng thái cũ cho các giao dịch thu nhập/nội bộ và cập nhật đồng loạt
                db.execute(text("UPDATE fact_transactions SET is_anomaly = FALSE, anomaly_score = 0.0"))
                for _, row in df.iterrows():
                    db.execute(
                        text("""
                            UPDATE fact_transactions
                            SET is_anomaly = :is_anom, anomaly_score = :score
                            WHERE transaction_id = :tx_id
                        """),
                        {
                            "is_anom": bool(row["is_anomaly"]),
                            "score": float(row["anomaly_score"]),
                            "tx_id": int(row["transaction_id"]),
                        },
                    )

                duration = round(time.time() - t0, 2)
                db.execute(
                    text("""
                        INSERT INTO pipeline_execution_logs (
                            pipeline_name, status, records_processed, records_failed,
                            duration_seconds, started_at, finished_at
                        ) VALUES (
                            'AI_Anomaly_Detection', 'SUCCESS', :proc, 0, :dur, :start_at, :end_at
                        )
                    """),
                    {
                        "proc": len(df),
                        "dur": duration,
                        "start_at": started_at,
                        "end_at": datetime.now(),
                    },
                )

            anomalies_df = df[df["is_anomaly"]].sort_values("anomaly_score", ascending=False)
            anomalies_list: List[Dict[str, Any]] = [
                {
                    "transaction_id": int(r["transaction_id"]),
                    "full_date": str(r["full_date"]),
                    "hour": int(r["hour"]),
                    "account_name": r["account_name"],
                    "category_name": r["category_name"],
                    "amount": float(r["signed_amount"]),
                    "description": r["clean_description"] or r["raw_description"],
                    "z_score": round(float(r["z_score"]), 2),
                    "anomaly_score": float(r["anomaly_score"]),
                    "reason": r["anomaly_reason"],
                }
                for _, r in anomalies_df.iterrows()
            ]

        return {
            "model": "Ensemble IsolationForest + Category Z-Score (>2.5σ)",
            "total_evaluated": int(len(df)),
            "anomalies_detected": len(anomalies_list),
            "anomaly_rate_pct": round(len(anomalies_list) * 100.0 / max(len(df), 1), 2),
            "persisted_to_db": persist,
            "duration_seconds": round(time.time() - t0, 2),
            "anomalies": anomalies_list,
        }
