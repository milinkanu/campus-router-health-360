/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          bg: "#0B0F17",
          card: "#151C28",
          border: "#1E293B",
          hover: "#1E293B",
        }
      }
    },
  },
  plugins: [],
}
