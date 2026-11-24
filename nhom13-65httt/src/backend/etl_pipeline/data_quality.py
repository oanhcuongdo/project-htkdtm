from sqlalchemy import text
from sqlalchemy.orm import Session


class DataQualityChecker:
    """
    Thực thi 5 luật kiểm thử chất lượng dữ liệu tự động (Data Quality Gate)
    theo đúng tiêu chí đánh giá trong Đề cương (>= 5 luật, 100% đạt).
    """

    @staticmethod
    def run_all_checks(db: Session) -> dict:
        checks = []

        # Luật 1: Không có khóa ngoại mồ côi (Orphan Foreign Keys)
        orphan_count = db.execute(
            text("""
                SELECT COUNT(*) FROM fact_transactions f
                LEFT JOIN dim_date d ON f.date_id = d.date_id
                LEFT JOIN dim_category c ON f.category_id = c.category_id
                LEFT JOIN dim_account a ON f.account_id = a.account_id
                WHERE d.date_id IS NULL OR c.category_id IS NULL OR a.account_id IS NULL
            """)
        ).scalar() or 0
        checks.append({
            "rule": "1_no_orphan_foreign_keys",
            "description": "100% bản ghi liên kết hợp lệ với Dim_Date, Dim_Category, Dim_Account",
            "failed_rows": int(orphan_count),
            "passed": orphan_count == 0,
        })

        # Luật 2: Nhất quán dấu số tiền theo chiều dòng tiền (INCOME > 0, EXPENSE/TRANSFER < 0)
        bad_sign_count = db.execute(
            text("""
                SELECT COUNT(*) FROM fact_transactions
                WHERE (direction = 'INCOME' AND amount <= 0)
                   OR (direction IN ('EXPENSE', 'TRANSFER') AND amount >= 0)
            """)
        ).scalar() or 0
        checks.append({
            "rule": "2_amount_sign_consistency",
            "description": "Thu nhập (INCOME) luôn dương (>0), Chi tiêu/Chuyển tiền luôn âm (<0)",
            "failed_rows": int(bad_sign_count),
            "passed": bad_sign_count == 0,
        })

        # Luật 3: Độ đầy đủ dữ liệu (Completeness >= 98%)
        total_rows = db.execute(text("SELECT COUNT(*) FROM fact_transactions")).scalar() or 0
        incomplete_rows = db.execute(
            text("""
                SELECT COUNT(*) FROM fact_transactions
                WHERE amount IS NULL OR date_id IS NULL OR account_id IS NULL
                   OR raw_description IS NULL OR TRIM(raw_description) = ''
            """)
        ).scalar() or 0
        completeness_pct = ((total_rows - incomplete_rows) * 100.0 / total_rows) if total_rows > 0 else 100.0
        checks.append({
            "rule": "3_completeness_threshold",
            "description": "Tỷ lệ bản ghi đầy đủ thông tin cốt lõi đạt >= 98%",
            "completeness_pct": round(completeness_pct, 2),
            "failed_rows": int(incomplete_rows),
            "passed": completeness_pct >= 98.0,
        })

        # Luật 4: Không trùng lặp khóa nghiệp vụ (reference_code trên cùng account_id)
        dup_ref_count = db.execute(
            text("""
                SELECT COUNT(*) FROM (
                    SELECT account_id, reference_code
                    FROM fact_transactions
                    WHERE reference_code IS NOT NULL AND TRIM(reference_code) != ''
                    GROUP BY account_id, reference_code
                    HAVING COUNT(*) > 1
                ) dup
            """)
        ).scalar() or 0
        checks.append({
            "rule": "4_unique_reference_codes",
            "description": "Không tồn tại mã tham chiếu ngân hàng trùng lặp trên cùng tài khoản",
            "failed_rows": int(dup_ref_count),
            "passed": dup_ref_count == 0,
        })

        # Luật 5: Kênh thu thập và chiều giao dịch hợp lệ
        invalid_enum_count = db.execute(
            text("""
                SELECT COUNT(*) FROM fact_transactions
                WHERE source_type NOT IN ('EMAIL', 'CSV', 'PDF', 'TELEGRAM', 'MANUAL')
                   OR direction NOT IN ('INCOME', 'EXPENSE', 'TRANSFER')
            """)
        ).scalar() or 0
        checks.append({
            "rule": "5_valid_source_and_direction",
            "description": "100% nguồn thu thập và chiều giao dịch thuộc tập giá trị hợp lệ",
            "failed_rows": int(invalid_enum_count),
            "passed": invalid_enum_count == 0,
        })

        passed_count = sum(1 for c in checks if c["passed"])
        return {
            "total_transactions": int(total_rows),
            "total_rules": len(checks),
            "passed_rules": passed_count,
            "all_passed": passed_count == len(checks),
            "checks": checks,
        }
