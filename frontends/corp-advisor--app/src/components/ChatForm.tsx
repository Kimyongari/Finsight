import React, {useState} from "react";
import {Button} from "../components/Button.tsx";
import {FooterText} from "./FooterText";

type ChatFormProps = {
  inputContainerClass: string;
  textareaRef: React.RefObject < HTMLTextAreaElement | null >;
  inputValue: string;
  onChange: React.ChangeEventHandler<HTMLTextAreaElement>;
  onKeyDown: React.KeyboardEventHandler<HTMLTextAreaElement>;
  onClick: React.MouseEventHandler<HTMLButtonElement>;
  handleOpenModal: () => void;
  loadingPlaceholder?: string;
  defaultPlaceholder?: string;
  afterSubmitPlaceholder?: string;
  hasMessages: boolean;
  totalUploadedFiles: File[];
  isLoading: boolean;
};

export function ChatForm({
  inputContainerClass,
  textareaRef,
  inputValue,
  onChange,
  onKeyDown,
  onClick,
  handleOpenModal,
  loadingPlaceholder = "답변 생성 중입니다.",
  defaultPlaceholder = "금융과 관련해 질문해주세요.",
  afterSubmitPlaceholder = "추가 질문을 입력하세요.",
  hasMessages,
  totalUploadedFiles,
  isLoading
} : ChatFormProps) {
  const [showUploadText, setShowUploadText] = useState(false);

  const placeholder = isLoading && inputValue === ""
    ? loadingPlaceholder
    : hasMessages
      ? afterSubmitPlaceholder
      : defaultPlaceholder;

  return (<div className={inputContainerClass}>
    <div className="flex gap-2 mb-2">
      <div className="flex flex-1 gap-2 border rounded-lg">
        <textarea ref={textareaRef} value={inputValue} onChange={onChange} onKeyDown={onKeyDown} placeholder={placeholder} disabled={isLoading} className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 transition resize-none overflow-y-hidden border-none" rows={1}/>{" "}
        {/* 파일 아이콘 클릭 시 문구 토글 */}
        <div className="relative">
          <button type="button" onClick={() => setShowUploadText((prev) => !prev)} className="p-3 bg-white rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 transition resize-none overflow-y-hidden border-none">
            📤
          </button>

          {
            showUploadText && (<div className="w-64 text-center absolute left-0 bg-white border border-gray-300 rounded shadow-md p-2 cursor-pointer" onClick={() => {
                handleOpenModal();
                setShowUploadText(false);
              }}>
              <div className="mb-2 py-2 border-b">
                {
                  totalUploadedFiles.length > 0
                    ? (<p className="text-gray-600">
                      {totalUploadedFiles.length}개의 파일이 업로드되었습니다.
                    </p>)
                    : (<p className="text-gray-600">업로드된 파일이 없습니다.</p>)
                }
              </div>
              다른 데이터 업로드 하기
            </div>)
          }
        </div>
      </div>
      {/* 전송 버튼 */}
      <button type="button" onClick={onClick} disabled={isLoading} className={`px-5 py-3 text-white font-bold rounded-lg self-end ${
        isLoading
          ? "bg-gray-700 cursor-not-allowed"
          : "bg-indigo-500 hover:bg-indigo-600 transform transition-transform duration-200 hover:scale-105 active:scale-95"}`}>
        ⬆
      </button>
    </div>
    <FooterText footerText="CorpAdvisor의 답변은 부정확할 수 있습니다. 중요한 정보는 다시 확인해주세요."/>
  </div>);
}
