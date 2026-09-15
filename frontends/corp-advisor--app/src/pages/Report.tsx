import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useChat } from "../ChatContext.tsx";
import { useCorpData } from "../hooks/useCorpData.ts";
import { Table } from "../components/Table.tsx";
import { SendHorizonal, ChevronLeft, Printer, RotateCcw } from "lucide-react";
import { LoadingSpinner } from "../components/LoadingSpinner.tsx";
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const REPORT_STEPS = [
  "DART 기업개황",
  "재무제표 파싱",
  "뉴스 수집·분석",
  "차트 생성",
  "종합 결론",
];

const HtmlWithScriptsRenderer = ({ htmlString }: { htmlString: string }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || !htmlString) return;

    // Clear previous content
    container.innerHTML = "";

    const tempDiv = document.createElement("div");
    tempDiv.innerHTML = htmlString;

    // Force links to open in a new tab
    const links = Array.from(tempDiv.querySelectorAll("a"));
    links.forEach((link) => {
      link.setAttribute("target", "_blank");
      link.setAttribute("rel", "noopener noreferrer"); // For security
    });

    // 재무제표처럼 열이 많은 표는 가로 스크롤 컨테이너로 감싼다
    Array.from(tempDiv.querySelectorAll("table")).forEach((table) => {
      if (table.parentElement?.classList.contains("table-wrap")) return;
      const wrap = document.createElement("div");
      wrap.className = "table-wrap";
      table.parentElement?.insertBefore(wrap, table);
      wrap.appendChild(table);
    });

    const scripts = Array.from(tempDiv.querySelectorAll("script"));

    // Append non-script HTML content first
    const fragment = document.createDocumentFragment();
    Array.from(tempDiv.childNodes).forEach((node) => {
      if (node.nodeName.toLowerCase() !== "script") {
        fragment.appendChild(node.cloneNode(true));
      }
    });
    container.appendChild(fragment);

    const loadedScripts: HTMLScriptElement[] = [];

    const executeScripts = async () => {
      for (const script of scripts) {
        const newScript = document.createElement("script");
        script.getAttributeNames().forEach((attr) => {
          newScript.setAttribute(attr, script.getAttribute(attr) || "");
        });

        if (script.src) {
          await new Promise<void>((resolve, reject) => {
            newScript.onload = () => resolve();
            newScript.onerror = () =>
              reject(new Error(`Script load error for ${script.src}`));
            document.body.appendChild(newScript);
            loadedScripts.push(newScript);
          });
        } else {
          newScript.innerHTML = script.innerHTML;
          document.body.appendChild(newScript);
          loadedScripts.push(newScript);
        }
      }
    };

    executeScripts();

    return () => {
      loadedScripts.forEach((script) => {
        if (document.body.contains(script)) {
          document.body.removeChild(script);
        }
      });
    };
  }, [htmlString]);

  return <div ref={containerRef} className="report-body w-full" />;
};

// 메시지 타입 정의
type Message = {
  id: number;
  type: "question" | "answer" | "loading";
  text: string | React.ReactNode;
  isStreaming?: boolean;
};

/** 보고서 HTML에서 제목(h1)을 뽑아 상단 바에 표시한다. */
function extractReportTitle(html: string): string {
  const match = html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i);
  if (!match) return "기업 분석 보고서";
  return match[1].replace(/<[^>]+>/g, "").trim() || "기업 분석 보고서";
}

