import { useState, useEffect, useRef } from "react";
import { useChat } from "../ChatContext.tsx";
import { useCorpData, FinancialRecord } from "../hooks/useCorpData.ts";
import { Table } from "../components/Table.tsx";
import { Button } from "../components/Button.tsx";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { LoadingSpinner } from "../components/LoadingSpinner.tsx";

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
  };

  useEffect(() => {
    const handleResize = () => setDeviceType(getDeviceType());
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const generateReport = async (corpCode?: string) => {
    const codeToUse = corpCode;
    if (!codeToUse?.trim()) return;

    const loadingAnswerId = Date.now() + 1;
    const loadingAnswer: Message = {
      id: loadingAnswerId,
      type: "answer",
      text: <LoadingSpinner loadingText="답변을 생성 중입니다. 잠시만 기다려주세요."/>,
    };

    setMessages((prev) => [...prev, loadingAnswer]);
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

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === loadingAnswerId ? { ...msg, text: data } : msg
        )
      );
    } catch (err) {
      console.error("답변을 가져오는 데 실패했습니다:", err);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === loadingAnswerId
            ? {
                ...msg,
                text: "답변을 가져오는 데 실패했습니다. 기업 코드를 올바르게 작성했는지 확인해주세요.",
              }
            : msg
        )
      );
    }
  };

  const inputContainerClass =
    deviceType === "mobile" ? "w-full" : "w-2/3 mx-auto";
  const messageListClass =
    deviceType === "mobile" ? "p-4" : "w-1/2 mx-auto p-4";

  const hasMessages = messages.length > 0;

  return (
    <div className="w-full flex flex-col justify-center items-start min-h-screen bg-white font-sans">
      {hasMessages ? (
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
                      <div className="prose max-w-none w-full">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            a: ({ node, ...props }) => (
                              <a {...props} target="_blank" rel="noopener noreferrer">
                                {props.children}
                              </a>
                            ),
                          }}
                        >
                          {msg.text}
                        </ReactMarkdown>
                      </div>
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
          <div className="flex flex-col justify-start items-start gap-2 p-4">
            <header className="w-full text-center">
              <h1 className="text-4xl font-bold text-gray-800 mb-2">
                기업 보고서 생성
              </h1>
              <p className="text-gray-500">CorpAdvisor</p>
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
                <Button ButtonText="검색" onClick={handleCorpSearch} />
              </div>

              <Table
                loading={corpLoading}
                error={corpError}
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
            </main>
          </div>
        </div>
      )}
    </div>
  );
}

export default Report;
