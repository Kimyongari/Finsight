import { useState, useEffect, useRef } from "react";
import { useChat } from "../ChatContext.tsx";
import { useCorpData, FinancialRecord } from "../hooks/useCorpData.ts";
import { Table } from "../components/Table.tsx";
import { Button } from "../components/Button.tsx";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { SendHorizonal } from "lucide-react";
import { LoadingSpinner } from "../components/LoadingSpinner.tsx";

const HtmlWithScriptsRenderer = ({ htmlString }: { htmlString: string }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || !htmlString) return;

    // Clear previous content
    container.innerHTML = "";

    const tempDiv = document.createElement("div");
    tempDiv.innerHTML = htmlString;

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

  return <div ref={containerRef} className="prose max-w-none w-full" />;
};

// 메시지 타입 정의
type Message = {
  id: number;
  type: "question" | "answer" | "loading";
  text: string | React.ReactNode;
  isStreaming?: boolean;
};

function Report() {
  const getDeviceType = () => {
    const width = window.innerWidth;
    if (width <= 768) return "mobile";
    if (width <= 1024) return "tablet";
    return "desktop";
  };

  const [deviceType, setDeviceType] = useState(getDeviceType());
  const [searchTerm, setSearchTerm] = useState(""); // 입력 폼 값
  const [submittedTerm, setSubmittedTerm] = useState(""); // fetch에 사용
  const [tableSearch, setTableSearch] = useState(""); // 테이블 내부 검색
  const [reportStatus, setReportStatus] = useState<
    "idle" | "success" | "error"
  >("idle");
  const [isGenerating, setIsGenerating] = useState(false);

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
  };

  useEffect(() => {
    const handleResize = () => setDeviceType(getDeviceType());
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const generateReport = async (corpCode?: string) => {
    const codeToUse = corpCode;
    if (!codeToUse?.trim()) return;

    // ✅ 이전 보고서 메시지 초기화
    setMessages([]);
    localStorage.removeItem("chatMessages");

    setIsGenerating(true);
    setSearchTerm("");

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/report/${codeToUse}`,
        {
          method: "GET",
        }
      );

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
      alert("입력하신 기업 코드로 검색된 리포트 정보가 없습니다.");
      console.error("답변을 가져오는 데 실패했습니다:", err);
      setReportStatus("error");
    } finally {
      setIsGenerating(false);
    }
  };
  const inputContainerClass =
    deviceType === "mobile" ? "w-full" : "w-2/3 mx-auto";
  const messageListClass =
    deviceType === "mobile" ? "p-4" : "w-1/2 mx-auto p-4";

  const hasMessages = messages.length > 0;

  return (
    <div className="w-full flex flex-col justify-center items-start min-h-screen bg-white font-sans">
      {reportStatus === "success" ? (
        <>
          <main className="w-full flex-1 overflow-y-auto pb-32">
            <div className={messageListClass}>
              <div className="space-y-4">
                {messages.map((msg) => {
                  const isQuestion = msg.type === "question";
                  return (
                    <div
                      key={msg.id}
                      className={`rounded-2xl break-words ${
                        isQuestion
                          ? "p-4 text-justify max-w-[80%] md:max-w-[70%] bg-indigo-50 shadow-sm text-gray-800 rounded-br-none"
                          : "w-full"
                      }`}
                    >
                      {typeof msg.text === "string" ? (
                        <HtmlWithScriptsRenderer
                          htmlString={msg.text as string}
                        />
                      ) : (
                        msg.text
                      )}
                    </div>
                  );
                })}
              </div>
              <div ref={chatEndRef} />
            </div>
          </main>
          <footer className="flex-1 flex-col justify-center items-center bg-white border-t border-gray-200 p-4 fixed bottom-0 left-0 right-0">
            <div className={`${inputContainerClass} mb-3 flex justify-center`}>
              <Button
                ButtonText="다른 기업의 보고서 생성하기"
                onClick={handleNewReport}
              />
            </div>
          </footer>
        </>
      ) : (
        <div className="w-full min-h-screen flex-1 flex justify-center items-center bg-gray-50">
          {isGenerating ? (
            <LoadingSpinner loadingText="리포트를 생성중입니다..." />
          ) : (
            <div className="flex flex-col justify-start items-start gap-2 p-4">
              <header className="w-full text-center">
                <h1 className="text-4xl font-bold text-gray-800 mb-2">
                  기업 보고서 생성
                </h1>
                <p className="text-gray-500">FinSight</p>
              </header>
              <main className="w-full max-w-screen-md">
                <div className="overflow-x-auto w-full mb-4 flex gap-2 p-4">
                  <input
                    type="text"
                    className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
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
                    className={`px-5 py-3 text-white font-bold rounded-lg self-end bg-indigo-500 hover:bg-indigo-600 transform transition-transform duration-200 hover:scale-105 active:scale-95}`}
                  >
                    <SendHorizonal />
                  </button>
                </div>

                <Table
                  loading={corpLoading}
                  error={corpError}
                  data={corpData.filter((item) =>
                    Object.values(item).some((v) =>
                      String(v)
                        .toLowerCase()
                        .includes(tableSearch.toLowerCase())
                    )
                  )}
                  isSearchInput={false}
                  searchTerm={tableSearch}
                  onSearchChange={setTableSearch}
                  onClick={generateReport}
                />
              </main>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default Report;
