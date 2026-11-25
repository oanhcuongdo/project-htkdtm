export function formatVND(amount) {
  if (amount === null || amount === undefined || Number.isNaN(Number(amount))) {
    return 'Thỏa thuận';
  }
  const num = Number(amount);
  if (num >= 1_000_000) {
    const tr = num / 1_000_000;
    return `${Number.isInteger(tr) ? tr : tr.toFixed(1)} triệu/tháng`;
  }
  return `${num.toLocaleString('vi-VN')} đ`;
}

export function formatExactVND(amount) {
  if (amount === null || amount === undefined || Number.isNaN(Number(amount))) {
    return 'Chưa rõ';
  }
  return `${Math.round(Number(amount)).toLocaleString('vi-VN')} đ`;
}

export function formatPricePerM2(pricePerM2) {
  if (!pricePerM2) return '—';
  return `${Math.round(Number(pricePerM2) / 1000).toLocaleString('vi-VN')}k/m²`;
}

export function getRiskMeta(riskScore = 0) {
  const score = Number(riskScore || 0);
  if (score >= 40) {
    return {
      label: 'Cần kiểm tra kỹ',
      tone: 'danger',
      bgClass: 'bg-red-50 text-[#DC2626] border-red-200',
    };
  }
  if (score >= 20) {
    return {
      label: 'Lưu ý thông tin',
      tone: 'warning',
      bgClass: 'bg-amber-50 text-[#B45309] border-amber-200',
    };
  }
  return {
    label: 'Độ tin cậy tốt',
    tone: 'safe',
    bgClass: 'bg-emerald-50 text-[#15803D] border-emerald-200',
  };
}
