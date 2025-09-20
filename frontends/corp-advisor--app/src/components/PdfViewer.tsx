import { useState, useEffect } from "react";
import { Document, Page, pdfjs } from "react-pdf";

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
  const pdfFile = "/121.pdf"; // public 폴더에 있는 PDF 파일
  useEffect(() => {
    setPageNumber(initialPage);
    setInputValue(String(initialPage));
  }, [initialPage]);
  // input 제어를 위해 별도 상태 (입력값은 string으로)
  const [inputValue, setInputValue] = useState(initialPage.toString());

  function onDocumentLoadSuccess(pdf: any) {
    setNumPages(pdf.numPages);
  }

  const goToPrevPage = () => {
    const newPage = Math.max(pageNumber - 1, 1);
    setPageNumber(newPage);
    setInputValue(String(newPage));
    onPageChange?.(newPage);
  };

  const goToNextPage = () => {
    const newPage = Math.min(pageNumber + 1, numPages || 1);
    setPageNumber(newPage);
    setInputValue(String(newPage));
    onPageChange?.(newPage);
  };
  // input에서 엔터/blur 시 페이지 이동
  const handleInputCommit = () => {
    let page = Number(inputValue);
    if (isNaN(page)) page = pageNumber;
    page = Math.max(1, Math.min(page, numPages || 1)); // 1 ~ numPages 제한
    setPageNumber(page);
    setInputValue(String(page)); // 입력값 정규화
  };
  return (
    <div className="min-h-full bg-gray-100 pb-8">
      {/* X 버튼 */}
      {onClose && (
        <button
          onClick={onClose}
          className="absolute top-2 right-6 text-gray-600 hover:text-gray-900"
        >
          ✕
        </button>
      )}
      <nav className="flex justify-center items-center gap-4 mb-2">
        <button onClick={goToPrevPage} disabled={pageNumber <= 1}>
          ◀
        </button>
        {/* 페이지 번호 input */}
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
          className="px-2 border border-gray-300 text-center rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
        />
        <span>/ {numPages ?? "-"}</span>
        <button
          onClick={goToNextPage}
          disabled={!numPages || pageNumber >= numPages}
        >
          ▶
        </button>
      </nav>

      <div
        style={{
          width: "100%",
          overflow: "auto",
        }}
      >
        <Document file={fileURL} onLoadSuccess={onDocumentLoadSuccess}>
          <Page pageNumber={pageNumber} />
        </Document>
      </div>
    </div>
  );
}
