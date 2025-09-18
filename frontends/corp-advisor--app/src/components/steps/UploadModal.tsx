import { useState } from "react";
import { FileUploader } from "../FileUploader";
import { Button } from "../Button";
// UploadModal 컴포넌트가 받을 props 타입 정의
type UploadModalProps = {
  onUploadSuccess: (files: File[]) => void;
};

export function UploadModal({ onUploadSuccess }: UploadModalProps) {
  // 파일 업로드
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const handleUpload = async () => {
    if (uploadedFiles.length === 0) {
      alert("업로드할 파일을 선택해주세요.");
      return;
    }

    setIsUploading(true);

    const formData = new FormData();
    uploadedFiles.forEach((file) => {
      formData.append("files", file); // 'files'는 백엔드와 약속된 key
    });
    const fileNames = uploadedFiles.map((file) => file.name).join(", ");
    console.log("업로드할 파일들:", fileNames);
    // API 호출이 성공했다고 가정하고, 1.5초 후 다음 단계로 이동
    setTimeout(() => {
      setIsUploading(false);
      onUploadSuccess(uploadedFiles); // 부모 컴포넌트에 알림
    }, 1500);
  };
  return (
    <>
      <FileUploader
        uploadedFiles={uploadedFiles}
        setUploadedFiles={setUploadedFiles}
      ></FileUploader>
      <Button
        ButtonText={isUploading ? "업로드 중..." : "업로드 완료"}
        onClick={handleUpload}
      ></Button>
    </>
  );
}
