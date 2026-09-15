// Chatbot.tsx
import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronLeft, Sparkles, RotateCcw } from "lucide-react";

import { ChatForm } from "../components/ChatForm";
import { Bubble } from "../components/Bubble";
import { Modal } from "../components/steps/Modal";
import { PdfViewer } from "../components/PdfViewer";
import { LoadingSpinner } from "../components/LoadingSpinner";
import type { Message } from "../ChatContext";
import type { CollectionFile } from "../hooks/useCollectionFiles";
import { useCollectionFiles } from "../hooks/useCollectionFiles";
import { useDynamicQuery } from "../hooks/useDynamicQuery";
import type { QueryMode } from "../hooks/useDynamicQuery";
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const initialMessages: Message[] = [];

// 빈 화면에서 제안하는 예시 질문
const SAMPLE_QUESTIONS = [
  "전자금융거래법 시행령상 전자금융업자의 자본금 요건은?",
  "금융회사가 클라우드컴퓨팅서비스를 이용할 때 지켜야 할 절차는?",
  "정보보호최고책임자 지정 대상과 주요 업무를 정리해줘",
  "전자금융사고 배상책임 보험 가입 기준이 궁금해",
];

function Chatbot() {
  const navigate = useNavigate();

  // --- 상태 및 훅 정의 ---

  // 1. 서버에 저장된 파일 목록 관리
  const { files: fetchedFiles, refetch: refetchCollectionFiles } =
    useCollectionFiles();
  const [collectionFiles, setCollectionFiles] = useState<CollectionFile[]>([]);

  // 2. 메시지 및 채팅 관련 상태
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [inputValue, setInputValue] = useState("");
  const [typingTextMap, setTypingTextMap] = useState<{
    [id: number]: { answer: string; cites?: any[] };
  }>({});

  // 3. 동적 API 호출 훅
  const [queryMode, setQueryMode] = useState<QueryMode>("rag");
  const {
    executeQuery,
    data: queryData,
    isQueryLoading: isQueryLoading,
    queryError: queryError,
  } = useDynamicQuery();
  const [pendingMessageId, setPendingMessageId] = useState<number | null>(null);

  // 4. UI 및 기타 상태
  const chatEndRef = useRef<null | HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // --- 파일 삭제 핸들러 ---
  const handleFileDelete = (fileNameToDelete: string) => {
    setCollectionFiles((currentFiles) =>
      currentFiles.filter((file) => file.file_name !== fileNameToDelete)
    );
  };

  // --- useEffect 훅들 ---

  // useCollectionFiles 훅이 파일 목록을 가져오면 collectionFiles 상태에 반영
  useEffect(() => {
    setCollectionFiles(fetchedFiles);
  }, [fetchedFiles]);

  // API 호출 성공 처리
  useEffect(() => {
    if (queryData && pendingMessageId) {
      setTypingTextMap((prev) => ({
        ...prev,
        [pendingMessageId]: {
          answer: queryData.answer,
          cites: queryData.retrieved_documents || queryData.search_results,
        },
      }));
      setPendingMessageId(null);
    }
  }, [queryData, pendingMessageId]);

  // API 호출 실패 처리
  useEffect(() => {
    if (queryError && pendingMessageId) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === pendingMessageId
            ? {
                ...msg,
                type: "answer",
                text: "답변을 가져오는 데 실패했습니다. 백엔드 서버 상태를 확인해주세요.",
                isStreaming: false,
              }
            : msg
        )
      );
      setPendingMessageId(null);
    }
  }, [queryError, pendingMessageId]);

  // 타자 치기 효과 적용 (긴 답변은 한 번에 여러 글자씩 흘려 체감 속도를 유지)
  useEffect(() => {
    const entries = Object.entries(typingTextMap);
    if (entries.length === 0) return;

    const intervals: ReturnType<typeof setInterval>[] = [];

    entries.forEach(([idStr, data]) => {
      const id = Number(idStr);
      const fullText = data.answer ?? "";
      const cites = data.cites;
      const step = Math.max(2, Math.ceil(fullText.length / 220));
      let charIndex = 0;

      const intervalId = setInterval(() => {
        if (charIndex < fullText.length) {
          charIndex = Math.min(charIndex + step, fullText.length);
          const currentText = fullText.slice(0, charIndex);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === id
                ? { ...msg, type: "answer", text: currentText }
                : msg
            )
          );
        } else {
          clearInterval(intervalId);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === id
                ? { ...msg, isStreaming: false, type: "answer", cites: cites }
                : msg
            )
          );
          setTypingTextMap((prev) => {
            const { [id]: _, ...rest } = prev;
            return rest;
          });
        }
      }, 16);

      intervals.push(intervalId);
    });

    return () => intervals.forEach(clearInterval);
  }, [typingTextMap]);

  // 자동 스크롤
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Textarea 높이 자동 조절
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [inputValue]);

  // --- 핸들러 함수들 ---

  const submitQuestion = (rawText: string) => {
    const text = rawText.trim();
    if (!text || isQueryLoading) return;

    const newQuestion: Message = {
      id: Date.now(),
      type: "question",
      text,
    };

    const loadingAnswerId = Date.now() + 1;
    const loadingAnswer: Message = {
      id: loadingAnswerId,
      type: "loading",
      text: (
        <LoadingSpinner
          loadingText={
            queryMode === "web_search"
              ? "웹에서 자료를 수집해 분석하고 있습니다"
              : "관련 법령을 검색해 답변을 작성하고 있습니다"
          }
        />
      ),
      isStreaming: true,
    };

    setMessages((prev) => [...prev, newQuestion, loadingAnswer]);
    setInputValue("");
    setIsPdfVisible(false);
    setPendingMessageId(loadingAnswerId);

    // 훅을 사용하여 API 호출 실행
    executeQuery(text, queryMode);
  };

  const handleSubmit = () => submitQuestion(inputValue);

  const handleReset = () => {
    setMessages([]);
    setTypingTextMap({});
    setIsPdfVisible(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const columnClass = "mx-auto w-full max-w-3xl px-4 sm:px-6";

  const hasMessages = messages.length > 0;

  // 모달 관련 상태 및 핸들러
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);

  const handleOpenModal = () => {
    setCurrentStep(1);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    refetchCollectionFiles();
    setTimeout(() => {
      setCurrentStep(1);
    }, 300);
  };

  const handleUploadSuccess = (newFiles: File[]) => {
    setUploadedFiles(newFiles);
    setCurrentStep(2);
  };

  const handleTriggerSuccess = () => {
    setCurrentStep(3);
    refetchCollectionFiles();
  };

  // PDF 뷰어 관련 상태 및 핸들러
  const [isPdfVisible, setIsPdfVisible] = useState(false);
  const [pageNum, setPageNum] = useState(1);
  const [pdfWidth, setPdfWidth] = useState(460);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [currentPdfFileName, setCurrentPdfFileName] = useState<string | null>(
    null
  );

  const handleClosePdf = () => setIsPdfVisible(false);

  const handleCiteClick = async (fileName: string, page: number) => {
    setPageNum(page);
    setIsPdfVisible(true);

    if (currentPdfFileName === fileName && pdfUrl) {
      return;
    }

    try {
      const response = await fetch(`${BASE_URL}/files/download-pdf/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_name: fileName }),
      });
      if (!response.ok) throw new Error("PDF fetch failed");

      const blob = await response.blob();
      if (pdfUrl) URL.revokeObjectURL(pdfUrl);
      const url = URL.createObjectURL(blob);
      setPdfUrl(url);
      setCurrentPdfFileName(fileName);
      setIsPdfVisible(true);
    } catch (err) {
      console.error(err);
    }
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    const startX = e.clientX;
    const startWidth = pdfWidth;

    const handleMouseMove = (e: MouseEvent) => {
      const newWidth = Math.max(280, startWidth + (startX - e.clientX));
      setPdfWidth(newWidth);
    };

    const handleMouseUp = () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
  };

  // --- 렌더링 ---
  return (
    <div className="flex h-screen w-full flex-col bg-ink-50 font-sans">
      {/* 상단 바 */}
      <header className="z-20 shrink-0 border-b border-ink-200 bg-white/90 backdrop-blur">
        <div className="flex items-center justify-between gap-3 px-4 py-2.5 sm:px-6">
          <button
            onClick={() => navigate("/")}
            className="flex items-center gap-1 rounded-lg px-2 py-1.5 text-[13.5px] font-medium text-ink-500 transition-colors hover:bg-ink-100 hover:text-ink-800"
          >
            <ChevronLeft size={18} />
            <span className="hidden sm:inline">홈으로</span>
          </button>

          <div className="flex items-center gap-2">
            <span className="text-[14px] font-bold tracking-tight text-ink-900">
              금융 자문 챗봇
            </span>
            <span className="hidden rounded-full border border-ink-200 bg-ink-50 px-2 py-0.5 text-[11.5px] font-medium text-ink-500 sm:inline">
              전자금융 법령 RAG
            </span>
          </div>

          <button
            onClick={handleReset}
            disabled={!hasMessages}
            className="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-[13.5px] font-medium text-ink-500 transition-colors hover:bg-ink-100 hover:text-ink-800 disabled:pointer-events-none disabled:opacity-40"
          >
            <RotateCcw size={15} />
            <span className="hidden sm:inline">새 대화</span>
          </button>
        </div>
      </header>

      {isModalOpen && (
        <Modal
          currentStep={currentStep}
          uploadedFiles={uploadedFiles}
          onClose={handleCloseModal}
          onUploadSuccess={handleUploadSuccess}
          onTriggerSuccess={handleTriggerSuccess}
        />
      )}

      {hasMessages ? (
        <div className="flex min-h-0 flex-1 flex-row">
          {/* 대화 영역 */}
          <div className="flex min-w-0 flex-1 flex-col">
            <main className="min-h-0 flex-1 overflow-y-auto py-6">
              <div className={`${columnClass} flex flex-col gap-6`}>
                {messages.map((msg) => (
                  <Bubble
                    isLoading={isQueryLoading}
                    onCiteClick={handleCiteClick}
                    key={msg.id}
                    isQuestion={msg.type === "question"}
                    cites={msg.cites || []}
                    msg={msg}
                  />
                ))}
                <div ref={chatEndRef} />
              </div>
            </main>

            <footer className="shrink-0 border-t border-ink-200 bg-white/90 py-3 backdrop-blur">
              <div className={columnClass}>
                <ChatForm
                  inputContainerClass="w-full"
                  textareaRef={textareaRef}
                  inputValue={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyDown}
                  onClick={handleSubmit}
                  handleOpenModal={handleOpenModal}
                  collectionFiles={collectionFiles}
                  handleFileDelete={handleFileDelete}
                  hasMessages={hasMessages}
                  isLoading={isQueryLoading}
                  queryMode={queryMode}
                  setQueryMode={setQueryMode}
                />
              </div>
            </footer>
          </div>

          {/* 원문 PDF 뷰어 */}
          {isPdfVisible && (
            <>
              <div
                className="w-1 shrink-0 cursor-col-resize bg-ink-200 transition-colors hover:bg-brand-400"
                onMouseDown={handleMouseDown}
              />
              <aside
                style={{ width: pdfWidth }}
                className="shrink-0 overflow-y-auto border-l border-ink-200 bg-white p-3"
              >
                {pdfUrl ? (
                  <PdfViewer
                    fileURL={pdfUrl}
                    initialPage={pageNum}
                    onPageChange={setPageNum}
                    onClose={handleClosePdf}
                  />
                ) : (
                  <LoadingSpinner loadingText="PDF를 불러오는 중입니다…" block />
                )}
              </aside>
            </>
          )}
        </div>
      ) : (
        /* 빈 상태 */
        <main className="flex min-h-0 flex-1 flex-col items-center justify-center overflow-y-auto py-8">
          <div className={`${columnClass} w-full`}>
            <div className="mb-8 text-center">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-ink-900 text-white">
                <Sparkles size={22} />
              </div>
              <h1 className="mb-2 text-[28px] font-extrabold tracking-tight text-ink-900">
                무엇을 확인해 드릴까요?
              </h1>
              <p className="text-[14.5px] text-ink-500">
                전자금융거래법 · 감독규정 · 시행세칙을 벡터 검색해 근거 조항과
                함께 답변합니다.
              </p>
            </div>

            <ChatForm
              inputContainerClass="w-full"
              textareaRef={textareaRef}
              inputValue={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              onClick={handleSubmit}
              handleOpenModal={handleOpenModal}
              collectionFiles={collectionFiles}
              handleFileDelete={handleFileDelete}
              hasMessages={hasMessages}
              isLoading={isQueryLoading}
              queryMode={queryMode}
              setQueryMode={setQueryMode}
            />

            <div className="mt-6">
              <p className="mb-2.5 text-[11.5px] font-semibold uppercase tracking-wider text-ink-400">
                예시 질문
              </p>
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {SAMPLE_QUESTIONS.map((question) => (
                  <button
                    key={question}
                    type="button"
                    onClick={() => submitQuestion(question)}
                    className="rounded-xl border border-ink-200 bg-white px-3.5 py-3 text-left text-[13.5px] leading-snug text-ink-600 shadow-card transition-all hover:-translate-y-0.5 hover:border-brand-300 hover:text-ink-900"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </main>
      )}
    </div>
  );
}

export default Chatbot;
