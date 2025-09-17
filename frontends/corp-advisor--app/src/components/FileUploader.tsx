import { useCallback } from "react";
import { useDropzone } from "react-dropzone";

interface FileUploaderProps {
  uploadedFiles: File[];
  setUploadedFiles: (files: File[]) => void;
}

const FileUploader = ({
  uploadedFiles,
  setUploadedFiles,
}: FileUploaderProps) => {
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

  return (
    <div className="flex flex-col border-2 border-dashed p-4 rounded mb-4">
      <div {...getRootProps()} className="flex-1 cursor-pointer mb-2">
        <input {...getInputProps()} />
        {isDragActive
          ? "여기에 파일을 놓으세요…"
          : uploadedFiles.length > 0
          ? `${uploadedFiles.length}개의 파일이 업로드됨`
          : "PDF를 드래그 앤 드롭 또는 클릭해서 업로드"}
      </div>

      {uploadedFiles.map((file, index) => (
        <div key={index} className="flex items-center mb-2">
          <span className="flex-1">{file.name}</span>
          <button
            onClick={() =>
              setUploadedFiles(uploadedFiles.filter((_, i) => i !== index))
            }
            className="ml-2 bg-red-500 text-white px-2 py-1 rounded"
          >
            X
          </button>
        </div>
      ))}
    </div>
  );
};

export default FileUploader;
