import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Message } from "../ChatContext";
// 출처
type RetrievedDoc = {
  name: string;
  i_page: number;
  file_path: string;
};

type BubbleProps = {
  isQuestion: boolean;
  answerClass?: string;
  cites: RetrievedDoc[];
  msg: Message;
  onCiteClick: (page: number) => void;
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
  onCiteClick,
}: BubbleProps) {
  const renderContent = () => {
    // 문자열이면 ReactMarkdown 사용, JSX이면 그대로 렌더링
    const [textVisibleMap, setTextVisibleMap] = useState<{
      [key: string]: boolean;
    }>({});

    const handleTextVisible = (key: string) => {
      setTextVisibleMap((prev) => ({
        ...prev,
        [key]: !prev[key], // 기존 값이 true면 false로, false면 true로 토글
      }));
    };

    if (typeof msg.text === "string") {
      return (
        <>
          <div className="prose max-w-none w-full">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {msg.text + (msg.isStreaming ? "\n" : "")}
            </ReactMarkdown>
          </div>
          {!msg.isStreaming && (
            <>
              <hr />
              <div className="flex flex-col gap-2 text-sm">
                {cites.map((cite) => {
                  const key = cite.name + cite.i_page;
                  return (
                    <div key={key}>
                      <button
                        onClick={() => {
                          onCiteClick(cite.i_page);
                          handleTextVisible(key);
                        }}
                        className="text-left"
                      >
                        {cite.name}
                      </button>
                      {textVisibleMap[key] && (
                        <div style={{ whiteSpace: "pre-wrap" }}>
                          {cite.text}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </>
      );
    } else {
      // JSX 요소면 그대로 렌더링
      return msg.text;
    }
  };

  return (
    <div
      key={msg.id}
      className={`flex w-full ${isQuestion ? "justify-end" : ""}`}
    >
      <div className={answerClass}>
        {isQuestion ? msg.text : renderContent()}
      </div>
    </div>
  );
}
