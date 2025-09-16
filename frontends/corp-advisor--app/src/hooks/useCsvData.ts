import { useState, useEffect } from "react";

// 데이터 타입을 정의 다른 곳에서도 사용할 수 있도록 export
export interface FinancialRecord {
  corp_code: string;
  corp_name: string;
  corp_eng_name: string;
  modify_date: string;
}

// CSV 파싱 함수도 훅 파일로 함께 옮겨 관리
const parseCsv = (csvText: string): FinancialRecord[] => {
  const lines = csvText.trim().split("\n");
  if (lines.length < 2) return [];

  const headers = lines[0].split(",").map((h) => h.trim());
  const data: FinancialRecord[] = [];

  for (let i = 1; i < lines.length; i++) {
    const values = lines[i].split(",").map((v) => v.trim());
    if (values.length === headers.length) {
      // CSV 헤더 순서에 의존하지 않도록 객체를 안전하게 생성
      const record: any = {};
      headers.forEach((header, index) => {
        record[header] = values[index];
      });
      data.push(record as FinancialRecord);
    }
  }
  return data;
};

// CSV 데이터를 fetching하고 관리하는 커스텀 훅
export const useCsvData = (filePath: string) => {
  const [data, setData] = useState<FinancialRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(filePath);
        if (!response.ok) {
          throw new Error("CSV 파일을 불러오는 데 실패했습니다.");
        }
        const csvText = await response.text();
        const parsedData = parseCsv(csvText);
        if (parsedData.length === 0) {
          throw new Error("CSV 데이터를 파싱할 수 없거나 파일이 비어있습니다.");
        }
        setData(parsedData);
      } catch (err) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError("알 수 없는 오류가 발생했습니다.");
        }
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [filePath]); // filePath가 변경되면 데이터를 다시 로드

  return { data, loading, error };
};
