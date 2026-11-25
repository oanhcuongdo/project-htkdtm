import numpy as np
import pandas as pd


class ZScoreDetector:
    """
    Phát hiện giao dịch đột biến bằng thống kê độ lệch chuẩn Z-Score theo từng danh mục chi tiêu.
    Ngưỡng cảnh báo chuẩn theo Đề cương: |Z| > 2.5 sigma.
    """

    Z_THRESHOLD = 2.5

    @classmethod
    def compute_category_zscores(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Nhận DataFrame chứa cột ['transaction_id', 'category_id', 'abs_amount', 'hour'].
        Trả về DataFrame bổ sung ['cat_mean', 'cat_std', 'cat_median', 'z_score', 'is_zscore_anomaly'].
        """
        result = df.copy()
        if result.empty:
            for col in ("cat_mean", "cat_std", "cat_median", "z_score", "is_zscore_anomaly"):
                result[col] = []
            return result

        stats = result.groupby("category_id")["abs_amount"].agg(["mean", "std", "median", "count"]).reset_index()
        stats.columns = ["category_id", "cat_mean", "cat_std", "cat_median", "cat_count"]
        result = result.merge(stats, on="category_id", how="left")

        # Tránh chia cho 0 với danh mục cố định (ví dụ: tiền nhà mỗi tháng đều đúng 3.500.000)
        def _calc_z(row):
            if row["cat_count"] < 3 or pd.isna(row["cat_std"]) or row["cat_std"] < 1.0:
                return 0.0
            return float((row["abs_amount"] - row["cat_mean"]) / row["cat_std"])

        result["z_score"] = result.apply(_calc_z, axis=1)
        result["is_zscore_anomaly"] = (result["z_score"] > cls.Z_THRESHOLD) | (
            result["hour"].isin([0, 1, 2, 3, 4]) & (result["abs_amount"] >= 1_000_000)
        )
        return result
