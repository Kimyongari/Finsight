import { useState, useEffect } from "react";

export interface FinancialRecord {
  corp_code: string;
  corp_name: string;
  corp_eng_name: string;
  modify_date: string;
}

interface ApiResponse {
  data: FinancialRecord[];
}

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
          "http://localhost:8000/financial/corp_list",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ keyword: query }),
          }
        );

        if (!response.ok)
          throw new Error("기업 리스트를 가져오는 데 실패했습니다.");
        const responseData: ApiResponse = await response.json();
        const result = responseData.data;

        setData(result);
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
