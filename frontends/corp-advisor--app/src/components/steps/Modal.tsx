import React from "react";
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
      className="fixed inset-0 bg-black bg-opacity-50 z-50 flex justify-center items-center"
      onClick={onClose}
    >
      <div
        className="bg-white p-8 rounded-lg shadow-xl relative w-full max-w-md"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-500 hover:text-gray-800"
        >
          &times;
        </button>
        <StepIndicator currentStep={currentStep} />
        {renderStep()}
      </div>
    </div>
  );
}
