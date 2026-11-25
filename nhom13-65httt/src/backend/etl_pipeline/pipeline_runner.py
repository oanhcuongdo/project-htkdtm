import time
from datetime import datetime
from typing import List
from sqlalchemy import text

from api.dependencies import get_db_session
from ingestion.models import RawTransactionDTO
from .cleaner import DataCleaner
from .normalizer import DataNormalizer
from .deduplicator import DeduplicationEngine
from .data_quality import DataQualityChecker


class ETLPipelineRunner:
    """Điều phối luồng ETL toàn trình: Clean -> Normalize -> Deduplicate -> Load -> Audit."""

    def run(self, dtos: List[RawTransactionDTO], pipeline_name: str = "ETL_Batch_Pipeline", user_id: int = 1) -> dict:
        started_at = datetime.now()
        t0 = time.time()

        inserted_count = 0
        deduplicated_count = 0
        failed_count = 0

        with get_db_session() as db:
            for dto in dtos:
                try:
                    effective_uid = user_id or dto.user_id or 1
                    vn_dt = DataNormalizer.to_vn_datetime(dto.transaction_time)
                    date_id = DataNormalizer.ensure_dim_date(db, vn_dt)
                    account_id = DataNormalizer.resolve_account_id(
                        db, dto.bank_name, dto.account_number_mask, user_id=effective_uid
                    )

                    is_internal = DataCleaner.is_internal_transfer(dto.raw_description, dto.counterparty_name)
                    clean_desc = DataCleaner.clean_description(dto.raw_description, dto.counterparty_name)
                    norm_amount, norm_dir = DataNormalizer.normalize_amount_and_direction(
                        dto.amount, dto.direction, is_internal
                    )
                    cat_id, merch_id = DataCleaner.infer_category_and_merchant(
                        dto.raw_description, dto.counterparty_name, norm_dir, is_internal
                    )

                    # Tích hợp mô hình AI NLP phân loại ngữ cảnh tiếng Việt cho các giao dịch chưa rõ danh mục
                    if not is_internal and merch_id is None:
                        try:
                            from ai_service.category_classifier import get_classifier
                            ai_pred = get_classifier().predict(
                                raw_description=dto.raw_description,
                                counterparty=dto.counterparty_name or "",
                                direction=norm_dir,
                            )
                            if ai_pred.get("confidence", 0.0) >= 0.55:
                                cat_id = int(ai_pred["category_id"])
                        except Exception:
                            pass

                    # Kiểm tra khử trùng lặp
                    is_dup, master_id, rule, sim_score = DeduplicationEngine.check_duplicate(
                        db=db,
                        account_id=account_id,
                        amount=norm_amount,
                        tx_time=vn_dt,
                        reference_code=dto.reference_code,
                        clean_description=clean_desc,
                        user_id=effective_uid,
                    )

                    if is_dup and master_id:
                        DeduplicationEngine.log_duplicate(
                            db=db,
                            master_tx_id=master_id,
                            applied_rule=rule or "EXACT_REF_CODE",
                            similarity_score=sim_score,
                            reason=f"Bỏ qua bản ghi trùng nguồn {dto.source_type} (Ref: {dto.reference_code}, ND: {clean_desc[:80]})",
                            user_id=effective_uid,
                        )
                        deduplicated_count += 1
                        continue

                    db.execute(
                        text("""
                            INSERT INTO fact_transactions (
                                user_id, date_id, category_id, account_id, merchant_id, amount, direction,
                                raw_description, clean_description, counterparty_name,
                                counterparty_account_mask, counterparty_bank, is_internal_transfer,
                                is_anomaly, anomaly_score, reference_code, source_type, created_at
                            ) VALUES (
                                :uid, :date_id, :cat_id, :acc_id, :merch_id, :amount, :direction,
                                :raw_desc, :clean_desc, :cp_name,
                                :cp_acc, :cp_bank, :is_internal,
                                FALSE, 0.0, :ref_code, :source_type, :created_at
                            )
                        """),
                        {
                            "uid": effective_uid,
                            "date_id": date_id,
                            "cat_id": cat_id,
                            "acc_id": account_id,
                            "merch_id": merch_id,
                            "amount": norm_amount,
                            "direction": norm_dir,
                            "raw_desc": DataCleaner.normalize_unicode(dto.raw_description),
                            "clean_desc": clean_desc,
                            "cp_name": DataCleaner.normalize_unicode(dto.counterparty_name or "") or None,
                            "cp_acc": dto.counterparty_account_mask,
                            "cp_bank": dto.counterparty_bank,
                            "is_internal": is_internal,
                            "ref_code": dto.reference_code,
                            "source_type": dto.source_type,
                            "created_at": vn_dt,
                        },
                    )
                    inserted_count += 1
                except Exception as exc:
                    failed_count += 1
                    print(f"[ETL ERROR] Lỗi xử lý bản ghi '{dto.raw_description}': {exc}")

            duration = round(time.time() - t0, 2)
            status = "SUCCESS" if failed_count == 0 else ("PARTIAL" if inserted_count > 0 else "FAILED")

            db.execute(
                text("""
                    INSERT INTO pipeline_execution_logs (
                        pipeline_name, status, records_processed, records_failed,
                        duration_seconds, started_at, finished_at
                    ) VALUES (
                        :pname, :status, :proc, :fail, :dur, :start_at, :end_at
                    )
                """),
                {
                    "pname": pipeline_name,
                    "status": status,
                    "proc": inserted_count + deduplicated_count,
                    "fail": failed_count,
                    "dur": duration,
                    "start_at": started_at,
                    "end_at": datetime.now(),
                },
            )

            dq_report = DataQualityChecker.run_all_checks(db)

        return {
            "pipeline_name": pipeline_name,
            "status": status,
            "total_input": len(dtos),
            "inserted": inserted_count,
            "deduplicated": deduplicated_count,
            "failed": failed_count,
            "duration_seconds": duration,
            "data_quality_passed": dq_report["all_passed"],
        }
