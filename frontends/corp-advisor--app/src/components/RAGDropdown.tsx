import type { ReactNode } from "react";
import { FileSearch, Layers, Globe } from "lucide-react";
import type { QueryMode } from "../hooks/useDynamicQuery";

const options: {
  label: string;
  value: QueryMode;
  icon: ReactNode;
  hint: string;
}[] = [
  {
    label: "일반 분석",
    value: "rag",
    icon: <FileSearch size={14} />,
    hint: "법령 벡터 검색으로 근거 조항을 찾아 답변합니다.",
  },
  {
    label: "심층 분석",
    value: "advanced_rag",
    icon: <Layers size={14} />,
    hint: "검색된 조항이 인용한 참조 조문까지 함께 확장 검색합니다.",
  },
  {
    label: "웹 서치",
    value: "web_search",
    icon: <Globe size={14} />,
    hint: "웹에서 최신 자료를 수집해 요약·분석합니다.",
  },
];

type RAGDropdownProps = {
  value: QueryMode;
  onSelect: (value: QueryMode) => void;
  disabled?: boolean;
};

/** 분석 모드 선택용 세그먼티드 컨트롤. */
export function RAGDropdown({ value, onSelect, disabled }: RAGDropdownProps) {
  const active = options.find((o) => o.value === value) ?? options[0];

  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
      <div
        role="tablist"
        aria-label="분석 모드"
        className="inline-flex rounded-xl border border-ink-200 bg-ink-100/70 p-1"
      >
        {options.map((option) => {
          const isActive = option.value === value;
          return (
            <button
              key={option.value}
              type="button"
              role="tab"
              aria-selected={isActive}
              disabled={disabled}
              onClick={() => onSelect(option.value)}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[13px] font-semibold transition-all duration-150 disabled:cursor-not-allowed disabled:opacity-50 ${
                isActive
                  ? "bg-white text-brand-700 shadow-sm"
                  : "text-ink-500 hover:text-ink-700"
              }`}
            >
              {option.icon}
              {option.label}
            </button>
          );
        })}
      </div>
      <p className="text-[12.5px] text-ink-400">{active.hint}</p>
    </div>
  );
}
