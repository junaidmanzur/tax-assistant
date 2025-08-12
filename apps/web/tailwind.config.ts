import type { Config } from 'tailwindcss';

export default {
  content: [
    './index.html',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        bg: '#0b0c10',
        panel: '#111218',
        muted: '#8a8f98',
        text: '#e9eaee',
        accent: '#4da3ff',
        border: '#23242b',
        chip: '#1b1d25',
      },
      borderRadius: {
        xl: '14px',
      },
      gridTemplateRows: {
        chat: '1fr auto',
      },
    },
  },
  plugins: [],
} satisfies Config;