// components/StepperIndicator.tsx
import { Check } from "lucide-react";

type Props = {
  currentStep: number;
};

export function StepIndicator({ currentStep }: Props) {
  const steps = ["파일 업로드", "벡터 저장", "완료"];

  return (
    <div className="mb-6 flex items-center">
      {steps.map((step, index) => {
        const stepNumber = index + 1;
        const isActive = currentStep === stepNumber;
        const isCompleted = currentStep > stepNumber;

        return (
          <div key={step} className="flex flex-1 items-center">
            <div className="flex items-center gap-2">
              <div
                className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[12.5px] font-bold transition-colors ${
                  isCompleted
                    ? "bg-brand-600 text-white"
                    : isActive
                    ? "bg-brand-100 text-brand-700 ring-2 ring-brand-500"
                    : "bg-ink-100 text-ink-400"
                }`}
              >
                {isCompleted ? <Check size={14} strokeWidth={3} /> : stepNumber}
              </div>
              <p
                className={`whitespace-nowrap text-[12.5px] ${
                  isActive
                    ? "font-bold text-ink-900"
                    : isCompleted
                    ? "font-medium text-ink-600"
                    : "text-ink-400"
                }`}
              >
                {step}
              </p>
            </div>
            {index < steps.length - 1 && (
              <div
                className={`mx-2 h-px flex-1 ${
                  isCompleted ? "bg-brand-300" : "bg-ink-200"
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
