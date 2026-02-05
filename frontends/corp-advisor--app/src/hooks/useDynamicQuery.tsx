import { useState, useCallback } from "react";

// ✅ 수정 포인트 1: 백엔드 기본 주소 설정
// 개발 환경(Vite)에서는 환경변수(VITE_API_URL)를 우선 사용하고, 없으면 하드코딩된 IP 사용
const BASE_URL = import.meta.env.VITE_API_URL || "http://34.22.88.153:8000";

// 드롭다운에서 선택할 값들의 타입을 미리 정의하여 안정성을 높입니다.
export type QueryMode = "rag" | "advanced_rag" | "web_search";

// ✅ 수정 포인트 2: BASE_URL을 사용하여 엔드포인트 동적 구성
const API_ENDPOINTS: Record<QueryMode, string> = {
  rag: `${BASE_URL}/rag/query`,
  advanced_rag: `${BASE_URL}/rag/advanced_query`,
  web_search: `${BASE_URL}/web-agent/agent/web-search`,
};

// 훅이 반환할 값들의 타입을 정의합니다.
interface UseDynamicQueryReturn {
  executeQuery: (query: string, mode: QueryMode) => Promise<void>;
  data: any;
  isQueryLoading: boolean;
  queryError: Error | null;
}

/**
 * 선택된 쿼리 모드에 따라 다른 API로 요청을 보내는 커스텀 훅
 */
export const useDynamicQuery = (): UseDynamicQueryReturn => {
  const [data, setData] = useState<any>(null);
  const [isQueryLoading, setIsLoading] = useState(false);
  const [queryError, setQeuryError] = useState<Error | null>(null);

  const executeQuery = useCallback(async (query: string, mode: QueryMode) => {
    // API URL을 mode에 따라 동적으로 선택합니다.
    const url = API_ENDPOINTS[mode];
    if (!url) {
      setQeuryError(new Error(`Invalid query mode: ${mode}`));
      return;
    }

    // 요청 시작 시 상태 초기화
    setIsLoading(true);
    setQeuryError(null);
    setData(null);

    try {
      // ✅ 수정 포인트 3: 하드코딩된 localhost 제거 -> BASE_URL 사용
      // 1. 의도 분석 단계
      const analyzeResponse = await fetch(`${BASE_URL}/rag/analyze_intention`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: query }),
      });

      if (!analyzeResponse.ok) {
        throw new Error("Intention analysis failed");
      }

      const analyzeResult = await analyzeResponse.json();

      // 2. 의도에 따른 분기 처리
      if (analyzeResult.next === "CHAT") {
        // ✅ 수정 포인트 4: BASE_URL 사용
        // CHAT인 경우 가이드 엔드포인트 호출
        const guideResponse = await fetch(`${BASE_URL}/rag/guide`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ query: query }),
        });

        if (!guideResponse.ok) {
          throw new Error("Guide request failed");
        }

        const guideResult = await guideResponse.json();
        setData(guideResult);
      } else {
        // RAG인 경우 원래의 엔드포인트 호출 (위에서 정의한 url 변수 사용)
        const response = await fetch(url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ query: query }),
        });

        if (!response.ok) {
          throw new Error(`API request failed: ${response.statusText}`);
        }

        const result = await response.json();
        setData(result);
        console.log(result);
      }
    } catch (err) {
      if (err instanceof Error) {
        setQeuryError(err);
      } else {
        setQeuryError(new Error("An unknown error occurred."));
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { executeQuery, data, isQueryLoading, queryError };
};