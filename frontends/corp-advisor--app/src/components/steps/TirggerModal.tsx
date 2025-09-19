// components/steps/Step2_Trigger.tsx
import { useState } from "react";
import { Button } from "../Button";

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
      const response = await fetch("http://127.0.0.1:8000/rag/register", {
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
      <h2 className="text-xl font-bold mb-4">2. 벡터 DB 저장</h2>
      <p className="mb-4">{files.length}개 파일에 대한 저장을 시작할까요?</p>
      <Button
        ButtonText={isProcessing ? "업로드 중..." : "업로드 하기"}
        onClick={handleTrigger}
      ></Button>
    </div>
  );
}
