type LoadingSpinnerProps = {
  loadingText: string;
  /** 진행 단계 안내 (선택) */
  steps?: string[];
  /** 세로 중앙 정렬된 큰 로더로 표시 */
  block?: boolean;
};

export const LoadingSpinner = ({
  loadingText,
  steps,
  block = false,
}: LoadingSpinnerProps) => {
  const dots = (
    <span className="flex items-center gap-1" aria-hidden="true">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="h-1.5 w-1.5 rounded-full bg-brand-500 animate-pulse-dot"
          style={{ animationDelay: `${i * 0.16}s` }}
        />
      ))}
    </span>
  );

  if (!block) {
    return (
      <div
        className="flex items-center gap-2.5 py-1 text-[14px] text-ink-500"
        role="status"
      >
        {dots}
        <span>{loadingText}</span>
      </div>
    );
  }

  return (
    <div
      className="flex flex-col items-center justify-center gap-4 py-16 text-center"
      role="status"
    >
      <div className="relative h-10 w-10">
        <div className="absolute inset-0 rounded-full border-[3px] border-ink-200" />
        <div className="absolute inset-0 animate-spin rounded-full border-[3px] border-transparent border-t-brand-500" />
      </div>
      <p className="text-[15px] font-semibold text-ink-800">{loadingText}</p>
      {steps && steps.length > 0 && (
        <ul className="flex flex-wrap items-center justify-center gap-x-2 gap-y-1 text-[12.5px] text-ink-400">
          {steps.map((step, index) => (
            <li key={step} className="flex items-center gap-2">
              {index > 0 && <span className="text-ink-300">→</span>}
              <span>{step}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
