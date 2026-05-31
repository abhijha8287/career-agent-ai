import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#15201b",
        moss: "#2f5d50",
        signal: "#d45b31",
        paper: "#f7f4ee",
        line: "#d9ded8"
      }
    }
  },
  plugins: []
};

export default config;
