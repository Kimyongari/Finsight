import { useState, useEffect, useRef } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import { ChevronLeft, ChevronRight, X } from "lucide-react";

import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

// PDF.js 워커 경로 설정
pdfjs.GlobalWorkerOptions.workerSrc = "/pdf.worker.min.mjs";

type PdfViewerProps = {
  initialPage?: number; // 보여주고 싶은 초기 페이지
  fileURL: string | null;
  onPageChange?: (page: number) => void;
  onClose?: () => void; // X 버튼 클릭 시 호출
};

export function PdfViewer({
  initialPage = 1,
  fileURL,
  onPageChange,
  onClose,
}: PdfViewerProps) {
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageNumber, setPageNumber] = useState(initialPage);
  const [inputValue, setInputValue] = useState(initialPage.toString());

  // 패널 너비에 맞춰 페이지를 렌더링해야 잘리지 않는다
  const containerRef = useRef<HTMLDivElement>(null);
  const [pageWidth, setPageWidth] = useState<number>(400);

  useEffect(() => {
    const element = containerRef.current;
    if (!element) return;

    const update = () => setPageWidth(Math.max(240, element.clientWidth - 8));
    update();

    const observer = new ResizeObserver(update);
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    setPageNumber(initialPage);
    setInputValue(initialPage.toString());
  }, [initialPage]);

  function onDocumentLoadSuccess(pdf: any) {
    setNumPages(pdf.numPages);
  }

  const movePage = (nextPage: number) => {
    const page = Math.max(1, Math.min(nextPage, numPages || 1));
    setPageNumber(page);
    setInputValue(String(page));
    onPageChange?.(page);
  };

  // input에서 엔터/blur 시 페이지 이동
  const handleInputCommit = () => {
    const parsed = Number(inputValue);
    movePage(Number.isNaN(parsed) ? pageNumber : parsed);
  };

  return (
    <div className="flex h-full flex-col" ref={containerRef}>
      <div className="sticky top-0 z-10 mb-2 flex items-center justify-between gap-2 rounded-xl border border-ink-200 bg-white/95 px-2 py-1.5 backdrop-blur">
        <span className="pl-1 text-[12px] font-semibold uppercase tracking-wider text-ink-400">
          원문
        </span>

        <div className="flex items-center gap-1">
          <button
            onClick={() => movePage(pageNumber - 1)}
            disabled={pageNumber <= 1}
            aria-label="이전 페이지"
            className="rounded-lg p-1 text-ink-500 transition-colors hover:bg-ink-100 hover:text-ink-800 disabled:pointer-events-none disabled:opacity-30"
          >
            <ChevronLeft size={16} />
          </button>
          <input
            type="number"
            min={1}
            max={numPages || undefined}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onBlur={handleInputCommit}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleInputCommit();
            }}
            className="w-14 rounded-lg border border-ink-200 px-1.5 py-1 text-center text-[13px] focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
          />
          <span className="text-[12.5px] text-ink-400">
            / {numPages ?? "-"}
          </span>
          <button
            onClick={() => movePage(pageNumber + 1)}
            disabled={!numPages || pageNumber >= numPages}
            aria-label="다음 페이지"
            className="rounded-lg p-1 text-ink-500 transition-colors hover:bg-ink-100 hover:text-ink-800 disabled:pointer-events-none disabled:opacity-30"
          >
            <ChevronRight size={16} />
          </button>
        </div>

        {onClose ? (
          <button
            onClick={onClose}
            aria-label="원문 닫기"
            className="rounded-lg p-1 text-ink-400 transition-colors hover:bg-ink-100 hover:text-ink-800"
          >
            <X size={16} />
          </button>
        ) : (
          <span className="w-6" />
        )}
      </div>

      <div className="overflow-auto rounded-xl border border-ink-200 bg-ink-100 p-1">
        <Document
          key={fileURL} // Force re-mount on file change
          file={fileURL}
          onLoadSuccess={onDocumentLoadSuccess}
          loading={
            <div className="py-10 text-center text-[13px] text-ink-400">
              PDF를 불러오는 중…
            </div>
          }
        >
          <Page
            pageNumber={pageNumber}
            width={pageWidth}
            renderAnnotationLayer={false}
            className="overflow-hidden rounded-lg bg-white shadow-sm"
          />
        </Document>
      </div>
    </div>
  );
}
