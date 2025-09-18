import { useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import type { PDFDocumentProxy } from "pdfjs-dist";

import "react-pdf/dist/esm/Page/AnnotationLayer.css";
import "react-pdf/dist/esm/Page/TextLayer.css";

// PDF.js 워커 경로 설정
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`;

function PdfViewer() {
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const pdfFile = "/sample.pdf"; // public 폴더에 있는 PDF 파일

  function onDocumentLoadSuccess({ numPages }: PDFDocumentProxy) {
    setNumPages(numPages);
  }

  function goToPrevPage() {
    setPageNumber((prevPage) => Math.max(prevPage - 1, 1));
  }

  function goToNextPage() {
    setPageNumber((prevPage) => Math.min(prevPage + 1, numPages || 1));
  }

  return (
    <div>
      <nav>
        <button onClick={goToPrevPage}>Prev</button>
        <p>
          Page {pageNumber} of {numPages}
        </p>
        <button onClick={goToNextPage}>Next</button>
      </nav>

      <div style={{ width: "100%", overflow: "auto" }}>
        <Document file={pdfFile} onLoadSuccess={onDocumentLoadSuccess}>
          <Page pageNumber={pageNumber} />
        </Document>
      </div>
    </div>
  );
}

export default PdfViewer;
