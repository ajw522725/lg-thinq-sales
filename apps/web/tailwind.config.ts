import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#f7f9ff",
        surface: "#ffffff",
        "surface-low": "#f1f4f9",
        "surface-container": "#ebeef3",
        "surface-high": "#e5e8ee",
        primary: "#7a0024",
        "primary-strong": "#a50034",
        secondary: "#5a5e6a",
        charcoal: "#181c20",
        error: "#ba1a1a"
      },
      boxShadow: {
        soft: "0 8px 32px rgba(0,0,0,0.04)"
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"]
      }
    }
  },
  plugins: []
};

export default config;
