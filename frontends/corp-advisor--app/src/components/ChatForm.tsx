import React from "react";
import { FooterText } from "./FooterText";

type ChatFormProps = {
  inputContainerClass: string;
  textareaRef: React.RefObject<HTMLTextAreaElement | null>;
  inputValue: string;
  onChange: React.ChangeEventHandler<HTMLTextAreaElement>;
  onKeyDown: React.KeyboardEventHandler<HTMLTextAreaElement>;
  onClick: React.MouseEventHandler<HTMLButtonElement>;
  loadingPlaceholder?: string;
  defaultPlaceholder?: string;
  afterSubmitPlaceholder?: string;
  hasMessages: boolean;
  isLoading: boolean;
};

export function ChatForm({
  inputContainerClass,
  textareaRef,
  inputValue,
  onChange,
  onKeyDown,
  onClick,
  loadingPlaceholder = "답변 생성 중입니다.",
  defaultPlaceholder = "금융과 관련해 질문해주세요.",
  afterSubmitPlaceholder = "추가 질문을 입력하세요.",
  hasMessages,
  isLoading,
}: ChatFormProps) {
  // placeholder 로직: 로딩 중 + 입력창 비어있을 때만 로딩 메시지
  const placeholder =
    isLoading && inputValue === ""
      ? loadingPlaceholder
      : hasMessages
      ? afterSubmitPlaceholder
      : defaultPlaceholder;

  return (
    <div className={inputContainerClass}>
      <div className="flex gap-2 mb-2">
        <textarea
          ref={textareaRef}
          value={inputValue}
          onChange={onChange}
          onKeyDown={onKeyDown}
          placeholder={placeholder}
          disabled={isLoading} // 로딩 중 입력창 비활성화
          className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 transition resize-none overflow-y-hidden"
          rows={1}
        />
        <button
          type="button"
          onClick={onClick}
          disabled={isLoading} // 로딩 중 버튼 비활성화
          className={`px-5 py-3 text-white font-bold rounded-lg self-end ${
            isLoading
              ? "bg-gray-700 cursor-not-allowed"
              : "bg-indigo-500 hover:bg-indigo-600 transform transition-transform duration-200 hover:scale-105 active:scale-95"
          }`}
        >
          ⬆
        </button>
      </div>
      <FooterText footerText="CorpAdvisor의 답변은 부정확할 수 있습니다. 중요한 정보는 다시 확인해주세요." />
    </div>
  );
}
