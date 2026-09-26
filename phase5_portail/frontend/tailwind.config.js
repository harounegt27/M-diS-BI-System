/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        tekup: "#1E2A6E",
        medis: "#2B7CC2",
      },
    },
  },
  plugins: [],
}