import pandas as pd
from ai_service.anomaly_detection.zscore_detector import ZScoreDetector
from ai_service.category_classifier.train_classifier import train_and_evaluate_classifier
from ai_service.category_classifier.nlp_classifier import VietnameseTransactionClassifier
from ai_service.category_classifier.vietnamese_text import preprocess_banking_text


def test_vietnamese_text_preprocessing():
    cleaned = preprocess_banking_text("MBVCB.987654321.ck tien an trua cty t11")
    assert "chuyen khoan" in cleaned
    assert "cong ty" in cleaned
    assert "thang" in cleaned
    assert "mbvcb" not in cleaned


def test_classifier_meets_kpi_f1_over_85_percent():
    report = train_and_evaluate_classifier(save_model=False, include_db=False)
    assert report["metrics"]["curated_unseen_f1_weighted"] >= 0.85
    assert report["metrics"]["f1_weighted"] >= 0.85
    assert report["kpi_passed"] is True


def test_classifier_predictions_on_vietnamese_slang():
    clf = VietnameseTransactionClassifier()
    clf.ensure_trained()

    res_food = clf.predict("MBVCB.112233.ck tien com trua van phong")
    assert res_food["category_id"] == 1

    res_rent = clf.predict("tra tien phong tro t11 cho bac hung")
    assert res_rent["category_id"] == 2

    res_elec = clf.predict("thanh toan hoa don tien dien EVN")
    assert res_elec["category_id"] == 3

    res_salary = clf.predict("CTY ABC tra luong thang 10")
    assert res_salary["category_id"] == 12

    res_internal = clf.predict("CUSTOMER MOMO-CASHIN-0977294663 bank2wallet")
    assert res_internal["category_id"] == 15


def test_zscore_anomaly_detector():
    # 10 giao dịch ăn uống bình thường ~50k và 1 giao dịch đột biến 2.500.000
    data = [
        {"transaction_id": i, "category_id": 1, "abs_amount": 50000.0 + (i * 2000), "hour": 12}
        for i in range(1, 11)
    ]
    data.append({"transaction_id": 99, "category_id": 1, "abs_amount": 2500000.0, "hour": 12})
    df = pd.DataFrame(data)

    scored = ZScoreDetector.compute_category_zscores(df)
    normal_flags = scored[scored["transaction_id"] != 99]["is_zscore_anomaly"].any()
    outlier_row = scored[scored["transaction_id"] == 99].iloc[0]

    assert not normal_flags
    assert bool(outlier_row["is_zscore_anomaly"]) is True
    assert outlier_row["z_score"] > 2.5
