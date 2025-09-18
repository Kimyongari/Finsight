import { useState, useEffect, useRef } from "react";
import { Bubble } from "../components/Bubble.tsx";
import { useChat } from "../ChatContext.tsx";
import { FinancialRecord } from "../hooks/useCsvData";
import { Table } from "../components/Table.tsx";
import { Button } from "../components/Button.tsx";

type Message = {
  id: number;
  type: "question" | "answer";
  text: string;
};

interface ReportPageProps {
  csvData: FinancialRecord[];
  isLoading: boolean;
  loadError: string | null;
}

function Report({ csvData, isLoading, loadError }: ReportPageProps) {
  const getDeviceType = () => {
    const width = window.innerWidth;
    if (width <= 768) return "mobile";
    if (width <= 1024) return "tablet";
    return "desktop";
  };

  const [deviceType, setDeviceType] = useState(getDeviceType());

  // 검색 및 필터링 상태
  const [filteredData, setFilteredData] = useState<FinancialRecord[]>([]);
  const [searchTerm, setSearchTerm] = useState("");

  // 원본 데이터 변경 시 필터링 데이터 업데이트
  useEffect(() => {
    setFilteredData(csvData);
  }, [csvData]);

  // 검색어가 변경될 때마다 데이터를 필터링
  useEffect(() => {
    if (!searchTerm) {
      setFilteredData(csvData); // 검색어가 없으면 전체 데이터 표시
    } else {
      const lowercasedFilter = searchTerm.toLowerCase();
      const filtered = csvData.filter((item) =>
        // 각 행의 모든 값을 소문자로 변환하여 검색어와 비교
        Object.values(item).some((value) =>
          String(value).toLowerCase().includes(lowercasedFilter)
        )
      );
      setFilteredData(filtered);
    }
  }, [searchTerm, csvData]);

  const { messages, setMessages } = useChat();
  const [inputValue, setInputValue] = useState("");

  useEffect(() => {
    const handleResize = () => setDeviceType(getDeviceType());
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const inputContainerClass =
    deviceType === "mobile" ? "w-full" : "w-2/3 mx-auto";
  const messageListClass =
    deviceType === "mobile" ? "p-4" : "w-1/2 mx-auto p-4";

  const chatEndRef = useRef<null | HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [inputValue]);

  useEffect(() => {
    localStorage.setItem("chatMessages", JSON.stringify(messages));
  }, [messages]);

  const handleSubmit = async (corpCode?: string) => {
    // corpCode가 있으면 그걸 쓰고, 없으면 inputValue를 씀
    const codeToUse = corpCode ?? inputValue;
    if (!codeToUse.trim()) return;

    const loadingAnswerId = Date.now() + 1;
    const loadingAnswer: Message = {
      id: loadingAnswerId,
      type: "answer",
      text: "답변을 생성 중입니다. 조금만 기다려주세요.",
    };

    setMessages((prev) => [...prev, loadingAnswer]);
    setInputValue("");

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
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      handleSubmit();
    }
  };
  const handleNewReport = () => {
    setMessages([]);
    localStorage.removeItem("chatMessages"); // localStorage도 초기화
  };

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
                    <Bubble
                      key={msg.id}
                      isQuestion={isQuestion}
                      msg={msg}
                      answerClass={`rounded-2xl break-words ${
                        isQuestion
                          ? "p-4 text-justify max-w-[80%] md:max-w-[70%] bg-indigo-50 shadow-sm text-gray-800 rounded-br-none"
                          : "w-full"
                      }`}
                    />
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
              <div className="overflow-x-auto w-full">
                <Table
                  loading={isLoading}
                  error={loadError}
                  data={filteredData}
                  searchTerm={searchTerm}
                  onSearchChange={setSearchTerm}
                  onClick={(corpCode: string) => handleSubmit(corpCode)}
                />
              </div>
            </main>
          </div>
        </div>
      )}
    </div>
  );
}

export default Report;
