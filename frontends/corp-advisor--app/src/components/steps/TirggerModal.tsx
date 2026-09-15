// components/steps/Step2_Trigger.tsx
import { useState } from "react";
import { Button } from "../Button";
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

type Props = {
  files: File[]; // 표시할 파일 이름
  onTriggerSuccess: () => void; // 트리거 성공 시 호출될 함수
};

export function TriggerModal({ files, onTriggerSuccess }: Props) {
  const [isProcessing, setIsProcessing] = useState(false);

  const handleTrigger = async () => {
    setIsProcessing(true);

    const fileNames = files.map((file) => file.name).join(", ");
    console.log("업로드할 파일들:", fileNames);
    try {
      const response = await fetch(`${BASE_URL}/rag/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_name: files.map((f) => f.name) }),
      });
      const data = await response.json();
      console.log("업로드 응답 데이터:", data);
      onTriggerSuccess(); // 업로드 성공 시 부모 컴포넌트에 알림
    } catch (err) {
      console.error("파일 업로드에 실패했습니다:", err);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div>
      <h2 className="mb-1.5 text-[17px] font-bold text-ink-900">
        벡터 DB에 저장
      </h2>
      <p className="mb-4 text-[13.5px] leading-relaxed text-ink-500">
        {files.length}개 문서를 조문 단위로 청크로 나눈 뒤 bge-m3 임베딩을 생성해
        저장합니다. 문서 길이에 따라 수십 초가 걸릴 수 있습니다.
      </p>
      <Button
        ButtonText={isProcessing ? "적재 중…" : "적재 시작"}
        onClick={handleTrigger}
        disabled={isProcessing}
      />
    </div>
  );
}
