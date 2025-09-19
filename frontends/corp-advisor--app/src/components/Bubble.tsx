import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

// 메시지 타입 정의
type Message = {
  id: number;
  type: "question" | "answer" | "loading";
  text: string;
  isStreaming?: boolean;
};

// 출처
type RetrievedDoc = {
  name: string;
  n_page: number;
};

type BubbleProps = {
  isQuestion: boolean;
  answerClass?: string;
  cites: RetrievedDoc[];
  msg: Message;
};

export function Bubble({
  isQuestion,
  answerClass = `rounded-2xl break-words p-4 text-justify shadow-sm ${
    isQuestion
      ? "text-gray-800 max-w-[80%] md:max-w-[70%] bg-indigo-50 rounded-br-none"
      : "max-w-[90%] md:max-w-[80%] border-gray-100 text-gray-800 border border-solid rounded-bl-none"
  }`,
  cites,
  msg,
}: BubbleProps) {
  return (
    <div
      key={msg.id}
      className={`flex w-full ${isQuestion ? "justify-end" : ""}`}
    >
      <div className={answerClass}>
        {isQuestion ? (
          msg.text
        ) : (
          <>
            <div className="prose max-w-none w-full">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {msg.text + (msg.isStreaming ? "\n" : "")}
              </ReactMarkdown>
            </div>
            <div>
              {cites.map((cite) => (
                <div>{cite.name}</div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
