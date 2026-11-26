/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        estonia: {
          blue: '#0030DE',      // Main Digital Blue
          paldiski: '#0062F5',  // Interactive Hover Blue
          liivi: '#000087',     // Deep Navy Dark Section
          parnu: '#CEE2FD',     // Soft Sky Surface / Pill
          narva: '#00C3FF',     // Electric Cyan Accent
          haapsalu: '#FCEEC8',  // Warm Sand Advisory Callout
        },
        boulder: {
          ehakivi: '#FFFFFF',    // Pure White Surface
          pahkla: '#F1F5F9',     // Light Neutral Canvas
          hellamaa: '#CBD5E1',   // Hairline Border / Grid Divider
          kabelikivi: '#64748B', // Muted Meta Text
          majakivi: '#3D4B5E',   // Secondary Body Ink
          mustkivi: '#0F172A',   // Primary Dark Ink & Footer
        },
      },
      fontFamily: {
        display: ['"Be Vietnam Pro"', 'system-ui', '-apple-system', 'sans-serif'],
        sans: ['"Plus Jakarta Sans"', '"Be Vietnam Pro"', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      borderRadius: {
        limestone: '1rem',       // 16px standard card
        'limestone-lg': '1.5rem', // 24px showcase banner
      },
    },
  },
  plugins: [],
}
