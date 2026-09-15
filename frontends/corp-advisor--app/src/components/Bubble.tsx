import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { FileText, Globe, ChevronDown, Sparkles } from "lucide-react";
import type { Message } from "../ChatContext";

// 출처
type RetrievedDoc = {
  name?: string;
  title?: string;
  i_page?: number;
  file_path?: string;
  file_name?: string;
  text?: string;
  content?: string;
  link?: string;
};

type BubbleProps = {
  isQuestion: boolean;
  answerClass?: string;
  cites: RetrievedDoc[];
  isLoading: boolean;
  msg: Message;
  onCiteClick: (fileName: string, page: number) => void;
};

/** 조문 이름을 읽기 좋게 분리한다: "전자금융감독규정제14조의2(...)" → 법령명 / 조문명 */
function splitClauseName(name: string): { law: string; clause: string } {
  const match = name.match(/^(.*?)(제\s*\d+조(?:의\s*\d+)?.*)$/);
  if (match) {
    return { law: match[1].trim(), clause: match[2].trim() };
  }
  return { law: "", clause: name };
}

const markdownComponents = {
  a: ({ node, ...props }: any) => (
    <a {...props} target="_blank" rel="noopener noreferrer" />
  ),
  // 넓은 표가 레이아웃을 밀어내지 않도록 감싼다
  table: ({ node, ...props }: any) => (
    <div className="md-scroll">
      <table {...props} />
    </div>
  ),
};

export function Bubble({
  isQuestion,
  answerClass,
  cites,
  isLoading,
  msg,
  onCiteClick,
}: BubbleProps) {
  const [visibleKey, setVisibleKey] = useState<string | null>(null);

  const handleTextVisible = (key: string) => {
    setVisibleKey((prev) => (prev === key ? null : key));
  };

  // ---------- 사용자 질문 ----------
  if (isQuestion) {
    return (
      <div className="flex w-full animate-fade-up justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-br-md bg-brand-600 px-4 py-2.5 text-[15px] leading-relaxed text-white shadow-sm">
          {msg.text}
        </div>
      </div>
    );
  }

  // ---------- 답변 ----------
  const renderBody = () => {
    if (typeof msg.text !== "string") {
      // 로딩 스피너 등 JSX는 그대로 렌더링
      return msg.text;
    }

    return (
      <>
        <div className="md-body">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={markdownComponents}
          >
            {msg.text}
          </ReactMarkdown>
          {msg.isStreaming && (
            <span className="ml-0.5 inline-block h-[1em] w-[2px] translate-y-[2px] animate-pulse bg-brand-500" />
          )}
        </div>

        {!msg.isStreaming && cites && cites.length > 0 && (
          <div className="mt-5 border-t border-ink-100 pt-4">
            <p className="mb-2.5 text-[11.5px] font-semibold uppercase tracking-wider text-ink-400">
              근거 문서 {cites.length}건
            </p>
            <div className="flex flex-col gap-1.5">
              {cites.map((cite, index) => {
                const rawName = cite.name || cite.title || "출처";
                const text = cite.text || cite.content;
                const key = `${rawName}-${index}`;
                const isWeb = Boolean(cite.link);
                const { law, clause } = isWeb
                  ? { law: "", clause: rawName }
                  : splitClauseName(rawName);
                const isOpen = visibleKey === key;

                if (isWeb) {
                  return (
                    <a
                      key={key}
                      href={cite.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="group flex items-start gap-2 rounded-lg border border-ink-200 bg-white px-3 py-2 transition-colors hover:border-brand-300 hover:bg-brand-50/40"
                    >
                      <Globe
                        size={14}
                        className="mt-0.5 shrink-0 text-ink-400 group-hover:text-brand-500"
                      />
                      <span className="flex-1 text-[13px] leading-snug text-ink-700 group-hover:text-brand-700">
                        {clause}
                      </span>
                      <span className="shrink-0 rounded bg-ink-100 px-1.5 py-0.5 text-[10.5px] font-semibold text-ink-500">
                        WEB
                      </span>
                    </a>
                  );
                }

                return (
                  <div key={key}>
                    <button
                      type="button"
                      onClick={() => {
                        if (cite.file_name && cite.i_page !== undefined) {
                          onCiteClick(cite.file_name, cite.i_page);
                        }
                        handleTextVisible(key);
                      }}
                      className={`flex w-full items-start gap-2 rounded-lg border px-3 py-2 text-left transition-colors ${
                        isOpen
                          ? "border-brand-300 bg-brand-50/60"
                          : "border-ink-200 bg-white hover:border-brand-300 hover:bg-brand-50/40"
                      }`}
                    >
                      <FileText
                        size={14}
                        className="mt-0.5 shrink-0 text-ink-400"
                      />
                      <span className="flex-1 text-[13px] leading-snug">
                        {law && (
                          <span className="mr-1.5 text-ink-400">{law}</span>
                        )}
                        <span className="font-medium text-ink-800">
                          {clause}
                        </span>
                      </span>
                      {cite.i_page ? (
                        <span className="shrink-0 rounded bg-ink-100 px-1.5 py-0.5 text-[10.5px] font-semibold text-ink-500">
                          p.{cite.i_page}
                        </span>
                      ) : null}
                      <ChevronDown
                        size={14}
                        className={`mt-0.5 shrink-0 text-ink-400 transition-transform ${
                          isOpen ? "rotate-180" : ""
                        }`}
                      />
                    </button>

                    {isOpen && !isLoading && text && (
                      <div className="mt-1.5 max-h-72 overflow-y-auto rounded-lg border border-ink-200 bg-ink-50 px-3.5 py-3 text-[12.5px] leading-relaxed text-ink-600">
                        <p style={{ whiteSpace: "pre-wrap" }}>{text}</p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </>
    );
  };

  return (
    <div className="flex w-full animate-fade-up gap-3">
      <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-ink-900 text-white">
        <Sparkles size={14} />
      </div>
      <div className="min-w-0 flex-1">
        <p className="mb-1.5 text-[12px] font-semibold text-ink-400">
          FinSight
        </p>
        <div
          className={
            answerClass ??
            "rounded-2xl rounded-tl-md border border-ink-200 bg-white px-5 py-4 shadow-card"
          }
        >
          {renderBody()}
        </div>
      </div>
    </div>
  );
}
