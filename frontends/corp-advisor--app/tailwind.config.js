export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}", // src 폴더 안의 모든 관련 파일을 감시하도록 설정
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "Pretendard Variable",
          "Pretendard",
          "-apple-system",
          "BlinkMacSystemFont",
          "system-ui",
          "Apple SD Gothic Neo",
          "Malgun Gothic",
          "sans-serif",
          // 1️⃣ 같은 키캡 이모지가 두부(tofu)로 깨지지 않도록 이모지 폰트를 명시
          "Apple Color Emoji",
          "Segoe UI Emoji",
          "Noto Color Emoji",
        ],
        mono: ["SFMono-Regular", "ui-monospace", "Menlo", "monospace"],
      },
      colors: {
        // 본문/보고서에 쓰는 잉크 계열 (파란기가 살짝 도는 중성색)
        ink: {
          50: "#f7f8fa",
          100: "#eef0f4",
          200: "#dfe3ea",
          300: "#c6ccd8",
          400: "#98a1b2",
          500: "#6b748a",
          600: "#4c5468",
          700: "#3a4154",
          800: "#252b3b",
          900: "#151a26",
        },
        brand: {
          50: "#eef2ff",
          100: "#e0e7ff",
          200: "#c7d2fe",
          300: "#a5b4fc",
          400: "#818cf8",
          500: "#6366f1",
          600: "#4f46e5",
          700: "#4338ca",
          800: "#3730a3",
          900: "#312e81",
        },
      },
      boxShadow: {
        card: "0 1px 2px rgba(21, 26, 38, 0.04), 0 8px 24px -12px rgba(21, 26, 38, 0.12)",
        lift: "0 2px 4px rgba(21, 26, 38, 0.05), 0 18px 40px -18px rgba(21, 26, 38, 0.22)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "pulse-dot": {
          "0%, 80%, 100%": { opacity: "0.25", transform: "scale(0.8)" },
          "40%": { opacity: "1", transform: "scale(1)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.28s ease-out both",
        "pulse-dot": "pulse-dot 1.2s ease-in-out infinite",
      },
    },
  },
  plugins: [
    require("@tailwindcss/typography"),
    require("tailwind-scrollbar-hide"),
  ],
};
