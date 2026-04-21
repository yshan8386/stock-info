import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#f7f8f4",
        panel: "#ffffff",
        line: "#dce2da",
        text: "#15201b",
        muted: "#65736b",
        accent: "#0f8a65",
        accentSoft: "#e5f5ed",
        info: "#256fb6",
        infoSoft: "#e7f0fb",
        warn: "#9a6500",
        warnSoft: "#fff3d8",
        coral: "#b84f45",
        coralSoft: "#fdecea"
      },
      fontFamily: {
        sans: ["Pretendard", "Inter", "system-ui", "sans-serif"]
      }
    }
  },
  plugins: []
};

export default config;
