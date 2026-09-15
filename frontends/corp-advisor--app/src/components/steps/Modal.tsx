import { X } from "lucide-react";
import { UploadModal } from "./UploadModal";
import { TriggerModal } from "./TirggerModal";
import { CompleteModal } from "./CompleteModal";
import { StepIndicator } from "./StepIndicator";
// Modal 컴포넌트가 받을 props 타입 정의
type ModalProps = {
  currentStep: number;
  uploadedFiles: File[];
  onClose: () => void;
  onUploadSuccess: (files: File[]) => void;
  onTriggerSuccess: () => void;
};

export function Modal({
  currentStep,
  uploadedFiles,
  onClose,
  onUploadSuccess,
  onTriggerSuccess,
}: ModalProps) {
  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return <UploadModal onUploadSuccess={onUploadSuccess} />;
      case 2:
        return (
          <TriggerModal
            files={uploadedFiles}
            onTriggerSuccess={onTriggerSuccess}
          />
        );
      case 3:
        return <CompleteModal onClose={onClose} />;
      default:
        return null;
    }
  };
  return (
    // 모달 배경 (Overlay)
    // 화면 전체를 덮는 반투명한 배경
    // 클릭하면 onClose 함수가 호출되어 모달이 닫힙니다.
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink-900/40 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-md rounded-2xl border border-ink-200 bg-white p-7 shadow-lift"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          aria-label="닫기"
          className="absolute right-3 top-3 rounded-lg p-1.5 text-ink-400 transition-colors hover:bg-ink-100 hover:text-ink-800"
        >
          <X size={16} />
        </button>
        <StepIndicator currentStep={currentStep} />
        {renderStep()}
      </div>
    </div>
  );
}
