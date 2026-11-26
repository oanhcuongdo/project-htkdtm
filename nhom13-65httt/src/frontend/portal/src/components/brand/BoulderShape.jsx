import React from 'react'

/**
 * 3 hình khối Đá tảng (Rändrahnud / Boulders) lấy cảm hứng trực tiếp từ Brand Estonia:
 * hữu cơ, hơi bất đối xứng nhưng vững chãi, dùng làm khung đỡ thị giác.
 */
const BOULDER_PATHS = {
  kupukivi:
    'M68.2 38.4C115.6 8.2 198.4 4.1 262.1 24.7C331.4 47.1 384.6 105.8 389.2 178.4C393.9 253.6 348.2 332.9 275.4 358.7C200.6 385.1 106.4 373.5 52.3 316.2C-2.5 258.2 -11.4 170.5 14.8 104.2C26.9 73.6 44.3 53.6 68.2 38.4Z',
  ukukivi:
    'M54.1 56.3C104.5 12.7 194.2 -6.2 269.8 18.9C338.1 41.6 392.4 103.5 391.2 174.8C390.1 246.2 334.7 308.4 264.9 338.6C188.4 371.7 95.8 377.4 42.6 322.1C-11.2 266.2 -7.4 173.8 18.2 106.5C27.1 83.2 39.2 69.2 54.1 56.3Z',
  silmakivi:
    'M82.4 22.8C152.9 -4.8 242.5 3.6 306.8 48.2C368.2 90.8 403.5 168.4 384.7 238.9C366.1 308.8 294.2 356.1 217.6 368.4C139.2 381.0 54.6 355.2 18.9 289.5C-16.4 224.5 1.8 134.8 40.2 74.1C52.1 55.3 66.2 29.2 82.4 22.8Z',
}

export default function BoulderShape({
  variant = 'kupukivi',
  fill = '#CEE2FD',
  className = '',
  opacity = 1,
}) {
  const pathD = BOULDER_PATHS[variant] || BOULDER_PATHS.kupukivi
  return (
    <svg
      viewBox="0 0 400 380"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      <path d={pathD} fill={fill} fillOpacity={opacity} />
    </svg>
  )
}
