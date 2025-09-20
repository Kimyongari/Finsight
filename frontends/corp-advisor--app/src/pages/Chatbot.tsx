// Chatbot.tsx
import { useState, useEffect, useRef } from "react";

import { ChatForm } from "../components/ChatForm";
import { Bubble } from "../components/Bubble";
import { Modal } from "../components/steps/Modal";
import { PdfViewer } from "../components/PdfViewer";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { Message, CollectionFile } from "../types"; // Message, CollectionFile 타입을 types/index.ts 등에서 가져오도록 수정
import { useCollectionFiles } from "../hooks/useCollectionFiles";
import { useDynamicQuery, QueryMode } from "../hooks/useDynamicQuery";

// 출처
type RetrievedDoc = {
  name: string;
  i_page: number;
  file_path: string;
};

const initialMessages: Message[] = [];

function Chatbot() {
  const exampleDocs: RetrievedDoc[] = [];
  const [retrievedDocs, setRetrievedDocs] =
    useState<RetrievedDoc[]>(exampleDocs);

  // --- 상태 및 훅 정의 ---

  // 1. 서버에 저장된 파일 목록 관리
  const { files: fetchedFiles, refetch: refetchCollectionFiles } =
    useCollectionFiles();
  const [collectionFiles, setCollectionFiles] = useState<CollectionFile[]>([]);

  // 2. 메시지 및 채팅 관련 상태
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [inputValue, setInputValue] = useState("");
  const [typingTextMap, setTypingTextMap] = useState<{ [id: number]: string }>(
    {}
  );

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
  const [deviceType, setDeviceType] = useState(getDeviceType());
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
      setRetrievedDocs(queryData.retrieved_documents || exampleDocs);
      setTypingTextMap((prev) => ({
        ...prev,
        [pendingMessageId]: queryData.answer,
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
                text: "답변을 가져오는 데 실패했습니다.",
                isStreaming: false,
              }
            : msg
        )
      );
      setPendingMessageId(null);
    }
  }, [queryError, pendingMessageId]);

  // 타자 치기 효과 적용
  useEffect(() => {
    Object.entries(typingTextMap).forEach(([idStr, fullText]) => {
      const id = Number(idStr);
      let currentText = "";
      let charIndex = 0;
      const intervalId = setInterval(() => {
        if (charIndex < fullText.length) {
          currentText += fullText.charAt(charIndex);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === id ? { ...msg, text: currentText } : msg
            )
          );
          charIndex++;
        } else {
          clearInterval(intervalId);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === id
                ? { ...msg, isStreaming: false, type: "answer" }
                : msg
            )
          );
          setTypingTextMap((prev) => {
            const { [id]: _, ...rest } = prev;
            return rest;
          });
        }
      }, 10); // 1ms는 너무 빠르므로 10ms 정도로 조정

      return () => clearInterval(intervalId);
    });
  }, [typingTextMap]);

  // 창 크기 변경 감지
  useEffect(() => {
    const handleResize = () => setDeviceType(getDeviceType());
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

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

  const handleSubmit = () => {
    if (!inputValue.trim()) return;

    const newQuestion: Message = {
      id: Date.now(),
      type: "question",
      text: inputValue,
    };

    const loadingAnswerId = Date.now() + 1;
    const loadingAnswer: Message = {
      id: loadingAnswerId,
      type: "loading",
      text: (
        <LoadingSpinner loadingText="답변을 생성 중입니다. 잠시만 기다려주세요." />
      ),
      isStreaming: true,
    };

    setMessages((prev) => [...prev, newQuestion, loadingAnswer]);
    setInputValue("");
    setIsPdfVisible(false);
    setPendingMessageId(loadingAnswerId);

    // 훅을 사용하여 API 호출 실행
    executeQuery(newQuestion.text, queryMode);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // 디바이스 크기 계산 함수
  function getDeviceType() {
    const width = window.innerWidth;
    if (width <= 768) return "mobile";
    if (width <= 1024) return "tablet";
    return "desktop";
  }

  const inputContainerClass = "w-full";

  const messageListClass =
    deviceType === "mobile" ? "p-4" : "w-1/2 mx-auto p-4";

  const hasMessages = messages.length > 0;

  // 모달 관련 상태 및 핸들러
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [totalUploadedFiles, setTotalUploadedFiles] = useState<File[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);

  const handleOpenModal = () => {
    setCurrentStep(1);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setTimeout(() => {
      setCurrentStep(1);
    }, 300);
  };

  const handleUploadSuccess = (newFiles: File[]) => {
    setTotalUploadedFiles((prevFiles) => [...prevFiles, ...newFiles]);
    setUploadedFiles(newFiles);
    setCurrentStep(2);
  };

  const handleTriggerSuccess = () => {
    setCurrentStep(3);
  };

  // PDF 뷰어 관련 상태 및 핸들러
  const [isPdfVisible, setIsPdfVisible] = useState(false);
  const [pageNum, setPageNum] = useState(1);
  const [pdfWidth, setPdfWidth] = useState(400);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);

  const handleClosePdf = () => setIsPdfVisible(false);

  const handleCiteClick = async (fileName: string, page: number) => {
    if (pageNum !== page || !isPdfVisible) {
      setPageNum(page);
      setIsPdfVisible(true);
    } else if (pageNum === page && pdfUrl) {
      setIsPdfVisible((prev) => !prev);
      return;
    }

    try {
      const response = await fetch("http://localhost:8000/files/download-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_name: fileName }),
      });
      if (!response.ok) throw new Error("PDF fetch failed");

      const blob = await response.blob();
      if (pdfUrl) URL.revokeObjectURL(pdfUrl);
      const url = URL.createObjectURL(blob);
      setPdfUrl(url);
      setIsPdfVisible(true);
    } catch (err) {
      console.error(err);
    }
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    const startX = e.clientX;
    const startWidth = pdfWidth;

    const handleMouseMove = (e: MouseEvent) => {
      const newWidth = Math.max(200, startWidth + (startX - e.clientX));
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
    <div className="w-full flex flex-col justify-center items-center h-screen bg-white font-sans">
      {hasMessages ? (
        <>
          <main
            className={`w-full flex gap-4 ${
              isPdfVisible ? "flex-row" : "flex-col"
            } flex-1`}
          >
            <div
              className={`${messageListClass} gap-4 scrollbar-hide flex-1 flex flex-col p-4 space-y-* max-h-[calc(100vh-4rem)] overflow-auto`}
            >
              {messages.map((msg) => (
                <Bubble
                  isLoading={isQueryLoading}
                  onCiteClick={handleCiteClick}
                  key={msg.id}
                  isQuestion={msg.type === "question"}
                  cites={retrievedDocs}
                  msg={msg}
                />
              ))}
              <div ref={chatEndRef} />
            </div>

            {isPdfVisible && (
              <>
                <div
                  className="w-1 bg-gray-300 cursor-col-resize"
                  onMouseDown={handleMouseDown}
                />
                <div
                  style={{ width: pdfWidth }}
                  className="scrollbar-hide max-h-[calc(100vh-4rem)] overflow-auto bg-gray-100 p-2"
                >
                  {pdfUrl ? (
                    <PdfViewer
                      fileURL={pdfUrl}
                      initialPage={pageNum}
                      onPageChange={setPageNum}
                      onClose={handleClosePdf}
                    />
                  ) : (
                    <LoadingSpinner loadingText="PDF를 로딩 중입니다..." />
                  )}
                </div>
              </>
            )}
          </main>
          <footer className="w-full bg-white border-t border-gray-200 p-2 fixed bottom-0 left-0 right-0">
            <ChatForm
              inputContainerClass={inputContainerClass}
              textareaRef={textareaRef}
              inputValue={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              onClick={handleSubmit}
              handleOpenModal={handleOpenModal}
              collectionFiles={collectionFiles}
              handleFileDelete={handleFileDelete}
              hasMessages={hasMessages}
              isLoading={isQueryLoading} // 훅의 로딩 상태를 사용
              queryMode={queryMode}
              setQueryMode={setQueryMode}
            />
          </footer>
        </>
      ) : (
        <div
          className={`${
            deviceType === "mobile"
              ? "w-full"
              : deviceType === "tablet"
              ? "w-3/4"
              : "w-1/2"
          } flex flex-col justify-center items-center h-full gap-6 p-4`}
        >
          <header className="text-center">
            <h1 className="text-4xl font-bold text-gray-800">금융 자문 챗봇</h1>
            <p className="text-gray-500 mt-2">CorpAdvisor</p>
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
          <ChatForm
            inputContainerClass={inputContainerClass}
            textareaRef={textareaRef}
            inputValue={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onClick={handleSubmit}
            handleOpenModal={handleOpenModal}
            collectionFiles={collectionFiles}
            handleFileDelete={handleFileDelete}
            hasMessages={hasMessages}
            isLoading={isQueryLoading} // 훅의 로딩 상태를 사용
            queryMode={queryMode}
            setQueryMode={setQueryMode}
          />
        </div>
      )}
    </div>
  );
}

export default Chatbot;
