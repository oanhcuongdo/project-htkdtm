import React from 'react'

const HEADER_LABELS = {
  recipient_name: 'Đối tác nhận tiền',
  sender_name: 'Nguồn gửi tiền',
  account_mask: 'Số tài khoản',
  bank_name: 'Ngân hàng',
  transfer_count: 'Số lần',
  total_amount_vnd: 'Tổng tiền (VND)',
  total_received_vnd: 'Tổng nhận (VND)',
  category_name: 'Danh mục',
  parent_category: 'Nhóm',
  monthly_budget_vnd: 'Ngân sách (VND)',
  actual_spent_vnd: 'Thực chi (VND)',
  over_budget_pct: 'Vượt trần (%)',
  month_label: 'Tháng',
  total_income_vnd: 'Thu nhập (VND)',
  total_expense_vnd: 'Chi tiêu (VND)',
  net_savings_vnd: 'Tiết kiệm (VND)',
  net_savings_rate_pct: 'Tỷ lệ TK (%)',
  date: 'Ngày',
  amount_vnd: 'Số tiền (VND)',
  counterparty_name: 'Đối tác',
  description: 'Nội dung',
  anomaly_score: 'Điểm AI',
  tx_count: 'Số GD',
  direction: 'Chiều',
}

function formatCell(key, val) {
  if (val === null || val === undefined || val === '') return '—'
  if (typeof val === 'number') {
    if (key.includes('vnd') || key.includes('amount')) {
      return val.toLocaleString('vi-VN') + ' đ'
    }
    if (key.includes('pct')) {
      return val.toFixed(1) + '%'
    }
    return val.toLocaleString('vi-VN')
  }
  return String(val)
}

export default function DataTablePreview({ tables }) {
  if (!tables || tables.length === 0) return null

  return (
    <div className="mt-3 space-y-3">
      {tables.map((tbl, idx) => {
        if (!tbl.rows || tbl.rows.length === 0) return null
        const cols = Object.keys(tbl.rows[0])
        return (
          <div key={idx} className="rounded-xl border border-boulder-hellamaa bg-boulder-ehakivi overflow-hidden">
            <div className="px-3.5 py-2 bg-boulder-pahkla border-b border-boulder-hellamaa text-xs font-semibold text-boulder-mustkivi">
              {tbl.title || 'Bảng dữ liệu đối chiếu từ PostgreSQL'}
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-xs">
                <thead className="bg-boulder-pahkla/60 text-boulder-majakivi">
                  <tr>
                    {cols.map((col) => (
                      <th key={col} className="px-3 py-2 text-left font-semibold whitespace-nowrap">
                        {HEADER_LABELS[col] || col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-boulder-pahkla">
                  {tbl.rows.map((row, rIdx) => (
                    <tr key={rIdx} className="hover:bg-estonia-parnu/25 transition-colors">
                      {cols.map((col) => (
                        <td
                          key={col}
                          className={`px-3 py-2 whitespace-nowrap ${
                            col.includes('vnd') || col.includes('amount')
                              ? 'font-semibold text-estonia-blue tabular-nums-vnd'
                              : col.includes('mask') || col === 'date'
                              ? 'font-mono text-boulder-majakivi'
                              : 'text-boulder-mustkivi'
                          }`}
                        >
                          {formatCell(col, row[col])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )
      })}
    </div>
  )
}
