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
    // --- 여기에 벡터 DB 저장 트리거 API 호출 로직 구현 ---
    console.log("벡터 DB 저장 트리거 API 호출...");

    // API 호출이 성공했다고 가정하고, 1.5초 후 다음 단계로 이동
    setTimeout(() => {
      setIsProcessing(false);
      onTriggerSuccess(); // 부모 컴포넌트에 알림
    }, 1500);
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
