// Chatbot.tsx
import { useState, useEffect, useRef } from "react";

import { ChatForm } from "../components/ChatForm.tsx";
import { Bubble } from "../components/Bubble.tsx";
import { Button } from "../components/Button.tsx";
import { Modal } from "../components/Modal.tsx";
import PdfViewer from "../components/PdfViewer.tsx";
// 메시지 타입 정의
type Message = {
  id: number;
  type: "question" | "answer" | "loading";
  text: string;
  isStreaming?: boolean;
};

const initialMessages: Message[] = [];

function Chatbot() {
  // 디바이스 크기
  const getDeviceType = () => {
    const width = window.innerWidth;
    if (width <= 768) return "mobile";
    if (width <= 1024) return "tablet";
    return "desktop";
  };

  const [deviceType, setDeviceType] = useState(getDeviceType());

  // 메시지, 타이핑 효과 관련 상태
  const [typingTextMap, setTypingTextMap] = useState<{ [id: number]: string }>(
    {}
  );
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const handleResize = () => setDeviceType(getDeviceType());
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const inputContainerClass =
    deviceType === "mobile" ? "w-full" : "w-2/3 mx-auto";
  const messageListClass =
    deviceType === "mobile" ? "p-4" : "w-1/2 mx-auto p-4";

  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [inputValue, setInputValue] = useState("");
  const chatEndRef = useRef<null | HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [inputValue]);

  const handleSubmit = async () => {
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
      text: "답변을 생각 중입니다. 조금만 기다려주세요.",
      isStreaming: true,
    };

    setMessages((prev) => [...prev, newQuestion, loadingAnswer]); // 질문과 빈 답변 메시지를 추가

    setInputValue("");
    setIsLoading(true); // 로딩 시작
    try {
      const response = await fetch("http://127.0.0.1:8000/rag/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: newQuestion.text }),
      });
      const data = await response.json();
      console.log("답변 데이터:", data);
      setTypingTextMap((prev) => ({ ...prev, [loadingAnswerId]: data.answer })); // 전체 답변 텍스트를 임시 상태에 저장, 타이핑 효과
    } catch (err) {
      console.error("답변을 가져오는 데 실패했습니다:", err);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === loadingAnswerId
            ? {
                ...msg,
                text: "답변을 가져오는 데 실패했습니다.",
                isStreaming: false,
              }
            : msg
        )
      );
    } finally {
      // 성공이든 실패든 입력창 다시 활성화
      setIsLoading(false);
    }
  };
  // --- 타자 치기 효과 적용 ---
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
          // 타이핑이 끝나면 isStreaming을 false로 변경
          setIsLoading(false);

          setTypingTextMap((prev) => {
            const { [id]: _, ...rest } = prev;
            return rest;
          });
        }
      }, 15);

      return () => clearInterval(intervalId);
    });
  }, [typingTextMap]); // typingText 상태가 변경될 때만 이펙트 실행

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // 모달 관련 상태
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleOpenModal = () => {
    setCurrentStep(1);
    setIsModalOpen(true);
  };
  const handleCloseModal = () => {
    setIsModalOpen(false);
    // 모달을 다시 열 때 항상 1단계부터 시작하도록 초기화
    setTimeout(() => {
      setCurrentStep(1);
    }, 300); // 모달 닫기 애니메이션 시간 고려
  };

  // Stepper를 위한 상태
  const [currentStep, setCurrentStep] = useState(1);
  const [totalUploadedFiles, settotalUploadedFiles] = useState<File[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]); // 업로드된 파일들
  // 1단계 -> 2단계로 넘어가는 함수
  const handleUploadSuccess = (newFiles: File[]) => {
    settotalUploadedFiles((prevFiles) => [...prevFiles, ...newFiles]); // 모달 창 끄고 새로 업로드 시 누적
    setUploadedFiles(newFiles); // 추가로 업로드된 파일들 상태 업데이트
    setCurrentStep(2);
  };

  // 2단계 -> 3단계로 넘어가는 함수
  const handleTriggerSuccess = () => {
    setCurrentStep(3);
  };

  // 모달 렌더링
  const renderModal = () => (
    <Modal
      currentStep={currentStep}
      uploadedFiles={uploadedFiles}
      onClose={handleCloseModal}
      onUploadSuccess={handleUploadSuccess}
      onTriggerSuccess={handleTriggerSuccess}
    />
  );

  // 챗팅 창 렌더링
  const renderChatForm = () => (
    <ChatForm
      inputContainerClass={inputContainerClass}
      textareaRef={textareaRef}
      inputValue={inputValue}
      onChange={(e) => setInputValue(e.target.value)}
      onKeyDown={handleKeyDown}
      onClick={handleSubmit}
      loadingPlaceholder="답변 생성 중입니다."
      defaultPlaceholder="금융과 관련한 질문을 입력해주세요."
      afterSubmitPlaceholder="추가 질문을 입력하세요."
      hasMessages={hasMessages}
      isLoading={isLoading}
    />
  );

  const hasMessages = messages.length > 0;

  return (
    <div className="w-full flex flex-col justify-center items-center h-screen bg-white font-sans">
      {hasMessages ? (
        <>
          <main className="w-full flex-1 overflow-y-auto pb-32">
            <div className={messageListClass}>
              <div className="space-y-4">
                {messages.map((msg) => {
                  const isQuestion = msg.type === "question";
                  return (
                    <Bubble key={msg.id} isQuestion={isQuestion} msg={msg} />
                  );
                })}
              </div>
              <div ref={chatEndRef} />
            </div>
          </main>
          <footer className="w-full bg-white border-t border-gray-200 p-4 fixed bottom-0 left-0 right-0">
            {renderChatForm()}
            <PdfViewer />
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
          <div>
            {totalUploadedFiles.length > 0 ? (
              <p className="text-gray-600">
                {totalUploadedFiles.length}개의 파일이 업로드되었습니다.
              </p>
            ) : (
              <p className="text-gray-600">업로드된 파일이 없습니다.</p>
            )}
          </div>
          <Button
            ButtonText="다른 데이터 업로드"
            onClick={handleOpenModal}
          ></Button>
          {isModalOpen && renderModal()}
          <div className="w-full">{renderChatForm()}</div>
        </div>
      )}
    </div>
  );
}

export default Chatbot;
