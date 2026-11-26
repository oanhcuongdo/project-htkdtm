import React from 'react'

/**
 * Họa tiết Đường Nét Đứt "Làn gió" (The Broken Line) của Brand Estonia.
 * Tuân thủ nghiêm ngặt công thức nhịp hình học: Y, X, 3Y, X (với Y = 22 >= 2*X, X = 10 -> "22 10 66 10").
 */
export default function BrokenLine({
  color = '#0030DE',
  className = 'w-44 h-3',
  strokeWidth = 3,
}) {
  return (
    <svg
      viewBox="0 0 240 10"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <line
        x1="2"
        y1="5"
        x2="238"
        y2="5"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeDasharray="22 10 66 10"
      />
    </svg>
  )
}
