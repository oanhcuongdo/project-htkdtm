import json
import os
from typing import Dict, Any, Optional
import joblib
import numpy as np

from .rule_based_matcher import RuleBasedMatcher, CATEGORY_NAMES
from .vietnamese_text import preprocess_banking_text

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "category_classifier.joblib")
EVAL_PATH = os.path.join(MODEL_DIR, "classifier_eval.json")


class VietnameseTransactionClassifier:
    """
    Mô hình AI kết hợp (Hybrid Rule-based + TF-IDF Word/Char N-gram ML Classifier)
    chuyên xử lý chuỗi chuyển khoản tiếng Việt không dấu, viết tắt, có mã rác ngân hàng.
    """

    def __init__(self, model_path: str = MODEL_PATH):
        self.model_path = model_path
        self.pipeline = None
        self._load_if_exists()

    def _load_if_exists(self):
        if os.path.exists(self.model_path):
            try:
                self.pipeline = joblib.load(self.model_path)
            except Exception:
                self.pipeline = None

    def ensure_trained(self):
        if self.pipeline is None:
            from .train_classifier import train_and_evaluate_classifier
            train_and_evaluate_classifier(save_model=True)
            self._load_if_exists()

    def predict(
        self,
        raw_description: str,
        counterparty: str = "",
        direction: Optional[str] = None,
        use_rules_first: bool = True,
    ) -> Dict[str, Any]:
        """Phân loại 1 mô tả giao dịch tiếng Việt thành danh mục kèm xác suất tin cậy."""
        # Bước 1: Kiểm tra bộ luật độ chính xác cao (Fast Path)
        if use_rules_first:
            rule_hit = RuleBasedMatcher.match(raw_description, counterparty)
            if rule_hit:
                return rule_hit

        # Bước 2: Dùng mô hình Machine Learning NLP (Word + Char N-gram TF-IDF + Calibrated Linear/Logistic)
        self.ensure_trained()
        cleaned = preprocess_banking_text(raw_description, counterparty)

        if self.pipeline is None or not cleaned:
            fallback_id = 13 if direction == "INCOME" else 1
            return {
                "category_id": fallback_id,
                "category_name": CATEGORY_NAMES[fallback_id],
                "confidence": 0.50,
                "method": "fallback",
                "preprocessed_text": cleaned,
            }

        probs = self.pipeline.predict_proba([cleaned])[0]
        classes = self.pipeline.classes_

        # Ràng buộc chiều dòng tiền nếu được cung cấp (INCOME chỉ chọn trong nhóm thu nhập nếu xác suất hợp lý)
        income_cats = {12, 13, 14}
        if direction == "INCOME":
            mask = np.array([int(c) in income_cats for c in classes])
            if mask.any() and probs[mask].max() >= 0.15:
                masked_probs = np.where(mask, probs, -1.0)
                best_idx = int(np.argmax(masked_probs))
            else:
                best_idx = int(np.argmax(probs))
        else:
            best_idx = int(np.argmax(probs))

        cat_id = int(classes[best_idx])
        confidence = round(float(probs[best_idx]), 4)

        # Lấy top 3 danh mục gợi ý
        top3_indices = np.argsort(probs)[::-1][:3]
        top3 = [
            {
                "category_id": int(classes[i]),
                "category_name": CATEGORY_NAMES.get(int(classes[i]), "Khác"),
                "probability": round(float(probs[i]), 4),
            }
            for i in top3_indices
        ]

        return {
            "category_id": cat_id,
            "category_name": CATEGORY_NAMES.get(cat_id, "Khác"),
            "confidence": confidence,
            "method": "ml_nlp_tfidf",
            "preprocessed_text": cleaned,
            "top_predictions": top3,
        }

    @staticmethod
    def load_evaluation_report() -> Optional[Dict[str, Any]]:
        if os.path.exists(EVAL_PATH):
            with open(EVAL_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return None


_classifier_singleton: Optional[VietnameseTransactionClassifier] = None


def get_classifier() -> VietnameseTransactionClassifier:
    global _classifier_singleton
    if _classifier_singleton is None:
        _classifier_singleton = VietnameseTransactionClassifier()
    return _classifier_singleton
