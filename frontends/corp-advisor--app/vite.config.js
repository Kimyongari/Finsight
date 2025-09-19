import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173, // 원하는 포트 지정
    strictPort: true, // true면 포트 사용 불가 시 서버 실행 실패
  },
});
