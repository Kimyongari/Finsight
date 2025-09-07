import { useState, useEffect, useRef } from "react";
import ReactMarkdown from 'react-markdown';
import remarkGfm from "remark-gfm";

type Message = {
  id: number;
  type: 'question' | 'answer';
  text: string;
  isStreaming?: boolean;
};

const initialMessages: Message[] = [];

function Chatbot() {
  const getDeviceType = () => {
    const width = window.innerWidth;
    if (width <= 768) return 'mobile';
    if (width <= 1024) return 'tablet';
    return 'desktop';
  };

  const [deviceType, setDeviceType] = useState(getDeviceType());

  useEffect(() => {
    const handleResize = () => setDeviceType(getDeviceType());
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const inputContainerClass = deviceType === 'mobile' ? "w-full" : "w-2/3 mx-auto";
  const messageListClass = deviceType === 'mobile' ? "p-4" : "w-1/2 mx-auto p-4";

  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [inputValue, setInputValue] = useState("");
  const chatEndRef = useRef<null | HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [inputValue]);

  const handleSubmit = async () => {
    if (!inputValue.trim()) return;

    // 로딩 중 메시지
    const loadingAnswerId = Date.now() + 1;
    const loadingAnswer: Message = { id: loadingAnswerId, type: 'answer', text: "답변 생성 중...", isStreaming: true };

    // 로딩 메시지만 상태에 추가
    setMessages(prev => [...prev, loadingAnswer]);
    setInputValue("");

    try {
      // 서버 요청
      const response = await fetch(`http://localhost:8000/report/${inputValue}`, {
        method: "GET"
      });

      if (!response.ok) {
        throw new Error('네트워크 응답이 실패했습니다.');
      }

      const data = await response.json();
      console.log(data);

      // 로딩 메시지를 실제 답변으로 교체
      setMessages(prev => prev.map(msg =>
        msg.id === loadingAnswerId
          ? { ...msg, text: data.answer, isStreaming: false }
          : msg
      ));

    } catch (err) {
      console.error("답변을 가져오는 데 실패했습니다:", err);

      // 에러 발생 시 로딩 메시지를 실패 메시지로 업데이트
      setMessages(prev => prev.map(msg =>
        msg.id === loadingAnswerId
          ? { ...msg, text: "답변을 가져오는 데 실패했습니다.", isStreaming: false }
          : msg
      ));
    }
  };

  const handleNewReport = () => {
    setMessages([]);
  };

  const hasMessages = messages.length > 0;

  const ChatForm = (
    <div className={inputContainerClass}>
      <div className="flex gap-2 mb-2">
        <textarea
          ref={textareaRef}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder={hasMessages ? "추가 질문을 입력하세요." : "기업명을 입력해주세요."}
          className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 transition resize-none overflow-y-hidden"
          rows={1}
        />
        <button
          type="button"
          onClick={handleSubmit}
          className="px-5 py-3 bg-indigo-500 text-white font-bold rounded-lg hover:bg-indigo-600 transform transition-transform duration-200 hover:scale-105 active:scale-95 self-end"
        >
          ⬆
        </button>
      </div>
      <div className="text-center text-xs text-gray-400">
        CorpAdvisor의 답변은 부정확할 수 있습니다. 중요한 정보는 다시 확인해주세요.
      </div>
    </div>
  );

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
                    <div
                      key={msg.id}
                      className={`flex w-full mt-16${isQuestion ? " justify-end" : ""}`}
                    >
                      <div
                        className={`rounded-2xl break-words ${
                          isQuestion
                            ? "p-4 text-justify max-w-[80%] md:max-w-[70%] bg-indigo-50 shadow-sm text-gray-800 rounded-br-none"
                            : "w-full"
                        }`}
                      >
                        <div className="prose max-w-none w-full">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {msg.text}
                          </ReactMarkdown>
                        </div>
                      </div>
                    </div>
                  );
                })}

                {/* 로딩 중 표시 */}
                {messages.length > 0 && messages[messages.length - 1].isStreaming && (
                  <div className="text-center text-gray-400 my-2">
                    답변을 생성 중입니다…
                  </div>
                )}
              </div>
              <div ref={chatEndRef} />
            </div>
          </main>
          <footer className="flex-1 flex-col justify-center items-center bg-white border-t border-gray-200 p-4 fixed bottom-0 left-0 right-0">
            <div className={`${inputContainerClass} mb-3 flex justify-center`}>
              <button
                type="button"
                onClick={handleNewReport}
                className="px-4 py-2 border border-gray-300 text-gray-600 text-sm font-bold rounded-lg hover:bg-gray-100 hover:text-black transition-colors duration-200"
              >
                다른 기업의 보고서 생성하기
              </button>
            </div>
          </footer>
        </>
      ) : (
        <div className={`${deviceType === 'mobile' ? "w-full" : deviceType === 'tablet' ? "w-3/4": "w-1/2"} flex flex-col justify-center items-center h-full gap-6 p-4`}>
          <header className="text-center">
            <h1 className="text-4xl font-bold text-gray-800">기업 보고서 생성</h1>
            <p className="text-gray-500 mt-2">CorpAdvisor</p>
          </header>
          <div className="w-full">{ChatForm}</div>
        </div>
      )}
    </div>
  );
}

export default Chatbot;