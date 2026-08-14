import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        sidebar: {
          DEFAULT: '#f9fafb',
          dark: '#171717',
        },
        chat: {
          DEFAULT: '#ffffff',
          dark: '#212121',
        },
        user: {
          bubble: '#f3f4f6',
          'bubble-dark': '#2f2f2f',
        },
        assistant: {
          bubble: '#ffffff',
          'bubble-dark': '#212121',
        },
        border: {
          light: '#e5e7eb',
          dark: '#3f3f3f',
        },
      },
    },
  },
  plugins: [],
};

export default config;
