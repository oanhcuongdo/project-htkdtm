from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from ai_service.anomaly_detection import AnomalyDetectionService
from ai_service.category_classifier import get_classifier
from ai_service.category_classifier.train_classifier import train_and_evaluate_classifier
from ai_service.forecasting import BurnRateAnalyzer, CashflowForecaster

router = APIRouter(prefix="/api/v1/ai", tags=["AI Intelligence Layer"])


class ClassifyRequest(BaseModel):
    description: str
    counterparty: str = ""
    direction: Optional[str] = None


class BatchClassifyRequest(BaseModel):
    items: List[ClassifyRequest]


@router.post("/classify")
def classify_transaction(payload: ClassifyRequest):
    """Phân loại 1 mô tả giao dịch tiếng Việt (không dấu/viết tắt) thành danh mục kèm xác suất."""
    clf = get_classifier()
    return clf.predict(
        raw_description=payload.description,
        counterparty=payload.counterparty,
        direction=payload.direction,
    )


@router.post("/classify-batch")
def classify_transactions_batch(payload: BatchClassifyRequest):
    """Phân loại hàng loạt nhiều mô tả giao dịch."""
    clf = get_classifier()
    results = [
        {
            "input": item.description,
            "prediction": clf.predict(
                raw_description=item.description,
                counterparty=item.counterparty,
                direction=item.direction,
            ),
        }
        for item in payload.items
    ]
    return {"total": len(results), "results": results}


@router.post("/train-classifier")
def retrain_classifier(include_db: bool = True):
    """Huấn luyện lại mô hình NLP phân loại danh mục và trả về báo cáo Accuracy, F1-Score, Confusion Matrix."""
    report = train_and_evaluate_classifier(save_model=True, include_db=include_db)
    # Tải lại mô hình vừa huấn luyện vào singleton
    get_classifier()._load_if_exists()
    return report


@router.post("/detect-anomalies")
def run_anomaly_detection(persist: bool = True, contamination: float = 0.03):
    """Chạy mô hình Isolation Forest + Z-Score (>2.5σ) và cập nhật cờ is_anomaly vào fact_transactions."""
    service = AnomalyDetectionService(contamination=contamination)
    return service.detect_and_update_db(persist=persist)


@router.post("/forecast")
def run_cashflow_forecast(horizon_days: int = 30, persist: bool = True):
    """Dự báo chi tiêu 30 ngày tới bằng SARIMAX/ARIMA, đánh giá MAPE và lưu vào ai_spending_forecast."""
    forecaster = CashflowForecaster()
    return forecaster.run_forecast(horizon_days=horizon_days, persist=persist)


@router.get("/burn-rate")
def get_burn_rate(year: Optional[int] = None, month: Optional[int] = None):
    """Tính tốc độ đốt ngân sách (Burn-rate) và dự phóng số dư cuối tháng (Câu hỏi nghiệp vụ số 4)."""
    return BurnRateAnalyzer.analyze_month(year=year, month=month)


@router.get("/evaluation-report")
def get_ai_evaluation_report():
    """Tổng hợp báo cáo đánh giá KPI của toàn bộ tầng AI (F1-Score >= 85%, MAPE < 15%)."""
    clf = get_classifier()
    clf_eval = clf.load_evaluation_report()
    fc_eval = CashflowForecaster.load_evaluation_report()
    return {
        "nlp_classifier": clf_eval or {"status": "not_trained_yet"},
        "cashflow_forecaster": fc_eval or {"status": "not_evaluated_yet"},
    }
