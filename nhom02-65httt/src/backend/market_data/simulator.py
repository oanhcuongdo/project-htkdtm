from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

@dataclass
class SimulationResult:
    sku: str
    channel: str
    current_price_vnd: float
    proposed_price_vnd: float
    pmin_vnd: float
    status: str
    reason: str
    simulated_at: str

def simulate_price_update(sku: str, channel: str, current_price_vnd: float,
                          proposed_price_vnd: float, pmin_vnd: float) -> dict:
    """Dry-run only: validates pricing guardrails and never calls marketplace APIs."""
    current, proposed, floor = map(float, (current_price_vnd, proposed_price_vnd, pmin_vnd))
    if min(current, proposed, floor) < 0 or current <= 0 or floor <= 0:
        raise ValueError("Giá hiện tại và Pmin phải > 0; giá đề xuất không được âm")
    if proposed < floor:
        status, reason, safe_price = "BLOCKED_BELOW_PMIN", "Giá đề xuất thấp hơn giá sàn Pmin", proposed
    else:
        status, reason, safe_price = "SIMULATED", "Đạt kiểm tra Pmin; chưa gửi lên sàn thật", proposed
    return asdict(SimulationResult(
        sku=sku, channel=channel, current_price_vnd=current,
        proposed_price_vnd=safe_price, pmin_vnd=floor, status=status,
        reason=reason, simulated_at=datetime.now(timezone.utc).isoformat()
    ))
