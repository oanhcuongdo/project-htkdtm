from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class RawTransactionDTO:
    """Cấu trúc dữ liệu trung gian thống nhất từ mọi kênh thu thập trước khi vào ETL."""
    bank_name: str
    transaction_time: datetime
    amount: float  # Dương (>0) là tiền vào, Âm (<0) là tiền ra
    direction: str  # 'INCOME' | 'EXPENSE' | 'TRANSFER'
    raw_description: str
    source_type: str  # 'EMAIL' | 'CSV' | 'PDF' | 'TELEGRAM'
    account_number_mask: Optional[str] = None
    counterparty_name: Optional[str] = None
    reference_code: Optional[str] = None
    raw_metadata: Dict[str, Any] = field(default_factory=dict)
