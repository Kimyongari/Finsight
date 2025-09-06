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

// 스트리밍으로 보여줄 가짜 답변 데이터 (마크다운 형식 포함)
const fakeGeminiResponse = `
# 삼성전자 2024년 3분기 실적 요약

### 삼성전자의 3분기 실적은 시장 예상치를 상회하는 인상적인 결과를 보여주었습니다.

* **반도체 (DS) 부문:** AI 칩 수요 증가와 메모리 가격 안정화로 흑자 전환에 성공했습니다.
* **모바일 (MX) 부문:** 새로운 폴더블 폰 시리즈의 판매 호조로 견조한 실적을 이어갔습니다.

|표|테스트|테스트|테스트|
|--|---|---|---|
|테스트|테스트|테스트|테스트|
|테스트|테스트|테스트|테스트|
|테스트|테스트|테스트|테스트|
|테스트|테스트|테스트|테스트|

1. 결론:** AI 시장의 성장과 함께 반도체 부문의 회복세가 뚜렷하며, 향후 전망도 긍정적입니다.

2. 결론:** AI 시장의 성장과 함께 반도체 부문의 회복세가 뚜렷하며, 향후 전망도 긍정적입니다.

- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)
- [네이버](https://www.naver.com)


`;

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
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [inputValue]);

  // --- 스트리밍 로직 수정 ---
  const lastMessage = messages[messages.length - 1];

  useEffect(() => {
    // 마지막 메시지가 스트리밍 중인 'answer'일 때만 타이핑 효과한 번만 실행
    if (lastMessage?.type === 'answer' && lastMessage.isStreaming) {
      let charIndex = 0;
      const intervalId = setInterval(() => {
        if (charIndex < fakeGeminiResponse.length) {
          const nextChar = fakeGeminiResponse.charAt(charIndex);
          // 함수형 업데이트를 사용하여 항상 최신 상태를 기반으로 텍스트 추가
          setMessages(prev =>
            prev.map(msg =>
              msg.id === lastMessage.id ? { ...msg, text: msg.text + nextChar } : msg
            )
          );
          charIndex++;
        } else {
          // 스트리밍 종료
          clearInterval(intervalId);
          setMessages(prev =>
            prev.map(msg =>
              msg.id === lastMessage.id ? { ...msg, isStreaming: false } : msg
            )
          );
        }
      }, 25); // 타이핑 속도 (ms)

      return () => clearInterval(intervalId);
    }
    // 의존성 배열을 수정하여, 새로운 답변이 시작될 때만 이 useEffect가 실행되도록 함
  }, [lastMessage?.id, lastMessage?.isStreaming]);


  const handleSubmit = () => {
    if (inputValue.trim()) {
      const newQuestion: Message = { id: Date.now(), type: "question", text: inputValue };
      const newAnswerPlaceholder: Message = { id: Date.now() + 1, type: "answer", text: "", isStreaming: true };
      
      setMessages(prev => [...prev, newQuestion, newAnswerPlaceholder]);
      
      setInputValue("");
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      handleSubmit();
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
          onKeyDown={handleKeyDown}
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
                    <div key={msg.id} className={`flex w-full ${isQuestion ? "justify-end" : ""}`}>
                      <div className={`rounded-2xl break-words ${isQuestion ? "p-4 text-justify max-w-[80%] md:max-w-[70%] bg-indigo-50 shadow-sm text-gray-800 rounded-br-none" : "w-full"}`}>
                        {isQuestion ? (
                          msg.text
                        ) : (
                          <div className="prose max-w-none w-full">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                              {msg.text + (msg.isStreaming ? '\n' : '')}
                            </ReactMarkdown>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
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

