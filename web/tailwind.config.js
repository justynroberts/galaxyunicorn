/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Space Grotesk', 'system-ui', 'sans-serif'],
        mono: ['Spline Sans Mono', 'monospace'],
      },
      colors: {
        surface: {
          900: '#0a0a0a',
          800: '#141414',
          700: '#1e1e1e',
          600: '#282828',
          500: '#333333',
        },
      },
    },
  },
  plugins: [],
}
