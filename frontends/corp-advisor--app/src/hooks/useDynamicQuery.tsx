import { useState, useCallback } from "react";

// 드롭다운에서 선택할 값들의 타입을 미리 정의하여 안정성을 높입니다.
export type QueryMode = "rag" | "advanced_rag" | "web_search";

// 각 모드에 해당하는 API 엔드포인트를 매핑합니다.
const API_ENDPOINTS: Record<QueryMode, string> = {
  rag: "http://localhost:8000/rag/query",
  advanced_rag: "http://localhost:8000/rag/advanced_query",
  web_search: "http://localhost:8000/web-agent/agent/web-search",
};

// 훅이 반환할 값들의 타입을 정의합니다.
interface UseDynamicQueryReturn {
  // executeQuery 함수는 query(질문)와 mode(API 종류)를 인자로 받습니다.
  executeQuery: (query: string, mode: QueryMode) => Promise<void>;
  data: any; // API 응답 데이터 (타입을 더 구체적으로 지정할 수 있습니다)
  isQueryLoading: boolean;
  queryError: Error | null;
}

/**
 * 선택된 쿼리 모드에 따라 다른 API로 요청을 보내는 커스텀 훅
 * @returns {UseDynamicQueryReturn} executeQuery 함수, 데이터, 로딩, 에러 상태
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
    } catch (err) {
      if (err instanceof Error) {
        setQeuryError(err);
      } else {
        setQeuryError(new Error("An unknown error occurred."));
      }
    } finally {
      setIsLoading(false);
    }
  }, []); // 의존성 배열이 비어있으므로 이 함수는 재생성되지 않습니다.

  return { executeQuery, data, isQueryLoading, queryError };
};
