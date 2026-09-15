import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { UploadCloud } from "lucide-react";
import { UploadFile } from "./UploadFile";

interface FileUploaderProps {
  uploadedFiles: File[];
  setUploadedFiles: (files: File[]) => void;
}

export function FileUploader({
  uploadedFiles,
  setUploadedFiles,
}: FileUploaderProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      setUploadedFiles([...uploadedFiles, ...acceptedFiles]);
    },
    [uploadedFiles, setUploadedFiles]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: true,
    accept: { "application/pdf": [".pdf"] },
  });

  const handleFileDelete = (targetIndex: number) => {
    setUploadedFiles(uploadedFiles.filter((_, index) => index !== targetIndex));
  };

  return (
    <div className="mb-4">
      <div
        {...getRootProps()}
        className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-4 py-8 text-center transition-colors ${
          isDragActive
            ? "border-brand-400 bg-brand-50"
            : "border-ink-200 bg-ink-50 hover:border-brand-300 hover:bg-brand-50/40"
        }`}
      >
        <input {...getInputProps()} />
        <UploadCloud
          size={24}
          className={isDragActive ? "text-brand-500" : "text-ink-400"}
        />
        <p className="text-[13.5px] font-medium text-ink-700">
          {isDragActive
            ? "여기에 파일을 놓으세요"
            : "PDF를 드래그하거나 클릭해서 업로드"}
        </p>
        <p className="text-[12px] text-ink-400">PDF 파일만 지원합니다</p>
      </div>

      {uploadedFiles.length > 0 && (
        <div className="mt-3 flex flex-col gap-1.5">
          {uploadedFiles.map((file, index) => (
            <UploadFile
              key={`${file.name}-${index}`}
              index={index}
              fileName={file.name}
              onDelete={() => handleFileDelete(index)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
