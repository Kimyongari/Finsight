// components/StepperIndicator.tsx
type Props = {
  currentStep: number;
};

export function StepIndicator({ currentStep }: Props) {
  const steps = ["파일 업로드", "벡터 저장", "완료"];

  return (
    <div className="flex justify-between items-center mb-6">
      {steps.map((step, index) => {
        const stepNumber = index + 1;
        const isActive = currentStep === stepNumber;
        const isCompleted = currentStep > stepNumber;

        return (
          <div key={step} className="flex items-center">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-white ${
                isActive || isCompleted ? "bg-blue-500" : "bg-gray-300"
              }`}
            >
              {isCompleted ? "✓" : stepNumber}
            </div>
            <p className={`ml-2 ${isActive ? "font-bold" : ""}`}>{step}</p>
          </div>
        );
      })}
    </div>
  );
}
