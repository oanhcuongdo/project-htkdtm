import React from 'react'

/**
 * Wordmark tối giản theo tinh thần Brand Estonia:
 * Biểu tượng khối đá tảng hữu cơ (Boulder) mini + kiểu chữ hình học sắc nét.
 */
export default function BrandWordmark({ dark = false, subtitle = '' }) {
  return (
    <div className="inline-flex items-center gap-3 select-none">
      <div className="relative w-9 h-9 flex items-center justify-center shrink-0">
        <svg viewBox="0 0 40 40" className="w-9 h-9" aria-hidden="true">
          <path
            d="M7.5 22.8C5.8 14.9 10.6 6.8 19.2 5.4C27.5 4.0 34.9 9.5 35.6 17.9C36.4 27.1 30.8 34.4 21.8 35.1C13.6 35.7 9.1 30.3 7.5 22.8Z"
            fill={dark ? '#00C3FF' : '#0030DE'}
          />
          <path
            d="M14 21.5H20.5M23.5 21.5H27.5M14 16H26"
            stroke={dark ? '#000087' : '#FFFFFF'}
            strokeWidth="2.4"
            strokeLinecap="round"
          />
        </svg>
      </div>
      <div className="leading-none">
        <span
          className={`font-display font-bold text-lg tracking-tight ${
            dark ? 'text-white' : 'text-boulder-mustkivi'
          }`}
        >
          personal
          <span className={dark ? 'text-estonia-narva' : 'text-estonia-blue'}>.cfo</span>
        </span>
        {subtitle && (
          <p className={`text-[11px] font-medium mt-1 ${dark ? 'text-estonia-parnu/80' : 'text-boulder-kabelikivi'}`}>
            {subtitle}
          </p>
        )}
      </div>
    </div>
  )
}
