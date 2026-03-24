import type { Config } from 'tailwindcss'

export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#0F172A',
        surface: '#1E293B',
        'surface-light': '#334155',
        accent: '#3B82F6',
        'accent-hover': '#2563EB',
        success: '#10B981',
        warning: '#F59E0B',
        danger: '#EF4444',
        muted: '#64748B',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
} satisfies Config
