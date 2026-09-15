import { ArrowRight, Building2, Search } from "lucide-react";
import type { FinancialRecord } from "../hooks/useCorpData";

// ReportTable 컴포넌트가 받을 props의 타입을 정의합니다.
interface ReportTableProps {
  loading: boolean;
  error: string | null;
  data: FinancialRecord[];
  searchTerm: string;
  isSearchInput: boolean;
  onSearchChange: (term: string) => void;
  onClick?: (corp_code: string) => void;
  /** 아직 검색을 실행하지 않은 상태 */
  isIdle?: boolean;
}

function formatModifyDate(value: string) {
  if (!value || value.length !== 8) return value;
  return `${value.slice(0, 4)}-${value.slice(4, 6)}-${value.slice(6)}`;
}

export function Table({
  loading,
  error,
  data,
  searchTerm,
  isSearchInput,
  onSearchChange,
  onClick,
  isIdle = false,
}: ReportTableProps) {
  const shell =
    "overflow-hidden rounded-2xl border border-ink-200 bg-white shadow-card";

  if (loading) {
    return (
      <div className={`${shell} px-6 py-14 text-center`}>
        <div className="mx-auto mb-3 h-8 w-8 animate-spin rounded-full border-[3px] border-ink-200 border-t-brand-500" />
        <p className="text-[14px] text-ink-500">
          DART 기업 목록을 조회하고 있습니다…
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`${shell} px-6 py-12 text-center`}>
        <p className="text-[14px] font-semibold text-red-600">{error}</p>
        <p className="mt-1 text-[13px] text-ink-500">
          백엔드 서버가 실행 중인지 확인해주세요.
        </p>
      </div>
    );
  }

  if (isIdle) {
    return (
      <div className={`${shell} px-6 py-14 text-center`}>
        <Search size={22} className="mx-auto mb-3 text-ink-300" />
        <p className="text-[14px] text-ink-500">
          기업명을 입력하면 DART에 등록된 기업 목록을 보여드립니다.
        </p>
      </div>
    );
  }

  return (
    <div className={shell}>
      {/* 검색창 */}
      {isSearchInput && (
        <div className="border-b border-ink-100 p-3">
          <input
            type="text"
            placeholder="기업명을 검색해주세요."
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full rounded-lg border border-ink-200 p-2.5 text-[14px] transition focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
          />
        </div>
      )}

      <div className="flex items-center justify-between border-b border-ink-100 bg-ink-50/60 px-4 py-2.5">
        <p className="text-[12.5px] font-semibold text-ink-500">
          검색 결과 {data.length}건
        </p>
        <p className="hidden text-[12px] text-ink-400 sm:block">
          기업을 선택하면 보고서 생성이 시작됩니다
        </p>
      </div>

      {/* 데이터 테이블 */}
      <div className="max-h-[22rem] overflow-y-auto">
        {data.length > 0 ? (
          <ul className="divide-y divide-ink-100">
            {data.map((row) => (
              <li key={row.corp_code}>
                <button
                  type="button"
                  onClick={() => onClick && onClick(row.corp_code)}
                  className="group flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-brand-50/50"
                >
                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-ink-100 text-ink-500 transition-colors group-hover:bg-brand-100 group-hover:text-brand-600">
                    <Building2 size={16} />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="flex items-center gap-1.5">
                      <span className="truncate text-[14.5px] font-semibold text-ink-900">
                        {row.corp_name}
                      </span>
                      {row.stock_code && (
                        <span className="shrink-0 rounded bg-brand-50 px-1.5 py-0.5 text-[10.5px] font-bold text-brand-700">
                          상장 {row.stock_code}
                        </span>
                      )}
                    </span>
                    <span className="block truncate text-[12.5px] text-ink-400">
                      {row.corp_eng_name || "영문명 없음"}
                    </span>
                  </span>
                  <span className="hidden shrink-0 text-right sm:block">
                    <span className="block font-mono text-[12.5px] text-ink-600">
                      {row.corp_code}
                    </span>
                    <span className="block text-[11.5px] text-ink-400">
                      수정 {formatModifyDate(row.modify_date)}
                    </span>
                  </span>
                  <ArrowRight
                    size={16}
                    className="shrink-0 text-ink-300 transition-all group-hover:translate-x-0.5 group-hover:text-brand-500"
                  />
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <div className="px-6 py-12 text-center text-[14px] text-ink-400">
            검색 결과가 없습니다. 다른 기업명으로 검색해보세요.
          </div>
        )}
      </div>
    </div>
  );
}
