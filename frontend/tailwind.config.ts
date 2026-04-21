import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#f6faf8",
        panel: "#ffffff",
        line: "#dce7e2",
        text: "#17211d",
        muted: "#64736d",
        accent: "#10865f",
        accentSoft: "#e7f6f0",
        info: "#246baf",
        infoSoft: "#e8f1fb",
        warn: "#a35f00",
        warnSoft: "#fff4df"
      },
      fontFamily: {
        sans: ["Pretendard", "Inter", "system-ui", "sans-serif"]
      }
    }
  },
  plugins: []
};

export default config;
