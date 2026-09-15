import React, { useEffect, useRef, useState } from "react";
import { FooterText } from "./FooterText";
import { Paperclip, ArrowUp, Trash2, FileText, Plus } from "lucide-react";
import { RAGDropdown } from "./RAGDropdown";
import type { CollectionFile } from "../hooks/useCollectionFiles";
import { useDeleteFile } from "../hooks/useDeleteFile";
import type { QueryMode } from "../hooks/useDynamicQuery";

type ChatFormProps = {
  inputContainerClass: string;
  textareaRef: React.RefObject<HTMLTextAreaElement | null>;
  inputValue: string;
  onChange: React.ChangeEventHandler<HTMLTextAreaElement>;
  onKeyDown: React.KeyboardEventHandler<HTMLTextAreaElement>;
  onClick: React.MouseEventHandler<HTMLButtonElement>;
  handleOpenModal: () => void;
  loadingPlaceholder?: string;
  defaultPlaceholder?: string;
  afterSubmitPlaceholder?: string;
  collectionFiles: CollectionFile[];
  handleFileDelete: (fileName: string) => void;
  hasMessages: boolean;
  isLoading: boolean;
  queryMode: QueryMode;
  setQueryMode: (mode: QueryMode) => void;
};

export function ChatForm({
  inputContainerClass,
  textareaRef,
  inputValue,
  onChange,
  onKeyDown,
  onClick,
  handleOpenModal,
  loadingPlaceholder = "답변을 생성하고 있습니다…",
  defaultPlaceholder = "전자금융 법령·감독규정에 대해 무엇이든 질문해주세요.",
  afterSubmitPlaceholder = "추가 질문을 입력하세요.",
  collectionFiles,
  handleFileDelete,
  hasMessages,
  isLoading,
  queryMode,
  setQueryMode,
}: ChatFormProps) {
  const [showFilePanel, setShowFilePanel] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const { deleteFile } = useDeleteFile();

  // 패널 외부 클릭 시 닫기
  useEffect(() => {
    if (!showFilePanel) return;
    const handleClickOutside = (event: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(event.target as Node)) {
        setShowFilePanel(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [showFilePanel]);

  const placeholder =
    isLoading && inputValue === ""
      ? loadingPlaceholder
      : hasMessages
      ? afterSubmitPlaceholder
      : defaultPlaceholder;

  const canSend = !isLoading && inputValue.trim().length > 0;

  return (
    <div className={inputContainerClass}>
      {/* 모드 선택 */}
      <div className="mb-2.5">
        <RAGDropdown
          value={queryMode}
          onSelect={setQueryMode}
          disabled={isLoading}
        />
      </div>

      {/* 입력창 */}
      <div className="rounded-2xl border border-ink-200 bg-white p-2 shadow-card transition-colors focus-within:border-brand-400 focus-within:ring-2 focus-within:ring-brand-100">
        <textarea
          rows={1}
          ref={textareaRef}
          value={inputValue}
          onChange={onChange}
          onKeyDown={onKeyDown}
          placeholder={placeholder}
          disabled={isLoading}
          className="max-h-40 w-full resize-none border-none bg-transparent px-3 py-2 text-[15px] leading-relaxed text-ink-800 placeholder:text-ink-400 focus:outline-none disabled:text-ink-400"
        />

        <div className="flex items-center justify-between gap-2 px-1 pb-0.5 pt-1">
          {/* 지식베이스 파일 */}
          <div className="relative" ref={panelRef}>
            <button
              type="button"
              onClick={() => setShowFilePanel((prev) => !prev)}
              className="flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-[13px] font-medium text-ink-500 transition-colors hover:bg-ink-100 hover:text-ink-700"
            >
              <Paperclip size={15} />
              지식베이스
              <span className="rounded-full bg-ink-100 px-1.5 py-0.5 text-[11px] font-bold text-ink-500">
                {collectionFiles?.length ?? 0}
              </span>
            </button>

            {showFilePanel && (
              <div
                className={`absolute left-0 z-20 w-[22rem] rounded-xl border border-ink-200 bg-white p-2 shadow-lift ${
                  hasMessages ? "bottom-full mb-2" : "top-full mt-2"
                }`}
              >
                <p className="px-2 py-1.5 text-[11.5px] font-semibold uppercase tracking-wider text-ink-400">
                  적재된 문서
                </p>
                <ul className="mb-1 max-h-56 overflow-y-auto">
                  {collectionFiles && collectionFiles.length > 0 ? (
                    collectionFiles.map((file) => (
                      <li
                        key={file.file_name}
                        className="group flex items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-ink-50"
                      >
                        <FileText
                          size={14}
                          className="shrink-0 text-ink-400"
                        />
                        <span
                          className="flex-1 truncate text-[13px] text-ink-700"
                          title={file.file_name}
                        >
                          {file.file_name}
                        </span>
                        {typeof file.chunk_count === "number" && (
                          <span className="shrink-0 text-[11px] text-ink-400">
                            {file.chunk_count} chunks
                          </span>
                        )}
                        <button
                          type="button"
                          aria-label={`${file.file_name} 삭제`}
                          onClick={() => {
                            deleteFile(file.file_name);
                            handleFileDelete(file.file_name);
                          }}
                          className="shrink-0 rounded p-1 text-ink-300 opacity-0 transition-opacity hover:bg-red-50 hover:text-red-500 group-hover:opacity-100"
                        >
                          <Trash2 size={13} />
                        </button>
                      </li>
                    ))
                  ) : (
                    <li className="px-2 py-3 text-[13px] text-ink-400">
                      업로드된 파일이 없습니다.
                    </li>
                  )}
                </ul>
                <button
                  type="button"
                  onClick={() => {
                    handleOpenModal();
                    setShowFilePanel(false);
                  }}
                  className="flex w-full items-center gap-1.5 rounded-lg border-t border-ink-100 px-2 pb-1 pt-2.5 text-[13px] font-semibold text-brand-600 hover:text-brand-700"
                >
                  <Plus size={14} />
                  PDF 추가 업로드
                </button>
              </div>
            )}
          </div>

          {/* 전송 */}
          <button
            type="button"
            onClick={onClick}
            disabled={!canSend}
            aria-label="질문 전송"
            className={`flex h-9 w-9 items-center justify-center rounded-xl transition-all duration-150 ${
              canSend
                ? "bg-brand-600 text-white hover:bg-brand-700 active:scale-95"
                : "cursor-not-allowed bg-ink-200 text-ink-400"
            }`}
          >
            <ArrowUp size={18} strokeWidth={2.4} />
          </button>
        </div>
      </div>

      <div className="mt-2">
        <FooterText footerText="FinSight의 답변은 부정확할 수 있습니다. 중요한 정보는 원문 법령을 다시 확인해주세요." />
      </div>
    </div>
  );
}
