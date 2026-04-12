/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        cyber: {
          50: "#e0f7ff",
          100: "#b3ecff",
          200: "#80dfff",
          300: "#4dd2ff",
          400: "#26c6ff",
          500: "#00d4ff",
          600: "#00a3cc",
          700: "#007399",
          800: "#004466",
          900: "#001a33",
        },
        glass: {
          bg: "rgba(13,17,23,0.95)",
          card: "rgba(255,255,255,0.03)",
          border: "rgba(0,212,255,0.12)",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      backdropBlur: {
        glass: "12px",
      },
    },
  },
  plugins: [],
};
