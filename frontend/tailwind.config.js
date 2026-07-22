/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        pavo: {
          50: '#f8f7f5',
          100: '#efede8',
          200: '#ddd9d0',
          300: '#c4bdaa',
          400: '#a99f85',
          500: '#94886b',
          600: '#7d7159',
          700: '#655b49',
          800: '#534b3e',
          900: '#474036',
        },
        cream: '#f8f7f5',
        warm: '#323431',
      },
      fontFamily: {
        sans: [
          '-apple-system', 'BlinkMacSystemFont', '"PingFang SC"',
          '"Microsoft YaHei"', '"Noto Sans SC"', 'sans-serif',
        ],
      },
    },
  },
  plugins: [],
}
