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
  isLoading: boolean;
  msg: Message;
  onCiteClick: (fileName: string, page: number) => void;
};

export function Bubble({
  isQuestion,
  answerClass = `rounded-2xl break-words p-4 text-justify shadow-sm ${
    isQuestion
      ? "text-gray-800 max-w-[80%] md:max-w-[70%] bg-indigo-50 rounded-br-none"
      : "max-w-[90%] md:max-w-[80%] border-gray-100 text-gray-800 border border-solid rounded-bl-none"
  }`,
  cites,
  isLoading,
  msg,
  onCiteClick,
}: BubbleProps) {
  const [visibleKey, setVisibleKey] = useState<string | null>(null);
  const renderContent = () => {
    const handleTextVisible = (key: string) => {
      setVisibleKey((prev) => (prev === key ? null : key));
    };

    if (typeof msg.text === "string") {
      return (
        <>
          <div className="prose max-w-none w-full mb-4">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {msg.text + (msg.isStreaming ? "\n" : "")}
            </ReactMarkdown>
          </div>
          {!msg.isStreaming && (
            <>
              <hr />
              <div className="flex flex-col gap-2 text-sm mt-4">
                {cites.map((cite, index) => {
                  const key = `${cite.name}-${cite.i_page}-${index}`;
                  return (
                    <div key={key}>
                      <button
                        onClick={() => {
                          onCiteClick(cite.file_name, cite.i_page);
                          handleTextVisible(key);
                        }}
                        className="text-left bg-gray-200"
                      >
                        {cite.name}
                      </button>
                      {visibleKey === key && !isLoading && (
                        <div
                          className="mt-2 border p-2 rounded-md bg-gray-50 border-gray-50"
                          style={{ whiteSpace: "pre-wrap" }}
                        >
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
