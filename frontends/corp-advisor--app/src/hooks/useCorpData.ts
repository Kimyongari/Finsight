import { useState, useEffect } from "react";

export interface FinancialRecord {
  corp_code: string;
  corp_name: string;
  corp_eng_name: string;
  modify_date: string;
  /** 상장사만 값이 있다 (6자리 종목코드) */
  stock_code?: string | null;
}

/** 이름이 정확히 일치하거나 상장된 기업을 위로 올린다. */
function sortByRelevance(
  records: FinancialRecord[],
  keyword: string
): FinancialRecord[] {
  const query = keyword.trim();
  const score = (record: FinancialRecord) => {
    let value = 0;
    if (record.stock_code) value -= 4; // 상장사 우선
    if (record.corp_name === query) value -= 8; // 정확 일치 최우선
    value += record.corp_name.length * 0.01; // 짧은 이름 우선
    return value;
  };
  return [...records].sort((a, b) => score(a) - score(b));
}

interface ApiResponse {
  data: FinancialRecord[];
}

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const useCorpData = (query: string) => {
  const [data, setData] = useState<FinancialRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!query) return;

    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `${BASE_URL}/financial/corp_list`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ keyword: query }),
          }
        );

        if (!response.ok)
          throw new Error("기업 리스트를 가져오는 데 실패했습니다.");
        const responseData: ApiResponse = await response.json();
        const result = responseData.data ?? [];

        setData(sortByRelevance(result, query));
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [query]);

  return { data, loading, error };
};
