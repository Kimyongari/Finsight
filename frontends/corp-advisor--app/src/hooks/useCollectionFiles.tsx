// hooks/useCollectionFiles.ts
import { useState, useEffect, useCallback } from "react";

// API 응답으로 받을 파일의 타입 (필요에 따라 수정)
export interface CollectionFile {
  file_name: string;
  [key: string]: any;
}

export const useCollectionFiles = () => {
  // 파일 목록 상태
  const [files, setFiles] = useState<CollectionFile[]>([]);
  // 로딩 상태
  const [isFileLoading, setIsLoading] = useState<boolean>(false);
  // 에러 상태
  const [error, setError] = useState<Error | null>(null);

  // API 호출 함수 (useCallback으로 불필요한 재실행 방지)
  const fetchFiles = useCallback(async () => {
    setIsLoading(true);
    setError(null); // 이전 에러 초기화
    try {
      const response = await fetch(
        "http://localhost:8000/rag/show_files_in_collection"
      );

      // HTTP 상태 코드가 2xx가 아닐 경우 에러 처리
      if (!response.ok) {
        throw new Error(
          `API 요청 실패: ${response.status} ${response.statusText}`
        );
      }

      const data = await response.json();
      const fileList = await data.unique_file_name_and_chunk;
      setFiles(fileList);
    } catch (err) {
      // 타입 가드를 통해 err가 Error 인스턴스인지 확인
      if (err instanceof Error) {
        setError(err);
      } else {
        setError(new Error("알 수 없는 에러가 발생했습니다."));
      }
      console.error("파일 목록을 가져오는 데 실패했습니다:", err);
    } finally {
      // 성공/실패 여부와 관계없이 로딩 상태 종료
      setIsLoading(false);
    }
  }, []);

  // 컴포넌트가 처음 마운트될 때 파일 목록을 한번 가져옴
  useEffect(() => {
    fetchFiles();
  }, [fetchFiles]); // fetchFiles는 useCallback으로 감싸져 있어 한번만 실행됨

  // 훅을 사용하는 컴포넌트에게 상태와 함수를 반환
  return { files, isFileLoading, error, refetch: fetchFiles };
};
