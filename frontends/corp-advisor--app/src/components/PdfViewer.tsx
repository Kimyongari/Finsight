import { useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";

import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

// PDF.js 워커 경로 설정
pdfjs.GlobalWorkerOptions.workerSrc = "/pdf.worker.min.mjs";

type PdfViewerProps = {
  initialPage?: number; // 보여주고 싶은 초기 페이지
  onClose?: () => void; // X 버튼 클릭 시 호출
};

export function PdfViewer({ initialPage = 1, onClose }: PdfViewerProps) {
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageNumber, setPageNumber] = useState(initialPage);
  const pdfFile = "/121.pdf"; // public 폴더에 있는 PDF 파일

  function onDocumentLoadSuccess(pdf: any) {
    setNumPages(pdf.numPages);
  }

  function goToPrevPage() {
    setPageNumber((prevPage) => Math.max(prevPage - 1, 1));
  }

  function goToNextPage() {
    setPageNumber((prevPage) => Math.min(prevPage + 1, numPages || 1));
  }

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
          Prev
        </button>
        <p>
          Page {pageNumber} of {numPages}
        </p>
        <button
          onClick={goToNextPage}
          disabled={!numPages || pageNumber >= numPages}
        >
          Next
        </button>
      </nav>

      <div style={{ width: "100%", overflow: "auto" }}>
        <Document file={pdfFile} onLoadSuccess={onDocumentLoadSuccess}>
          <Page pageNumber={pageNumber} />
        </Document>
      </div>
    </div>
  );
}
