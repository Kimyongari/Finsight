import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0", // [핵심] 외부 접속 허용 (이게 없으면 localhost로만 뜸)
    port: 5173,      // 포트 고정
    strictPort: true, // 포트 충돌 시 에러 발생 (자동으로 5174로 넘어가지 않음)
  },
});