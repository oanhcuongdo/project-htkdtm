from datetime import datetime
from typing import Optional, Tuple
from rapidfuzz.distance import JaroWinkler
from sqlalchemy import text
from sqlalchemy.orm import Session


class DeduplicationEngine:
    """
    Động cơ khử trùng lặp đa nguồn theo đúng đặc tả Đề cương:
    1. Quy tắc 1 (EXACT_REF_CODE): Trùng mã tham chiếu ngân hàng trên cùng tài khoản.
    2. Quy tắc 2 (FUZZY_TIME_AMOUNT_NAME): Cùng tài khoản, bằng số tiền, chênh lệch thời gian <= 10 phút,
       và độ tương đồng nội dung / đối tác >= 0.8 theo Jaro-Winkler.
    """

    SIMILARITY_THRESHOLD = 0.80
    TIME_WINDOW_MINUTES = 10

    @classmethod
    def check_duplicate(
        cls,
        db: Session,
        account_id: int,
        amount: float,
        tx_time: datetime,
        reference_code: Optional[str],
        clean_description: str,
        user_id: int = 1,
    ) -> Tuple[bool, Optional[int], Optional[str], float]:
        """
        Trả về (is_duplicate, master_transaction_id, applied_rule, similarity_score).
        """
        # 1. Quy tắc 1: Khớp chính xác theo mã tham chiếu ngân hàng (reference_code) trên cùng user
        if reference_code and reference_code.strip():
            exact_row = db.execute(
                text("""
                    SELECT transaction_id
                    FROM fact_transactions
                    WHERE user_id = :uid AND account_id = :acc_id AND reference_code = :ref_code
                    LIMIT 1
                """),
                {"uid": user_id, "acc_id": account_id, "ref_code": reference_code.strip()},
            ).first()
            if exact_row:
                return True, int(exact_row[0]), "EXACT_REF_CODE", 1.0

        # 2. Quy tắc 2: Khớp gần đúng theo (user, tài khoản, số tiền, khung thời gian +-10 phút, Jaro-Winkler >= 0.8)
        candidates = db.execute(
            text("""
                SELECT f.transaction_id, f.clean_description, f.raw_description, f.created_at, d.full_date, d.hour
                FROM fact_transactions f
                JOIN dim_date d ON f.date_id = d.date_id
                WHERE f.user_id = :uid
                  AND f.account_id = :acc_id
                  AND ABS(f.amount) = :abs_amt
                  AND d.full_date = :tx_date
                  AND ABS(d.hour - :tx_hour) <= 1
            """),
            {
                "uid": user_id,
                "acc_id": account_id,
                "abs_amt": abs(amount),
                "tx_date": tx_time.date(),
                "tx_hour": tx_time.hour,
            },
        ).fetchall()

        target_text = (clean_description or "").lower().strip()
        for cand in candidates:
            cand_id = int(cand[0])
            cand_desc = (cand[1] or cand[2] or "").lower().strip()

            # Tính điểm tương đồng Jaro-Winkler
            score = JaroWinkler.similarity(target_text, cand_desc)
            if score >= cls.SIMILARITY_THRESHOLD:
                return True, cand_id, "FUZZY_TIME_AMOUNT_NAME", round(float(score), 4)

        return False, None, None, 0.0

    @staticmethod
    def log_duplicate(
        db: Session,
        master_tx_id: int,
        applied_rule: str,
        similarity_score: float,
        reason: str,
        duplicate_record_id: int = 0,
        user_id: int = 1,
    ):
        db.execute(
            text("""
                INSERT INTO log_dedup (
                    user_id, master_transaction_id, duplicate_record_id, applied_rule, similarity_score, reason
                ) VALUES (
                    :uid, :master_id, :dup_id, :rule, :score, :reason
                )
            """),
            {
                "uid": user_id,
                "master_id": master_tx_id,
                "dup_id": duplicate_record_id,
                "rule": applied_rule,
                "score": similarity_score,
                "reason": reason,
            },
        )
