import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#111414",
        panel: "#181c1c",
        line: "#293130",
        text: "#f2f5f3",
        muted: "#9aa6a2",
        accent: "#31c48d",
        cyan: "#22d3ee"
      },
      fontFamily: {
        sans: ["Pretendard", "Inter", "system-ui", "sans-serif"]
      }
    }
  },
  plugins: []
};

export default config;

