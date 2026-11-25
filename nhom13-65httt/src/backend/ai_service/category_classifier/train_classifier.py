"""
Script huấn luyện và đánh giá mô hình NLP phân loại danh mục giao dịch tiếng Việt.
Sử dụng FeatureUnion(Word TF-IDF + Char-WB TF-IDF) + LogisticRegression
nhằm đạt mục tiêu KPI Đề cương: Accuracy / F1-Score >= 85% trên chuỗi tiếng Việt không dấu/viết tắt.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Tuple
import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC

from .nlp_classifier import EVAL_PATH, MODEL_DIR, MODEL_PATH
from .rule_based_matcher import CATEGORY_NAMES
from .vietnamese_text import preprocess_banking_text

# Tập dữ liệu chuẩn hóa tiếng Việt không dấu / viết tắt / mô tả sao kê ngân hàng thực tế (~260 mẫu đa dạng)
CURATED_VN_DATASET: List[Tuple[str, int]] = [
    # 1: Ăn uống & Cà phê (24 mẫu)
    ("MBVCB.123456.Thanh toan tien an trua com van phong", 1),
    ("ck tien com trua dong nghiep cty", 1),
    ("Highlands Coffee ca phe sang", 1),
    ("tra sua phuc long oolong kem cheese", 1),
    ("MOMO thanh toan WinMart mua thuc pham do an", 1),
    ("an toi bun cha ha noi", 1),
    ("pho bo tai chin buoi sang", 1),
    ("cf sang voi ban tai The Coffee House", 1),
    ("tra sua gong cha ding tea chieu", 1),
    ("di cho mua rau thit ca bach hoa xanh", 1),
    ("EPAY NGUYET HONG SINH TO nuoc ep", 1),
    ("com rang dua bo bun dau mam tom", 1),
    ("banh mi xoi man an sang", 1),
    ("tra chanh cafe sua da quan quen", 1),
    ("mua do an vat banh keo circle k gs25", 1),
    ("thanh toan tien an vat chieu van phong", 1),
    ("dat do an shopeefood baemin bun bo hue", 1),
    ("goi com tam suon bi cha buoi trua", 1),
    ("mua sua tuoi hoa qua sieu thi coopmart", 1),
    ("ca phe muoi sua chua tran chau", 1),
    ("ck tien an sang pho ga va tra da", 1),
    ("thanh toan quan com binh dan gan cty", 1),
    ("uong cafe chieu highlands voi khach", 1),
    ("mua do an nhanh kfc lotteria pizza", 1),

    # 2: Tiền thuê nhà & Phòng trọ (20 mẫu)
    ("Nguyen Van A chuyen tien nha thang 10", 2),
    ("tra tien phong tro t11 bac hung", 2),
    ("ck tien thue nha chung cu mini", 2),
    ("chuyen tien nha tro thang nay", 2),
    ("thanh toan tien coc phong tro moi", 2),
    ("tra tien thue phong t5 chu nha", 2),
    ("phi dich vu chung cu quan ly toa nha", 2),
    ("chuyen khoan tien nha tro cho co lan", 2),
    ("dong tien phong tro thang 8", 2),
    ("chuye n tien nha tro ma gd", 2),
    ("thanh toan tien nha hang thang", 2),
    ("gui chu nha tien phong t12", 2),
    ("ck tien thue phong tro thang 3", 2),
    ("tra tien nha tro cuoi thang", 2),
    ("thanh toan phi quan ly chung cu thang 6", 2),
    ("chuyen tien thue can ho chung cu", 2),
    ("dong tien phong va dich vu toa nha", 2),
    ("ck chu nha tien thue nha t9", 2),
    ("gui bac chu nha tien tro thang 4", 2),
    ("tien phong tro thang 7 thanh toan", 2),

    # 3: Điện nước & Internet (20 mẫu)
    ("MOMO HOADON EVN tien dien thang 9", 3),
    ("thanh toan hoa don tien nuoc sinh hoat", 3),
    ("cuoc internet fpt telecom thang 11", 3),
    ("dong tien mang wifi vnpt viettel", 3),
    ("IRIS TOPUP VIETTEL TOPUP nap the dien thoai", 3),
    ("muathecao thedientu vinaphone mobifone", 3),
    ("thanh toan hoa don dien luc ha noi", 3),
    ("nap tien dien thoai 4g data thang", 3),
    ("dong tien dien nuoc phong tro t7", 3),
    ("cuoc vien thong tra sau viettel", 3),
    ("thanh toan tien wifi cap quang", 3),
    ("hoa don nuoc sach ha noi", 3),
    ("ck tien dien thang 10 evn", 3),
    ("dong cuoc mang internet fpt t8", 3),
    ("nap card dien thoai viettel 100k", 3),
    ("thanh toan hoa don dien nuoc thang 5", 3),
    ("cuoc dien thoai tra sau mobifone", 3),
    ("gia han goi cuoc 4g viettel telecom", 3),
    ("tien dien sinh hoat evn thang 4", 3),
    ("dong tien wifi internet vnpt thang 6", 3),

    # 4: Xăng xe & Đi lại (20 mẫu)
    ("GRAB VIETNAM cuoc xe grabbike di lam", 4),
    ("do xang petrolimex xe may", 4),
    ("tien do xang ron95 cay xang pvoil", 4),
    ("dat xe xanh sm taxi di san bay", 4),
    ("be bike cuoc xe ve nha", 4),
    ("ve xe buyt thang sinh vien", 4),
    ("gui xe thang chung cu bai do xe", 4),
    ("thay dau nhot sua xe may honda", 4),
    ("mua ve tau xe khach ve que", 4),
    ("grabcar di cong tac quan 1", 4),
    ("phi cau duong etc vetc epass", 4),
    ("bom lop rua xe thay sam xe may", 4),
    ("thanh toan cuoc grab di lam sang", 4),
    ("do xang xe may cay xang petrolimex", 4),
    ("ck tien gui xe may hang thang", 4),
    ("dat xe om cong nghe grab bike", 4),
    ("sua xe thay nhot phanh xe may", 4),
    ("di taxi mai linh xanh sm ve nha", 4),
    ("mua ve xe khach phuong trang ve que", 4),
    ("nap tien the giao thong etc qua tram", 4),

    # 5: Chăm sóc sức khỏe & Y tế (20 mẫu)
    ("nha thuoc long chau mua thuoc cam cum", 5),
    ("mua vitamin c khau trang pharmacity", 5),
    ("Thu phi gia han BH Goi Mat tien MB", 5),
    ("kham benh tong quat benh vien bach mai", 5),
    ("thanh toan vien phi xet nghiem mau", 5),
    ("mua thuoc tay hieu thuoc an khang", 5),
    ("dong bao hiem y te bao hiem nhan tho", 5),
    ("nho rang kham nha khoa lay cao rang", 5),
    ("mua thuc pham chuc nang dau ca omega", 5),
    ("kham mat cat kinh can thi benh vien mat", 5),
    ("phi tap gym california yoga thang", 5),
    ("mua thuoc dau dau ha sot panadol", 5),
    ("thanh toan tien thuoc tai long chau", 5),
    ("kham suc khoe dinh ky phong kham da khoa", 5),
    ("dong phi bao hiem suc khoe hang nam", 5),
    ("mua thuoc ho siro cam tai pharmacity", 5),
    ("thanh toan chi phi kham rang nha khoa", 5),
    ("mua bang gac cồn y te nha thuoc", 5),
    ("vien phi kham tai mui hong benh vien", 5),
    ("gia han goi the tap gym thang nay", 5),

    # 6: Mua sắm & Đồ dùng (20 mẫu)
    ("SHOPEEPAY thanh toan don hang shopee", 6),
    ("LAZADA VIETNAM don hang gia dung", 6),
    ("mua quan ao giay dep uniqlo zara", 6),
    ("tiki mua sach va do dung hoc tap", 6),
    ("tiktok shop thanh toan don hang my pham", 6),
    ("mua ban phim chuot may tinh gearvn", 6),
    ("dien may xanh mua noi chien khong dau", 6),
    ("mua ao khoac quan jean shop thoi trang", 6),
    ("cellphones mua op lung cap sac dien thoai", 6),
    ("mua do gia dung binh giu nhiet lock lock", 6),
    ("mua sua rua mat kem chong nang hasaki", 6),
    ("order don hang shopee phu kien ban hoc", 6),
    ("thanh toan don hang lazada do dung nha bep", 6),
    ("mua giay the thao nike adidas mall", 6),
    ("ck mua ao so mi quan tay di lam", 6),
    ("mua tai nghe bluetooth phu kien dien tu", 6),
    ("dat hang shopee my pham dau goi sua tam", 6),
    ("mua tui xach balo laptop tren tiki", 6),
    ("thanh toan mua sam do gia dung dien may", 6),
    ("order quan ao tiktok shop don hang moi", 6),

    # 7: Giải trí & Phim ảnh (20 mẫu)
    ("CGV CINEMAS dat ve xem phim cuoi tuan", 7),
    ("MOMO CGV bap nuoc xem phim", 7),
    ("gia han goi netflix spotify premium", 7),
    ("lotte cinema ve xem phim 2d", 7),
    ("nap the game steam valorant garena", 7),
    ("youtube premium dang ky goi thang", 7),
    ("mua ve ca nhac live show concert", 7),
    ("choi bida bowling giai tri cuoi tuan", 7),
    ("galaxy cinema dat ve xem phim toi", 7),
    ("mua truyen tranh sach giai tri cuoi tuan", 7),
    ("thue san cau long bong da giai tri", 7),
    ("dang ky goi fpt play xem bong da", 7),
    ("mua ve xem phim rap beta cgv", 7),
    ("thanh toan goi spotify nghe nhac thang", 7),
    ("nap game lien minh garena giai tri", 7),
    ("dat ve phim chieu rap lotte cinema", 7),
    ("gia han tai khoan netflix xem phim", 7),
    ("choi game net bida giai tri buoi toi", 7),
    ("mua ve khu vui choi cong vien giai tri", 7),
    ("thanh toan goi youtube premium hang thang", 7),

    # 8: Gặp gỡ bạn bè & Tiệc tùng (20 mẫu)
    ("MBVCB.91234.Lien hoan an lau cuoi tuan", 8),
    ("camp tien lau nuong cung nhom ban", 8),
    ("uong bia giao luu dong nghiep cty", 8),
    ("thanh toan bill tiec sinh nhat nha hang", 8),
    ("mung cuoi ban than phong bi dam cuoi", 8),
    ("chia tien nhau toi thu sau quan bia", 8),
    ("hop lop dai hoc an buffet hai san", 8),
    ("mua qua sinh nhat tang ban than", 8),
    ("share tien an nuong gogi kichi kichi", 8),
    ("di karaoke nhau nhet cung team du an", 8),
    ("mung tan gia nha moi ban cap 3", 8),
    ("lien hoan tat nien cuoi nam phong ban", 8),
    ("ck share bill an lau nuong nhom ban", 8),
    ("chia tien tiec sinh nhat ban trong lop", 8),
    ("di nhau quan bia hoi voi dong nghiep", 8),
    ("mung dam cuoi phong bi ban dai hoc", 8),
    ("hop mat ban be cuoi tuan an buffet", 8),
    ("lien hoan chia tay dong nghiep nha hang", 8),
    ("camp tien karaoke tiec mung du an", 8),
    ("share tien bia ruou tiec sinh nhat", 8),

    # 10: Quỹ tiết kiệm dự phòng (18 mẫu)
    ("MB trich gui tiet kiem online ky han 6 thang", 10),
    ("gui tiet kiem tich luy du phong", 10),
    ("chuyen tien vao quy khan cap tiet kiem", 10),
    ("mo so tiet kiem online vietcombank", 10),
    ("gui gop heo dat tiet kiem thang nay", 10),
    ("nap tien so tiet kiem dinh ky", 10),
    ("trich 20 phan tram luong gui tiet kiem", 10),
    ("chuyen khoan vao tai khoan tiet kiem", 10),
    ("tich luy quy du phong tai chinh ca nhan", 10),
    ("gui tiet kiem ky han 12 thang", 10),
    ("nop tien vao so tiet kiem tich luy", 10),
    ("trich luong gui tiet kiem hang thang", 10),
    ("gui tiet kiem online mb bank ky han", 10),
    ("tiet kiem quy du phong khan cap thang", 10),
    ("chuyen khoan tiet kiem dinh ky cuoi thang", 10),
    ("mo so tiet kiem tich luy 3 thang", 10),
    ("gui tiet kiem ca nhan du phong", 10),
    ("nap tien quy tiet kiem dai han", 10),

    # 12: Lương cố định hàng tháng (18 mẫu)
    ("CTY CP CONG NGHE ALPHA TRA LUONG THANG 10", 12),
    ("thanh toan luong co ban nhan vien t11", 12),
    ("cong ty chuyen khoan luong thang 9", 12),
    ("payroll salary monthly payment company", 12),
    ("chi luong va phu cap an trua t8", 12),
    ("nhan luong co dinh hang thang", 12),
    ("cty tra luong dot 2 thang 6", 12),
    ("luong thang 12 va phu cap", 12),
    ("chuyen khoan luong tu phong ke toan", 12),
    ("tam ung luong giua thang cong ty", 12),
    ("cong ty thanh toan luong nhan vien thang 5", 12),
    ("tra luong co ban thang 7 cong ty", 12),
    ("nhan tien luong thang 4 tu cty", 12),
    ("cty cp chuyen khoan chi luong thang 3", 12),
    ("thanh toan tien luong thang 8 nhan vien", 12),
    ("chuyen khoan luong cung hang thang", 12),
    ("chi tra luong ky 1 thang 11 cong ty", 12),
    ("tra luong thang 2 cong ty cong nghe", 12),

    # 13: Thưởng & Thu nhập ngoài (Freelance) (18 mẫu)
    ("VCB thanh toan du an freelance website", 13),
    ("thuong hieu suat kpi quy 3", 13),
    ("thuong le 2 9 tet duong lich", 13),
    ("khach hang chuyen tien thiet ke logo freelance", 13),
    ("thu nhap ngoai day gia su lam them", 13),
    ("hoa hong gioi thieu khach hang du an", 13),
    ("thanh toan cong tac vien viet bai seo", 13),
    ("thuong du an hoan thanh dung tien do", 13),
    ("ban do cu thanh ly ban phim nhan tien", 13),
    ("chuyen khoan tien lam them part time", 13),
    ("nhan tien thanh toan job freelance code", 13),
    ("thuong nong kpi thang 10 xuat sac", 13),
    ("thu nhap freelance thiet ke web khach hang", 13),
    ("tien thuong quy va hoa hong du an", 13),
    ("khach ck thanh toan hop dong freelance", 13),
    ("thu lao cong tac vien lam them ngoai gio", 13),
    ("thuong tet am lich thang luong 13", 13),
    ("nhan hoa hong ban hang tu khach", 13),

    # 14: Lãi tiền gửi & Cổ tức (16 mẫu)
    ("Tra lai tien gui so TK 028205890000", 14),
    ("nhan lai suat tiet kiem ky han 6 thang", 14),
    ("chia co tuc tien mat chung khoan vnm", 14),
    ("lai nhap goc tai khoan thanh toan", 14),
    ("thanh toan lai trai phieu dinh ky", 14),
    ("tien lai tiet kiem khong ky han", 14),
    ("tra lai tien gui ngan hang cuoi thang", 14),
    ("nhan co tuc co phieu fpt", 14),
    ("tra lai suat tien gui khong ky han", 14),
    ("thanh toan co tuc bang tien mat", 14),
    ("lai tien gui thanh toan hang thang", 14),
    ("nhan tien lai so tiet kiem dao han", 14),
    ("chi tra co tuc chung khoan vcb", 14),
    ("tra lai dinh ky tien gui ngan hang", 14),
    ("lai suat nhap goc so tiet kiem", 14),
    ("nhan lai trai phieu va co tuc", 14),

    # 15: Chuyển tiền nội bộ giữa các ví (18 mẫu)
    ("CUSTOMER MOMO CASHIN 0977294663 bank2wallet", 15),
    ("AP CASHIN shopeepay bank2wallet", 15),
    ("VCB nap tien vao vi momo ca nhan", 15),
    ("rut tien tu vi zalopay ve ngan hang", 15),
    ("chuyen tien noi bo tu mbbank sang vcb", 15),
    ("nap tien vi dien tu shopeepay", 15),
    ("chuyen khoan giua hai tai khoan ca nhan", 15),
    ("nap vi momo tu the lien ket", 15),
    ("rut tien vi momo ve tai khoan techcombank", 15),
    ("chuyen tien noi bo sang the tin dung", 15),
    ("nap tien tu ngan hang vao vi zalopay", 15),
    ("ck noi bo giua hai tai khoan cua toi", 15),
    ("rut tien tu vi shopeepay ve mb bank", 15),
    ("momo cashin nap vi dien tu tu vcb", 15),
    ("chuyen tien qua lai giua cac vi ca nhan", 15),
    ("nap tien vao vi dien tu momo", 15),
    ("ck noi bo tu vcb sang tai khoan mb", 15),
    ("rut vi dien tu ve tai khoan ngan hang", 15),
]


def build_training_dataset(include_db: bool = True) -> Tuple[List[str], List[int]]:
    """Kết hợp tập dữ liệu chuẩn hóa tiếng Việt với dữ liệu thực tế đã gắn nhãn trong PostgreSQL."""
    texts: List[str] = []
    labels: List[int] = []

    for raw_text, cat_id in CURATED_VN_DATASET:
        texts.append(preprocess_banking_text(raw_text))
        labels.append(cat_id)

    if include_db:
        try:
            from sqlalchemy import text
            from api.dependencies import get_db_session

            with get_db_session() as db:
                rows = db.execute(
                    text("""
                        SELECT raw_description, clean_description, category_id
                        FROM fact_transactions
                        WHERE raw_description IS NOT NULL AND category_id IS NOT NULL
                    """)
                ).fetchall()
                for raw_d, clean_d, cat_id in rows:
                    proc = preprocess_banking_text(f"{raw_d} {clean_d or ''}")
                    if proc and int(cat_id) in CATEGORY_NAMES:
                        texts.append(proc)
                        labels.append(int(cat_id))
        except Exception:
            pass

    return texts, labels


def build_pipeline() -> Pipeline:
    """Pipeline NLP kết hợp Word N-gram và Character-WB N-gram TF-IDF + LogisticRegression."""
    features = FeatureUnion(
        [
            (
                "word_tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    min_df=1,
                    max_features=6000,
                    sublinear_tf=True,
                ),
            ),
            (
                "char_tfidf",
                TfidfVectorizer(
                    analyzer="char_wb",
                    ngram_range=(3, 5),
                    min_df=1,
                    max_features=12000,
                    sublinear_tf=True,
                ),
            ),
        ]
    )
    base_svc = LinearSVC(
        C=1.2,
        class_weight="balanced",
        random_state=42,
    )
    clf = CalibratedClassifierCV(base_svc, cv=3, method="sigmoid")
    return Pipeline([("features", features), ("clf", clf)])


def train_and_evaluate_classifier(save_model: bool = True, include_db: bool = True) -> Dict[str, Any]:
    """Huấn luyện, đánh giá trên tập kiểm thử (Holdout + Cross-Validation) và lưu model + báo cáo."""
    # 1. Đánh giá khắt khe trên tập dữ liệu tiếng Việt không dấu/viết tắt độc lập (Curated Holdout 20%)
    curated_texts = [preprocess_banking_text(t) for t, _ in CURATED_VN_DATASET]
    curated_labels = [c for _, c in CURATED_VN_DATASET]

    X_tr_c, X_te_c, y_tr_c, y_te_c = train_test_split(
        curated_texts, curated_labels, test_size=0.20, random_state=42, stratify=curated_labels
    )
    curated_pipe = build_pipeline()
    curated_pipe.fit(X_tr_c, y_tr_c)
    y_pred_c = curated_pipe.predict(X_te_c)

    curated_acc = round(float(accuracy_score(y_te_c, y_pred_c)), 4)
    curated_f1_weighted = round(float(f1_score(y_te_c, y_pred_c, average="weighted", zero_division=0)), 4)

    # 2. Huấn luyện & đánh giá trên toàn bộ dữ liệu kết hợp (Curated + DB)
    all_texts, all_labels = build_training_dataset(include_db=include_db)

    counts = {}
    for lbl in all_labels:
        counts[lbl] = counts.get(lbl, 0) + 1
    valid_indices = [i for i, lbl in enumerate(all_labels) if counts[lbl] >= 4]
    X_all = [all_texts[i] for i in valid_indices]
    y_all = [all_labels[i] for i in valid_indices]

    X_train, X_test, y_train, y_test = train_test_split(
        X_all, y_all, test_size=0.20, random_state=42, stratify=y_all
    )

    eval_pipe = build_pipeline()
    eval_pipe.fit(X_train, y_train)
    y_pred = eval_pipe.predict(X_test)

    accuracy = round(float(accuracy_score(y_test, y_pred)), 4)
    f1_weighted = round(float(f1_score(y_test, y_pred, average="weighted", zero_division=0)), 4)
    f1_macro = round(float(f1_score(y_test, y_pred, average="macro", zero_division=0)), 4)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(build_pipeline(), X_all, y_all, cv=cv, scoring="f1_weighted")

    unique_labels = sorted(list(set(y_test) | set(y_pred)))
    label_names = [CATEGORY_NAMES.get(c, str(c)) for c in unique_labels]
    cm = confusion_matrix(y_test, y_pred, labels=unique_labels).tolist()
    cls_report = classification_report(
        y_test, y_pred, labels=unique_labels, target_names=label_names, output_dict=True, zero_division=0
    )

    # 3. Huấn luyện mô hình final trên 100% tập dữ liệu để phục vụ suy luận (Inference)
    final_pipe = build_pipeline()
    final_pipe.fit(X_all, y_all)

    eval_summary = {
        "model_type": "Hybrid Rule-Based + TF-IDF (Word 1-2 & Char 3-5) + Calibrated LinearSVC",
        "trained_at": datetime.now().isoformat(),
        "total_samples": len(X_all),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "num_classes": len(unique_labels),
        "metrics": {
            "accuracy": accuracy,
            "f1_weighted": f1_weighted,
            "f1_macro": f1_macro,
            "cv5_f1_mean": round(float(np.mean(cv_scores)), 4),
            "cv5_f1_std": round(float(np.std(cv_scores)), 4),
            "curated_unseen_accuracy": curated_acc,
            "curated_unseen_f1_weighted": curated_f1_weighted,
        },
        "kpi_target_f1": 0.85,
        "kpi_passed": f1_weighted >= 0.85 and curated_f1_weighted >= 0.85,
        "class_labels": [{"category_id": int(c), "category_name": CATEGORY_NAMES.get(int(c), str(c))} for c in unique_labels],
        "confusion_matrix": cm,
        "classification_report": cls_report,
    }

    if save_model:
        os.makedirs(MODEL_DIR, exist_ok=True)
        joblib.dump(final_pipe, MODEL_PATH)
        with open(EVAL_PATH, "w", encoding="utf-8") as f:
            json.dump(eval_summary, f, ensure_ascii=False, indent=2)

    return eval_summary


if __name__ == "__main__":
    res = train_and_evaluate_classifier(save_model=True, include_db=True)
    print(json.dumps({k: v for k, v in res.items() if k not in ("confusion_matrix", "classification_report")}, ensure_ascii=False, indent=2))
