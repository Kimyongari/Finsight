// components/steps/Step3_Complete.tsx
import { CheckCircle2 } from "lucide-react";
import { Button } from "../Button";

type Props = {
  onClose: () => void; // 모달 닫기 함수
};

export function CompleteModal({ onClose }: Props) {
  return (
    <div className="text-center">
      <CheckCircle2 size={36} className="mx-auto mb-3 text-brand-600" />
      <h2 className="mb-1.5 text-[17px] font-bold text-ink-900">
        적재가 완료되었습니다
      </h2>
      <p className="mb-5 text-[13.5px] leading-relaxed text-ink-500">
        업로드한 문서가 벡터 DB에 저장되었습니다.
        <br />
        이제 해당 문서를 근거로 질문할 수 있습니다.
      </p>
      <Button ButtonText="닫기" onClick={onClose} />
    </div>
  );
}