function Report() {
  const navigate = useNavigate();

  const [searchTerm, setSearchTerm] = useState(""); // 입력 폼 값
  const [submittedTerm, setSubmittedTerm] = useState(""); // fetch에 사용
  const [tableSearch, setTableSearch] = useState(""); // 테이블 내부 검색
  const [reportStatus, setReportStatus] = useState<
    "idle" | "success" | "error"
  >("idle");
  const [isGenerating, setIsGenerating] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { messages, setMessages } = useChat();
  const chatEndRef = useRef<null | HTMLDivElement>(null);

  const {
    data: corpData,
    loading: corpLoading,
    error: corpError,
  } = useCorpData(submittedTerm);

  const handleCorpSearch = () => {
    if (!searchTerm.trim()) return;
    setSubmittedTerm(searchTerm.trim());
    setTableSearch(searchTerm.trim()); // 동시에 테이블 필터링
  };

  const handleNewReport = () => {
    setMessages([]);
    localStorage.removeItem("chatMessages");
    setReportStatus("idle");
    setErrorMessage(null);
  };

  const generateReport = async (corpCode?: string) => {
    const codeToUse = corpCode;
    if (!codeToUse?.trim()) return;

    // ✅ 이전 보고서 메시지 초기화
    setMessages([]);
    localStorage.removeItem("chatMessages");

    setIsGenerating(true);
    setErrorMessage(null);
    setSearchTerm("");

    try {
      const response = await fetch(`${BASE_URL}/report/${codeToUse}`, {
        method: "GET",
      });

      if (!response.ok) throw new Error("네트워크 응답이 실패했습니다.");
      const data = await response.text();

      setReportStatus("success");

      const reportAnswer: Message = {
        id: Date.now(),
        type: "answer",
        text: data,
      };

      // ✅ 이전 메시지가 아니라 완전히 새 메시지만 추가
      setMessages([reportAnswer]);
    } catch (err) {
      console.error("답변을 가져오는 데 실패했습니다:", err);
      setErrorMessage(
        "보고서를 생성하지 못했습니다. 선택한 기업의 공시 데이터가 없거나 서버에 문제가 있을 수 있습니다."
      );
      setReportStatus("error");
    } finally {
      setIsGenerating(false);
    }
  };

  const reportHtml =
    typeof messages[0]?.text === "string" ? (messages[0].text as string) : "";
  const reportTitle = reportHtml ? extractReportTitle(reportHtml) : "";

  // ---------- 보고서 결과 화면 ----------
  if (reportStatus === "success" && reportHtml) {
    return (
      <div className="flex min-h-screen w-full flex-col bg-ink-50 font-sans">
        <header className="sticky top-0 z-20 border-b border-ink-200 bg-white">
          <div className="mx-auto flex w-full max-w-4xl items-center justify-between gap-3 px-4 py-2.5 sm:px-6">
            <button
              onClick={() => navigate("/")}
              className="flex items-center gap-1 rounded-lg px-2 py-1.5 text-[13.5px] font-medium text-ink-500 transition-colors hover:bg-ink-100 hover:text-ink-800"
            >
              <ChevronLeft size={18} />
              <span className="hidden sm:inline">홈으로</span>
            </button>

            <p className="min-w-0 flex-1 truncate text-center text-[14px] font-bold tracking-tight text-ink-900">
              {reportTitle}
            </p>

            <div className="flex items-center gap-1">
              <button
                onClick={() => window.print()}
                className="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-[13.5px] font-medium text-ink-500 transition-colors hover:bg-ink-100 hover:text-ink-800"
              >
                <Printer size={15} />
                <span className="hidden sm:inline">인쇄</span>
              </button>
              <button
                onClick={handleNewReport}
                className="flex items-center gap-1.5 rounded-lg bg-brand-600 px-3 py-1.5 text-[13.5px] font-semibold text-white transition-colors hover:bg-brand-700"
              >
                <RotateCcw size={14} />
                <span className="hidden sm:inline">다른 기업</span>
              </button>
            </div>
          </div>
        </header>

        <main className="mx-auto w-full max-w-4xl flex-1 px-4 py-8 sm:px-6">
          <article className="rounded-2xl border border-ink-200 bg-white p-6 shadow-card sm:p-10">
            <HtmlWithScriptsRenderer htmlString={reportHtml} />
          </article>
          <p className="mt-4 text-center text-[12.5px] text-ink-400">
            본 보고서는 DART 공시와 웹 자료를 AI가 자동 분석한 결과이며 투자
            권유가 아닙니다.
          </p>
          <div ref={chatEndRef} />
        </main>
      </div>
    );
  }

  // ---------- 기업 검색 화면 ----------
  return (
    <div className="flex min-h-screen w-full flex-col bg-ink-50 font-sans">
      <header className="border-b border-ink-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex w-full max-w-3xl items-center justify-between gap-3 px-4 py-2.5 sm:px-6">
          <button
            onClick={() => navigate("/")}
            className="flex items-center gap-1 rounded-lg px-2 py-1.5 text-[13.5px] font-medium text-ink-500 transition-colors hover:bg-ink-100 hover:text-ink-800"
          >
            <ChevronLeft size={18} />
            <span className="hidden sm:inline">홈으로</span>
          </button>
          <span className="text-[14px] font-bold tracking-tight text-ink-900">
            기업 분석 보고서
          </span>
          <span className="hidden rounded-full border border-ink-200 bg-ink-50 px-2 py-0.5 text-[11.5px] font-medium text-ink-500 sm:inline">
            DART · 뉴스 · 차트
          </span>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col justify-center px-4 py-10 sm:px-6">
        {isGenerating ? (
          <LoadingSpinner
            loadingText="보고서를 생성하고 있습니다"
            steps={REPORT_STEPS}
            block
          />
        ) : (
          <>
            <div className="mb-7 text-center">
              <h1 className="mb-2 text-[30px] font-extrabold tracking-tight text-ink-900">
                어떤 기업을 분석할까요?
              </h1>
              <p className="text-[14.5px] text-ink-500">
                DART 공시 기준 기업명을 입력해주세요. (예: 삼성전자, 카카오,
                셀트리온)
              </p>
            </div>

            <div className="mb-4 flex gap-2">
              <input
                type="text"
                className="flex-1 rounded-xl border border-ink-200 bg-white px-4 py-3 text-[15px] shadow-card transition focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
                placeholder="기업명을 입력하세요"
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value); // 입력값 상태
                  setTableSearch(e.target.value); // 테이블 필터링
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleCorpSearch();
                }}
              />
              <button
                type="button"
                onClick={handleCorpSearch}
                aria-label="기업 검색"
                className="flex items-center justify-center rounded-xl bg-brand-600 px-5 text-white transition-all hover:bg-brand-700 active:scale-95"
              >
                <SendHorizonal size={18} />
              </button>
            </div>

            {errorMessage && (
              <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-[13.5px] text-red-700">
                {errorMessage}
              </div>
            )}

            <Table
              loading={corpLoading}
              error={corpError}
              isIdle={!submittedTerm}
              data={corpData.filter((item) =>
                Object.values(item).some((v) =>
                  String(v).toLowerCase().includes(tableSearch.toLowerCase())
                )
              )}
              isSearchInput={false}
              searchTerm={tableSearch}
              onSearchChange={setTableSearch}
              onClick={generateReport}
            />
          </>
        )}
      </main>
    </div>
  );
}

export default Report;
