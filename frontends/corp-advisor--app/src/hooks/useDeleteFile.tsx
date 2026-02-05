import { useState, useCallback } from "react";

// 훅이 반환할 상태와 함수의 타입을 정의합니다.
interface UseDeleteFileReturn {
  deleteFile: (fileName: string) => Promise<void>;
  isDeleteLoading: boolean;
  isSuccess: boolean;
  error: Error | null;
}
const BASE_URL = import.meta.env.VITE_API_URL || "http://34.22.88.153:8000";

/**
 * 파일 이름으로 서버에 파일 삭제 요청을 보내는 커스텀 훅
 * @returns {UseDeleteFileReturn} deleteFile 함수, 로딩, 성공, 에러 상태
 */
export const useDeleteFile = (): UseDeleteFileReturn => {
  const [isDeleteLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const deleteFile = useCallback(async (fileName: string) => {
    // 요청 시작 시 상태 초기화
    setIsLoading(true);
    setIsSuccess(false);
    setError(null);

    try {
      const response = await fetch(
        `${BASE_URL}/rag/delete_objects_from_file_name`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ file_name: fileName }),
        }
      );

      if (!response.ok) {
        // 서버가 에러 응답을 보냈을 경우
        const errorData = await response.json().catch(() => ({})); // 에러 본문이 JSON이 아닐 수도 있음
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      // 성공적으로 응답을 받았을 때
      setIsSuccess(true);
      console.log(`Successfully deleted: ${fileName}`);
    } catch (err) {
      if (err instanceof Error) {
        setError(err);
      } else {
        setError(new Error("An unknown error occurred."));
      }
      console.error("Failed to delete file:", err);
    } finally {
      setIsLoading(false);
    }
  }, []); // 의존성 배열이 비어있으므로 함수는 재생성되지 않음

  return { deleteFile, isDeleteLoading, isSuccess, error };
};
